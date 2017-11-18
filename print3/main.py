# -*- coding: utf-8 -*-


import os.path
import traceback
import sys
import urllib
import json
import re
import copy
import datetime
import time
import multiprocessing
import random
from urlparse import urlparse, parse_qs, urlsplit, urlunparse
from urllib import urlencode, quote_plus, unquote_plus

from collections import OrderedDict

from PyPDF2 import PdfFileMerger


from flask import Flask, abort, Response, request
import requests


import logging
# log = logging.getLogger(__name__)
# log.setLevel(logging.INFO)

WMS_SOURCE_URL = 'http://localhost:%s' % os.environ.get('WMS_PORT')
LOGLEVEL = int(os.environ.get('PRINT_LOGLEVEL', logging.DEBUG))
PRINT_TEMP_DIR = os.environ.get('PRINT_TEMP_DIR', '/var/local/print')
API_URL = os.environ.get('API_URL', 'https://api3.geo.admin.ch')
TOMCAT_SERVER_URL = os.environ.get('TOMCAT_SERVER_URL', 'https://print.geo.admin.ch')
PRINT_SERVER_URL = os.environ.get('PRINT_SERVER_URL', 'https://print.geo.admin.ch')

logging.basicConfig(level=LOGLEVEL, stream=sys.stderr)
log = logging.getLogger('print')


NUMBER_POOL_PROCESSES = multiprocessing.cpu_count()
MAPFISH_FILE_PREFIX = 'mapfish-print'
MAPFISH_MULTI_FILE_PREFIX = MAPFISH_FILE_PREFIX + '-multi'
USE_MULTIPROCESS = True
USE_LV95_SERVICES = False
VERIFY_SSL = False
LOG_SPEC_FILES = False


app = Flask(__name__)
req_session = requests.Session()
req_session.mount('http://', requests.adapters.HTTPAdapter(max_retries=0))
req_session.mount('https://', requests.adapters.HTTPAdapter(max_retries=0))


@app.route('/checker')
def checker():
    return 'OK'

''' Print proxy to the MapFish Print Server to deal with time series
    If at least a layer has an attribute 'timestamps' holding an array
    of timestamps to print, one page per timestamp will be generated and
    merged.'''


@app.route('/printcancel')
def print_cancel():

    fileid = request.args.get('id')
    cancelfile = create_cancel_file(PRINT_TEMP_DIR, fileid)
    with open(cancelfile, 'a+'):
        pass

    if not os.path.isfile(cancelfile):
        abort(500, 'Could not create cancel file with id' % fileid)

    return Response(status=200)


@app.route('/printprogress')
def print_progress():

    fileid = request.args.get('id')
    filename = create_info_file(PRINT_TEMP_DIR, fileid)
    pdffile = create_pdf_path(PRINT_TEMP_DIR, fileid)

    if not os.path.isfile(filename):
        abort(400, '%s does not exists' % filename)
    
    with open(filename, 'r') as data_file:
        data = json.load(data_file)

    # When file is written, get current size
    if os.path.isfile(pdffile):
        data['written'] = os.path.getsize(pdffile)

    return Response(json.dumps(data), mimetype='application/json')


@app.route('/printmulti/create.json', methods=['OPTIONS'])
def print_create_option():
    return Response('OK', status=200, mimetype='text/plain')


@app.route('/printmulti/create.json', methods=['GET', 'POST'])
def print_create_post():
    # jsonstring = urllib.unquote_plus(request.content)
    # spec = json.loads(jsonstring, encoding=self.request.charset)

    # delete all child processes that have already terminated
    # but are <defunct>. This is a side_effect of the below function
    multiprocessing.active_children()

    app.logger.info('info')
    try:
        spec = request.get_json()

    except:
        logging.debug('JSON content could not be parsed')
        exc_type, exc_value, exc_traceback = sys.exc_info()
        app.logger.debug("*** Traceback:/%s" % traceback.print_tb(exc_traceback, limit=1, file=sys.stdout))
        app.logger.debug("*** Exception:/n%s" % traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout))
        abort(400, 'JSON content could not be parsed')

    if spec is None:
        data = request.stream.read()
        try:
            spec = json.loads(data)
        except ValueError:
            app.logger.debug(data)
            abort(400, 'JSON content could not be parsed: {}'.format(data))

    if LOG_SPEC_FILES:
        app.logger.debug(json.dumps(spec, indent=2))

    # Remove older files on the system
    delete_old_files(PRINT_TEMP_DIR)

    scheme = request.headers.get('X-Forwarded-Proto',
                                 request.scheme)
    headers = dict(request.headers)
    headers.pop("Host", headers)
    unique_filename = datetime.datetime.now().strftime("%y%m%d%H%M%S") + str(random.randint(1000, 9999))

    with open(create_info_file(PRINT_TEMP_DIR, unique_filename), 'w+') as outfile:
        json.dump({'status': 'ongoing'}, outfile)

    info = (spec, PRINT_TEMP_DIR, scheme, API_URL, TOMCAT_SERVER_URL, headers, unique_filename)
    p = multiprocessing.Process(target=create_and_merge, args=(info,))
    p.start()
    
    response = {'idToCheck': unique_filename}

    return Response(json.dumps(response), mimetype='application/json')


def _normalize_projection(coords, use_lv95=USE_LV95_SERVICES):
    '''Converts point and bbox to LV95, if needed, i.e. if source coords is
       LV03 and backend service supports LV95
    '''
    eastings = coords[::2]
    northings = coords[1::2]
    is_lv95 = (coords[0] > 2e6 and coords[1] > 1e6)
    if use_lv95:
        if is_lv95:
            return coords
        else:
            xx = map(lambda x: x - 2e6, eastings)
            yy = map(lambda x: x - 1e6, northings)
    else:
        if is_lv95:
            xx = map(lambda x: x - 2e6, eastings)
            yy = map(lambda x: x - 1e6, northings)
        else:
            return coords
    lst = zip(xx, yy)
    reproj_coords = [e for l in lst for e in l]

    return reproj_coords


def _zeitreihen(d, api_url):
    '''Returns the timestamps for a given scale and location for ch.swisstopo.zeitreihen
    '''
    # api_url='//mf-chsdi3.dev.bgdi.ch'
    app.logger.debug(d)
    app.logger.debug(api_url)
    timestamps = []

    sr = 2056 if USE_LV95_SERVICES else 21781
    d['sr'] = sr
    params = urllib.urlencode(d)
    url = 'http:' + api_url + '/rest/services/ech/MapServer/ch.swisstopo.zeitreihen/releases?%s' % params

    try:
        r = requests.get(url)
        if r.status_code == requests.codes.ok:
            data = r.json()
            timestamps = data['results']
    except:

        return timestamps

    return timestamps


def _increment_info(l, filename):
    l.acquire()
    try:
        with open(filename, 'r') as infile:
            data = json.load(infile)

        data['done'] = data['done'] + 1

        with open(filename, 'w+') as outfile:
            json.dump(data, outfile)
    except:
        pass

    finally:
        l.release()


def _normalize_imageDisplay(display):
    # Given print size is for 72 dpi: https://github.com/geoadmin/mf-geoadmin3/blob/master/src/components/print/PrintDirective.js#L27
    sourceDPI = 72.0
    # Target print dpi is 254
    targetDPI = 256.0
    ratio = targetDPI / sourceDPI
    return str(int(display[0] * ratio)) + ',' + \
        str(int(display[1] * ratio)) + ',' + \
        str(targetDPI)


def _get_timestamps(spec, api_url):
    '''Returns the layers indices to be printed for each timestamp
    For instance (u'19971231', [1, 2]), (u'19981231', [0, 1, 2])  '''

    results = {}
    lyrs = spec.get('layers', [])
    log.debug('[_get_timestamps] layers: %s', lyrs)
    for idx, lyr in enumerate(lyrs):
        # For zeitreihen, we always get the timestamps from the service
        if lyr.get('layer') == 'ch.swisstopo.zeitreihen':
            try:
                page = spec['pages'][0]
                display = page['display']
                center = _normalize_projection(page['center'])
                bbox = _normalize_projection(page['bbox'])
                mapExtent = bbox
                imageDisplay = _normalize_imageDisplay(display)
                params = {
                    'mapExtent': ','.join(map(str, mapExtent)),
                    'imageDisplay': imageDisplay,
                    'geometry': str(center[0]) + ',' + str(center[1]),
                    'geometryType': 'esriGeometryPoint'
                }
                timestamps = _zeitreihen(params, api_url)
                log.debug('[_get_timestamps] Zeitreihen %s', timestamps)
            except Exception as e:
                log.debug(str(e))
                timestamps = lyr['timestamps'] if 'timestamps' in lyr.keys() else None
        else:
            timestamps = lyr['timestamps'] if 'timestamps' in lyr.keys() else None

        if timestamps is not None:
            for ts in timestamps:
                if len(timestamps) > 1 and ts.startswith('9999'):
                    continue
                if ts in results.keys():
                    results[ts].append(idx)
                else:
                    results[ts] = [idx]

    return OrderedDict(sorted(results.items(), key=lambda t: t[0]))


def _qrcodeurlparse(raw_url):
    ''' Parse an qrcodegenerator ready link '''

    pattern = re.compile(ur'(https?:\/\/.*)\?url=(.*)')

    m = re.search(pattern, raw_url)

    try:
        (qrcode_service_url, qs) = m.groups()

        rawurl_to_shorten = unquote_plus(qs)
        scheme, netloc, path, params, query, fragment = urlparse(rawurl_to_shorten)
        map_url = urlunparse((scheme, netloc, path, None, None, None))
        parsed_params = parse_qs(query)
        params = dict([(key, ','.join(parsed_params[key])) for key in parsed_params.keys() if isinstance(parsed_params[key], list)])
        log.debug('map params=%s', params)

        return (qrcode_service_url, map_url, params)
    except:
        return False


def _qrcodeurlunparse(url_tuple):
    (qrcode_service_url, map_url, params) = url_tuple

    try:
        str_params = dict(map(lambda x: (x[0], unicode(x[1]).encode('utf-8')), params.items()))
    except UnicodeDecodeError:
        str_params = params
    quoted_map_url = quote_plus(map_url + "?url=" + unquote_plus(urlencode(str_params)))

    return qrcode_service_url + "?url=" + quoted_map_url


def _shorten(url, api_url='http://api3.geo.admin.ch'):
    ''' Shorten a possibly long url '''

    shorten_url = api_url + '/shorten.json?url=%s' % quote_plus(url)

    try:
        r = requests.get(shorten_url, verify=VERIFY_SSL)
        if r.status_code == requests.codes.ok:
            shorturl = r.json()['shorturl']
            return shorturl
    except:
        return url


def create_pdf_path(print_temp_dir, unique_filename):
    return os.path.join(print_temp_dir, MAPFISH_MULTI_FILE_PREFIX + unique_filename + '.pdf.printout')


def create_info_file(print_temp_dir, unique_filename):
    return os.path.join(print_temp_dir, MAPFISH_MULTI_FILE_PREFIX + unique_filename + '.json')


def create_cancel_file(print_temp_dir, unique_filename):
    return os.path.join(print_temp_dir, MAPFISH_MULTI_FILE_PREFIX + unique_filename + '.cancel')


def worker(job):
    ''' Print and dowload the indivialized PDFs'''

    timestamp = None
    (idx, url, headers, timestamp, layers, tmp_spec, print_temp_dir, infofile, cancelfile, lock) = job

    app.logger.debug(json.dumps(tmp_spec, indent=2))

    for layer in layers:
        try:
            tmp_spec['layers'][layer]['params']['TIME'] = str(timestamp)
        except:
            continue

    # Before launching print request, check if process is canceled
    if os.path.isfile(cancelfile):
        return (timestamp, None)

    h = {'Referer': headers.get('Referer'), 'Content-Type': 'application/json'}
    r = requests.post(url,  data=json.dumps(tmp_spec), headers=h,  verify=VERIFY_SSL)

    if r.status_code == requests.codes.ok:

        # GetURL '141028163227.pdf.printout', file 'mapfish-print141028163227.pdf.printout'
        # We only get the pdf name and rely on the fact that they are stored on Zadara
        try:
            pdf_url = r.json()['getURL']
            app.logger.debug('[Worker] pdf_url: %s', pdf_url)
            filename = os.path.basename(urlsplit(pdf_url).path)
            localname = os.path.join(print_temp_dir, MAPFISH_FILE_PREFIX + filename)
        except:
            app.logger.debug('[Worker] Failed timestamp: %s', timestamp)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            app.logger.debug("*** Traceback:/n %s" % traceback.print_tb(exc_traceback, limit=1, file=sys.stdout))
            app.logger.debug("*** Exception:/n %s" % traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout))

            return (timestamp, None)
        _increment_info(lock, infofile)
        return (timestamp, localname)
    else:
        app.logger.debug('[Worker] Failed get/generate PDF for: %s. Error: %s', timestamp, r.status_code)
        app.logger.debug('[Worker] response: %s', r.text)
        app.logger.debug('[Worker] spec: %s', tmp_spec)
        app.logger.debug('[Worker] headers: %s', h)
        app.logger.debug('[Worker] url: %s', url)
        app.logger.debug('[Worker] print dir: %s', print_temp_dir)

        return (timestamp, None)


# Function to be used on process to create all
# pdfs and merge them
def create_and_merge(info):

    lock = multiprocessing.Manager().Lock()
    (spec, print_temp_dir, scheme, api_url, print_url, headers, unique_filename) = info

    def _isMultiPage(spec):
        isMultiPage = False
        if 'movie' in spec.keys():
            isMultiPage = spec['movie']
        return isMultiPage

    def _merge_pdfs(pdfs, infofile):
        '''Merge individual pdfs into a big one'''
        '''We assume this happens in one process'''

        with open(infofile, 'r') as data_file:
            info_json = json.load(data_file)

        info_json['merged'] = 0

        def write_info():
            with open(infofile, 'w+') as outfile:
                json.dump(info_json, outfile)

        log.info('[_merge_pdfs] Starting merge')
        merger = PdfFileMerger()
        expected_file_size = 0
        for pdf in sorted(pdfs, key=lambda x: x[0]):

            ts, localname = pdf
            if localname is not None:
                try:
                    path = open(localname, 'rb')
                    expected_file_size += os.path.getsize(localname)
                    merger.append(fileobj=path)
                    info_json['merged'] += 1
                    write_info()
                except:
                    return None

        try:
            info_json['filesize'] = expected_file_size
            info_json['written'] = 0
            write_info()
            filename = create_pdf_path(print_temp_dir, unique_filename)
            log.info('[_merge_pdfs] Writing file.')
            out = open(filename, 'wb')
            merger.write(out)
            log.info('[_merge_pdfs] Merged PDF written to: %s', filename)
        except:
            return False

        finally:
            out.close()
            merger.close()

        return True

    jobs = []
    all_timestamps = []

    create_pdf_url = scheme + ':' + print_url + '/print/create.json'

    url = create_pdf_url + '?url=' + urllib.quote_plus(create_pdf_url)
    infofile = create_info_file(print_temp_dir, unique_filename)
    cancelfile = create_cancel_file(print_temp_dir, unique_filename)

    if _isMultiPage(spec):
        all_timestamps = _get_timestamps(spec, api_url)

        app.logger.info('[print_create_post] Going multipages')
        if len(all_timestamps) < 1:
            return 4

        app.logger.debug('[print_create_post] Timestamps to process: %s', all_timestamps.keys())

    for i, lyr in enumerate(spec['layers']):
        cleanup_baseurl = spec['layers'][i]['baseURL'].replace('{', '%7B').replace('}', '%7D')
        spec['layers'][i]['baseURL'] = cleanup_baseurl

    if len(all_timestamps) < 1:
        job = (0, url, headers, None, [], spec, print_temp_dir)
        jobs.append(job)
    else:
        last_timestamp = all_timestamps.keys()[-1]

        for idx, ts in enumerate(all_timestamps):
            lyrs = all_timestamps[ts]

            tmp_spec = copy.deepcopy(spec)
            for lyr in lyrs:
                try:
                    tmp_spec['layers'][lyr]['params']['TIME'] = str(ts)
                except KeyError:
                    pass

            if ts is not None:
                qrcodeurl = spec['qrcodeurl']
                tmp_spec['pages'][0]['timestamp'] = str(ts[0:4]) + "\n"

                ''' Adapteds the qrcode url and shortlink to match the timestamp
                    on every page of the PDF document'''

                parsed_qrcode_url = _qrcodeurlparse(qrcodeurl)
                if parsed_qrcode_url:
                    (qrcode_service_url, map_url, map_params) = parsed_qrcode_url
                    if 'time' in map_params:
                        map_params['time'] = ts[0:4]
                    if 'layers_timestamp' in map_params:
                        map_params['layers_timestamp'] = ts

                    time_updated_qrcodeurl = _qrcodeurlunparse((qrcode_service_url, map_url, map_params))
                    shortlink = _shorten(map_url + "?" + urlencode(map_params))

                    tmp_spec['qrcodeurl'] = time_updated_qrcodeurl
                    tmp_spec['pages'][0]['shortLink'] = shortlink
                    log.debug('[print_create] QRcodeURL: %s', time_updated_qrcodeurl)
                    log.debug('[print_create] shortLink: %s', shortlink)

            if 'legends' in tmp_spec.keys() and ts != last_timestamp:
                del tmp_spec['legends']
                tmp_spec['enableLegends'] = False

            app.logger.debug('[print_create] Processing timestamp: %s', ts)

            job = (idx, url, headers, ts, lyrs, tmp_spec, print_temp_dir, infofile, cancelfile, lock)

            jobs.append(job)

    with open(infofile, 'w+') as outfile:
        json.dump({'status': 'ongoing', 'done': 0, 'total': len(jobs)}, outfile)

    if USE_MULTIPROCESS:
        app.logger.info("Going multiprocess")
        pool = multiprocessing.Pool(NUMBER_POOL_PROCESSES)
        pdfs = pool.map(worker, jobs)
        pool.close()
        try:
            pool.join()
            pool.terminate()
        except Exception as e:
            for i in reversed(range(len(pool._pool))):
                p = pool._pool[i]
                if p.exitcode is None:
                    p.terminate()
                del pool._pool[i]
            log.error('Error while generating the partial PDF: %s', e)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            log.debug("*** Traceback:/n %s" % traceback.print_tb(exc_traceback, limit=1, file=sys.stdout))
            log.debug("*** Exception:/n %s" % traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout))
            return 1
    else:
        app.logger.info("Going single process")
        pdfs = []
        for j in jobs:
            pdfs.append(worker(j))
            _increment_info(lock, infofile)

    # Check if canceled, then we don't merge pdf's
    # We don't/can't cancel the merge process itself
    if os.path.isfile(cancelfile):
        return 0

    log.debug('pdfs %s', pdfs)
    if len([i for i, v in enumerate(pdfs) if v[1] is None]) > 0:
        log.error('One or more partial PDF is missing. Cannot merge PDF')
        return 2

    if _merge_pdfs(pdfs, infofile) is False:
        log.error('Something went wrong while merging PDFs')
        return 3

    pdf_download_url = scheme + ':' + PRINT_SERVER_URL + '/print/-multi' + unique_filename + '.pdf.printout'
    with open(infofile, 'w+') as outfile:
        json.dump({'status': 'done', 'getURL': pdf_download_url}, outfile)

    log.info('[create_pdf] PDF ready to download: %s', pdf_download_url)

    return 0


def delete_old_files(path):
    now = time.time()
    # older than 1 hour
    cutoff = now - 3600
    files = os.listdir(path)
    for xfile in files:
        if MAPFISH_MULTI_FILE_PREFIX not in xfile:
            continue
        fn = path + '/' + xfile
        if os.path.isfile(fn):
            t = os.stat(fn)
            c = t.st_ctime
            if c < cutoff:
                os.remove(fn)

if __name__ == '__main__':
    custom_log_format = """-------------------------------------------------------------------------
        %(module)s [%(pathname)s:%(lineno)d]: %(message)s
    -------------------------------------------------------------------------"""
    app.config['DEBUG'] = os.environ.get('DEBUG', False)
    port = int(os.environ.get('WSGI_PORT'))
    app.debug_log_format = custom_log_format

    fileHandler = logging.FileHandler("wsgi.log")
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] [%(pathname)s:%(lineno)d] %(message)s")
    logFormatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
    fileHandler.setFormatter(logFormatter)

    app.logger.addHandler(fileHandler)
    app.run(host='0.0.0.0', port=port)
