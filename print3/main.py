# -*- coding: utf-8 -*-


import os.path
import traceback
import sys
import urllib
import json
import copy
import datetime
import multiprocessing
import random
from urlparse import urlsplit
from urllib import urlencode


from PyPDF2 import PdfFileMerger


from flask import Flask, abort, Response, request
import requests
from requests.exceptions import Timeout, ConnectionError, SSLError

from print3.utils import (_get_timestamps, delete_old_files,
        _qrcodeurlparse, _qrcodeurlunparse, _shorten, create_pdf_path, create_info_file, create_cancel_file, _increment_info)

from print3.config import MAPFISH_FILE_PREFIX, MAPFISH_MULTI_FILE_PREFIX, USE_MULTIPROCESS, VERIFY_SSL, LOG_SPEC_FILES, REFERER_URL

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
log = logging.getLogger(__name__)


NUMBER_POOL_PROCESSES = multiprocessing.cpu_count()


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


def get_tomcat_backend_info():
    url = 'http:%s/%s' % (TOMCAT_SERVER_URL, 'service-print-main/pdf/info.json')
    r = req_session.get(url,
                        headers={'Referer': REFERER_URL},
                        verify=False)
    return r.content


@app.route('/backend_checker')
def backend_checker():
    try:
        content = get_tomcat_backend_info()
    except (Timeout, SSLError, ConnectionError):
        abort(502, 'Cannot connect to backend tomcat')
    try:
        json.loads(content)
        return 'OK'
    except Exception:
        abort(
            503,
            'Incomprehensible answer. tomcat is probably not ready yet.')


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

    # pdf_download_url = scheme + ':' + PRINT_SERVER_URL + '/print/-multi' + unique_filename + '.pdf.printout'
    pdf_download_url = scheme + ':' + PRINT_SERVER_URL + '/' + MAPFISH_MULTI_FILE_PREFIX + unique_filename + '.pdf.printout'
    with open(infofile, 'w+') as outfile:
        json.dump({'status': 'done', 'getURL': pdf_download_url}, outfile)

    log.info('[create_pdf] PDF ready to download: %s', pdf_download_url)

    return 0


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
