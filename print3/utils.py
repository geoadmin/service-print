import os
import time
import re
import urllib
import requests
from collections import OrderedDict
from urlparse import urlparse, parse_qs, urlunparse
from urllib import urlencode, quote_plus, unquote_plus
import json

from print3.config import MAPFISH_MULTI_FILE_PREFIX, VERIFY_SSL, USE_LV95_SERVICES


import logging
log = logging.getLogger(__name__)


def create_pdf_path(print_temp_dir, unique_filename):
    return os.path.join(print_temp_dir, MAPFISH_MULTI_FILE_PREFIX + unique_filename + '.pdf.printout')


def create_info_file(print_temp_dir, unique_filename):
    return os.path.join(print_temp_dir, MAPFISH_MULTI_FILE_PREFIX + unique_filename + '.json')


def create_cancel_file(print_temp_dir, unique_filename):
    return os.path.join(print_temp_dir, MAPFISH_MULTI_FILE_PREFIX + unique_filename + '.cancel')


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
            xx = map(lambda x: x + 2e6, eastings)
            yy = map(lambda x: x + 1e6, northings)
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
