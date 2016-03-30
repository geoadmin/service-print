# -*- coding: utf-8 -*-


import os.path
import traceback
import sys
import urllib
import urllib2
import json
import re
import copy
import datetime
import time
import multiprocessing
import random
import uuid
from urlparse import urlparse, parse_qs, urlunparse
from urllib import urlencode, quote_plus, unquote_plus

from httplib2 import Http
from collections import OrderedDict

from PyPDF2 import PdfFileMerger

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError
from pyramid.response import Response

import logging
log = logging.getLogger(__name__)

log.setLevel(logging.INFO)
USE_MULTIPROCESS = True
debuglevel = 0

NUMBER_POOL_PROCESSES = multiprocessing.cpu_count()
MAPFISH_FILE_PREFIX = 'mapfish-print'
MAPFISH_MULTI_FILE_PREFIX = MAPFISH_FILE_PREFIX + '-multi'


currentFuncName = lambda n=0: sys._getframe(n + 1).f_code.co_name


def _zeitreihen(d, api_url):
    '''Returns the timestamps for a given scale and location for ch.swisstopo.zeitreihen
    '''

    timestamps = []

    http = Http(disable_ssl_certificate_validation=True)
    params = urllib.urlencode(d)
    url = 'http:' + api_url + '/rest/services/ech/MapServer/ch.swisstopo.zeitreihen/releases?%s' % params

    try:
        resp, content = http.request(url)
        if int(resp.status) == 200:
            timestamps = json.loads(content)['results']
    except:
        return timestamps

    return timestamps


def _increment_info(l, filename):
    l.acquire()
    try:
        # FIXME infofile
        with open(filename, 'r') as infile:
            data = json.load(infile)

        data['printed'] = data['printed'] + 1

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


def _get_layers(spec):
    try:
        layers = spec['attributes']['map']['layers']
    except KeyError:
        layers = []

    return layers


@view_config(route_name='get_timestamps', renderer='jsonp')
def get_timestamps(self):
    jsonstring = urllib.unquote_plus(self.body)
    spec = json.loads(jsonstring, encoding=self.charset)

    api_url = "//api3.geo.admin.ch"

    return _get_timestamps(spec, api_url)


def _get_timestamps(spec, api_url):
    '''Returns the layers indices to be printed for each timestamp
    For instance (u'19971231', [1, 2]), (u'19981231', [0, 1, 2])  '''

    results = {}
    lyrs = _get_layers(spec)
    log.debug('[_get_timestamps] layers: %s', lyrs)
    for idx, lyr in enumerate(lyrs):
        # For zeitreihen, we always get the timestamps from the service
        if lyr.get('layer') == 'ch.swisstopo.zeitreihen':
            try:
                page = spec['pages'][0]
                display = page['display']
                center = page['center']
                bbox = page['bbox']
                mapExtent = bbox
                mapExtent[3], mapExtent[1] = mapExtent[1], mapExtent[3]
                imageDisplay = _normalize_imageDisplay(display)
                params = {
                    'mapExtent': ','.join(map(str, mapExtent)),
                    'imageDisplay': imageDisplay,
                    'geometry': str(center[0]) + ',' + str(center[1]),
                    'geometryType': 'esriGeometryPoint'
                }
                timestamps = _zeitreihen(params, api_url)

                log.debug('[_get_timestamps] Zeitreichen %s', timestamps)
            except Exception as e:
                log.debug(str(e))
                timestamps = lyr['timestamps'] if 'timestamps' in lyr.keys() else None
        else:
            dimensions = lyr.get('dimensions')
            if dimensions is not None and 'Time' in dimensions:
                params = lyr.get('dimensionParams')
                if params is not None:
                    try:
                        timestamp = params.get('TIME')
                        timestamps = [int(timestamp) if timestamp != 'current' else timestamp]
                    except:
                        timestamps = None

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

    http = Http(disable_ssl_certificate_validation=True)

    shorten_url = api_url + '/shorten.json?url=%s' % quote_plus(url)

    try:
        resp, content = http.request(shorten_url)
        if int(resp.status) == 200:
            shorturl = json.loads(content)['shorturl']
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

    for lyr in tmp_spec['attributes']['map']['layers']:
        try:
            del lyr['timestamps']  # this makes print server crash
            layername = lyr['layer']
            if layername in layers:

                lyr['dimensionParams']['TIME'] = str(timestamp)
        except:
            log.debug('[worker] Cannot fixe tmp_spec')

    log.debug('[worker] Finale partial spec\n----------------\n%s\n---------------\n', json.dumps(tmp_spec, indent=4, sort_keys=True))

    # Before launching print request, check if process is canceled
    if os.path.isfile(cancelfile):
        return (timestamp, None)
    log.debug('[Worker] Requesting partial PDF for: %s', timestamp)
    referer = headers.get('Referer', '')

    opener = urllib2.build_opener(urllib2.HTTPHandler(debuglevel=debuglevel))
    request = urllib2.Request(url, data=json.dumps(tmp_spec))
    request.add_header("Content-Type", 'application/json')
    request.add_header("Referer", referer)
    request.add_header("User-Agent", 'MapFish Print salutes you')

    log.debug('[Worker] headers\n%s', headers)

    try:
        filename = str(uuid.uuid1())
        localname = os.path.join(print_temp_dir, MAPFISH_FILE_PREFIX + filename)

        connection = opener.open(request)
    except urllib2.HTTPError as err:
        if err.code == 404:
            log.error("Page %s not found", url)
        elif err.code == 403:
            log.error("Access to %s denied", url)
        else:
            log.error("Unkonw error while accessing %s: %s", url, err.code)

        return (timestamp, None)

    except urllib2.URLError as err:
        log.debug('[Worker] Failed timestamp: %s', timestamp)
        log.debug('[Worker] Failed timestamp: %s', err.reason)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log.debug("*** Traceback:/n{}".format(traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)))
        log.debug("*** Exception:/n{}".format(traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)))

    if connection.code == 200:
        CHUNK = 1024 * 50
        with open(localname, 'wb') as fp:
            while True:
                chunk = connection.read(CHUNK)
                if not chunk:
                    break
                fp.write(chunk)
        _increment_info(lock, infofile)
        log.info('[Worker] Partial PDF written to: %s', localname)

        return (timestamp, localname)
    else:
        log.error('[Worker] Failed get/generate PDF for: %s. Error: %s', timestamp, connection.code)

        return (timestamp, None)


# Function to be used on process to create all
# pdfs and merge them
def create_and_merge(info):

    lock = multiprocessing.Manager().Lock()
    (spec, print_temp_dir, scheme, api_url, print_proxy_url, print_server_url, headers, unique_filename) = info

    def _isMultiPage(spec):
        isMultiPage = False
        if 'movie' in spec.keys():
            isMultiPage = spec['movie']
        return isMultiPage

    def _merge_pdfs(pdfs, infofile):
        '''Merge individual pdfs into a big one'''
        '''We assume this happens in one process'''
        # FIXME infofile
        with open(infofile, 'r') as data_file:
            info_json = json.load(data_file)

        info_json['merged'] = 0

        def write_info():
            # FIXME infofile
            with open(infofile, 'w+') as outfile:
                json.dump(info_json, outfile)

        log.info('[_merge_pdfs] Starting merge')
        merger = PdfFileMerger()
        expected_file_size = 0
        # Send PDF as is if only one
        if len(pdfs) == 1:
            pdf = pdfs[0]
            ts, localname = pdf
            if localname is not None:
                try:
                    info_json['done'] = True
                    info_json['status'] = 'finished'
                    filename = create_pdf_path(print_temp_dir, unique_filename)
                    log.info('[_merge_pdfs] Only one PDF, copied to: %s', filename)
                    os.rename(localname, filename)
                except:
                    return False
        else:
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
                info_json['done'] = True
                info_json['status'] = 'finished'
                write_info()
                filename = create_pdf_path(print_temp_dir, unique_filename)
                log.info('[_merge_pdfs] Writing file.')
                out = open(filename, 'wb')
                merger.write(out)
                log.info('[_merge_pdfs] Merged PDF written to: %s', filename)
                log.debug(json.dumps(info_json, indent=4))
            except:
                return False

            finally:
                out.close()
                merger.close()

            return True

    jobs = []
    all_timestamps = []

    # FIXME Make it more flexible
    create_pdf_url = 'http:' + print_server_url + '/print/geoadmin3/buildreport.pdf'

    url = create_pdf_url + '?url=' + urllib.quote_plus(create_pdf_url)
    infofile = create_info_file(print_temp_dir, unique_filename)
    cancelfile = create_cancel_file(print_temp_dir, unique_filename)

    pdf_download_path = '/download/-multi' + unique_filename + '.pdf.printout'

    if _isMultiPage(spec):
        all_timestamps = _get_timestamps(spec, api_url)
        log.info('[print_create] Going multipages')
        log.debug('[print_create] Timestamps to process: %s', all_timestamps.keys())

    # FIXME jobs for single or multi should be the same
    if len(all_timestamps) < 1:
        job = (0,   url, headers, None, [], spec, print_temp_dir, infofile, cancelfile, lock)
        jobs.append(job)
    else:
        last_timestamp = all_timestamps.keys()[-1]

        for idx, ts in enumerate(all_timestamps):
            lyrs = all_timestamps[ts]

            tmp_spec = copy.deepcopy(spec)

            # These are indexes
            for lyr in lyrs:
                try:
                    tmp_spec['attributes']['map']['layers'][lyr]['dimensionParams']['TIME'] = str(ts)
                except KeyError:
                    pass

            if ts is not None:
                # FIXME url qrcode
                qrcodeurl = spec['attributes'].get('qrcodeurl', 'https://map.geo.admin.ch/')  # ['qrimage']
                tmp_spec['pages'][0]['timestamp'] = str(ts[0:4])  # FIXME why did we add this char ???? + "\n"

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

            log.debug('[print_create] Processing timestamp: %s', ts)

            job = (idx, url, headers, ts, lyrs, tmp_spec, print_temp_dir, infofile, cancelfile, lock)

            jobs.append(job)
    # FIXME infofile
    with open(infofile, 'w+') as outfile:
        data = {
            "done": False,
            "status": "running",
            "total": len(jobs),
            "printed": 0,
            "elapsedTime":  1,
            "waitingTime": 0,
            "downloadURL": pdf_download_path
        }

        json.dump(data, outfile)

    if USE_MULTIPROCESS:
        pool = multiprocessing.Pool(NUMBER_POOL_PROCESSES)
        log.info('[{}] Using multiprocess for {} jobs'.format(currentFuncName(), len(jobs)))
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
            log.debug("*** Traceback:/n{}".format(traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)))
            log.debug("*** Exception:/n{}".format(traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)))
            return 1
    else:
        pdfs = []
        log.info('[{}] Using single process for {} jobs'.format(currentFuncName(), len(jobs)))
        for j in jobs:
            pdfs.append(worker(j))
            _increment_info(lock, infofile)

    # Check if canceled, then we don't merge pdf's
    # We don't/can't cancel the merge process itself
    if os.path.isfile(cancelfile):
        return 0

    log.debug('[create_and_merge] Pdfs to merge %s', pdfs)
    if len([i for i, v in enumerate(pdfs) if v[1] is None]) > 0:
        log.error('One or more partial PDF is missing. Cannot merge PDF')
        return 2

    if _merge_pdfs(pdfs, infofile) is False:
        log.error('Something went wrong while merging PDFs')
        return 3

    # FIXME infofile
    with open(infofile, 'w+') as outfile:
        try:
            data = json.load(outfile)
        except ValueError:
            data = {}
        data['done'] = True
        data['status'] = 'finished'
        data['downloadURL'] = pdf_download_path

        json.dump(data, outfile)

    log.info('[create_pdf] PDF ready to download: %s', pdf_download_path)

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


class PrintMulti(object):

    ''' Print proxy to the MapFish Print Server to deal with time series

    If at least a layer has an attribute 'timestamps' holding an array
    of timestamps to print, one page per timestamp will be generated and
    merged.'''

    def __init__(self, request):
        self.request = request
        self.server_id  = request.registry.settings['server_id']

    @view_config(route_name='print_cancel', renderer='jsonp')
    def print_cancel(self):
        if self.request.method == 'OPTIONS':
            return Response(status=200)
        print_temp_dir = self.request.registry.settings['print_temp_dir']
        fileid = self.request.matchdict["id"]
        cancelfile = create_cancel_file(print_temp_dir, fileid)
        with open(cancelfile, 'a+'):
            pass

        if not os.path.isfile(cancelfile):
            raise HTTPInternalServerError('Could not create cancel file with given id')

        log.info("[print_cancel] Job with id=%s cancelled", fileid)

        return Response(status=200)

    @view_config(route_name='print_progress', renderer='jsonp')
    def print_progress(self):
        print_temp_dir = self.request.registry.settings['print_temp_dir']
        fileid = self.request.matchdict["id"]
        filename = create_info_file(print_temp_dir, fileid)
        pdffile = create_pdf_path(print_temp_dir, fileid)

        if not os.path.isfile(filename):
            raise HTTPBadRequest('No print job with id {}'.format(fileid))

        with open(filename, 'r') as data_file:
            try:
                data = json.load(data_file)
            except ValueError:
                data = {'done': False, 'status': 'error'}

        # When file is written, get current size
        if os.path.isfile(pdffile):
            data['elapsedTime'] = os.path.getsize(pdffile)
        log.info("[print_progress] Progress for job id=%s, 'done'=%s", fileid, data['done'])

        return data

    @view_config(route_name='print_create', renderer='jsonp')
    def print_create(self):
        if self.request.method == 'OPTIONS':
            return Response(status=200)

        log.info("[print_create] New print job")
        # delete all child processes that have already terminated
        # but are <defunct>. This is a side_effect of the below function
        multiprocessing.active_children()

        # IE is always URLEncoding the body
        jsonstring = urllib.unquote_plus(self.request.body)

        try:
            spec = json.loads(jsonstring, encoding=self.request.charset)
        except:
            log.error('[print_create] JSON content could not be parsed')
            exc_type, exc_value, exc_traceback = sys.exc_info()
            log.debug("*** Traceback:/n{}".format(traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)))
            log.debug("*** Exception:/n{}".format(traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)))
            raise HTTPBadRequest('JSON is empty or content could not be parsed')

        print_temp_dir = self.request.registry.settings['print_temp_dir']

        # Remove older files on the system
        delete_old_files(print_temp_dir)

        scheme = self.request.headers.get('X-Forwarded-Proto',
                                          self.request.scheme)
        print_proxy_url = self.request.registry.settings['print_proxy_url']
        print_server_url = self.request.registry.settings['print_server_url']
        api_url = self.request.registry.settings['api_url']
        headers = dict(self.request.headers)
        headers.pop("Host", headers)

        unique_filename = datetime.datetime.now().strftime("%y%m%d%H%M%S") + str(random.randint(1000, 9999))
        pdf_download_path = '/download/-multi' + unique_filename + '.pdf.printout'

        with open(create_info_file(print_temp_dir, unique_filename), 'w+') as outfile:
            data = {
                "done": False,
                "status": "running",
                "elapsedTime": 1,
                "waitingTime": 0,
                "downloadURL": pdf_download_path
            }
            json.dump(data, outfile)

        info = (spec, print_temp_dir, scheme, api_url, print_proxy_url, print_server_url, headers, unique_filename)

        p = multiprocessing.Process(target=create_and_merge, args=(info,))
        p.start()

        response = {"ref": unique_filename,
                    "statusURL": "/print/print/geoadmin3/status/{}.json".format(unique_filename),
                    "downloadURL": pdf_download_path}

        return response
