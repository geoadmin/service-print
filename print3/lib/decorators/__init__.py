# -*- coding: utf-8 -*-

from functools import wraps
from urllib import unquote_plus
import json
import geojson


import pyramid.httpexceptions as exc


def requires_authorization():
    def wrapper(f):
        @wraps(f)
        def wrapped(self, *args, **kwargs):
            if hasattr(self, 'request'):
                request = self.request
            else:
                request = self
            if request.headers.get('X-SearchServer-Authorized', '').lower() != 'true':
                raise exc.HTTPForbidden(detail='This service requires an authorization')
            else:
                return f(self, *args, **kwargs)
        return wrapped
    return wrapper


def _validate_spec(spec):
    layers = spec.get('layers', [])

    for lyr in layers:
        lyr_type = lyr.get('type')

        if lyr_type == 'Vector':
            geoJson = lyr.get('geoJson')
            if geoJson.get('type') == 'FeatureCollection':
                features = geoJson.get('features', [])
                for feature in features:
                   try:
                       jsonstring = json.dumps(feature)
                       obj = geojson.loads(jsonstring)
                   except ValueError:
                       raise exc.HTTPBadRequest('Spec file validation issue: vector feature cannot be parsed')
                   
                   if 'geometry' not in obj:
                       raise exc.HTTPBadRequest('Spec file validation issue: vector feature has no geometry')
                   geom = obj['geometry']

                   is_valid = geojson.is_valid(geom)

                   if 'valid' in is_valid.keys() and is_valid['valid'] == 'no':
                        raise exc.HTTPBadRequest('Spec file validation issue: A Vector layer has feature(s) with invalid geometry')


def validates_spec():
    def wrapper(f):
        @wraps(f)
        def wrapped(self, *args, **kwargs):
            if hasattr(self, 'request'):
                request = self.request
            else:
                request = self

            # IE is always URLEncoding the body
            jsonstring = unquote_plus(request.body)

            spec = json.loads(jsonstring, encoding=request.charset)
            try:
                spec = json.loads(jsonstring, encoding=request.charset)
            except:
                raise exc.HTTPBadRequest('JSON content could not be parsed')

            _validate_spec(spec)

            return f(self, *args, **kwargs)

        return wrapped
    return wrapper
