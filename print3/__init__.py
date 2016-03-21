# -*- coding: utf-8 -*-

from pyramid.config import Configurator
from pyramid.events import BeforeRender, NewRequest
from pyramid.renderers import JSONP





def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    app_version = settings.get('app_version')
    settings['app_version'] = app_version
    config = Configurator(settings=settings)


    # renderers
    #config.add_mako_renderer('.js')
    config.add_renderer('jsonp', JSONP(param_name='callback', indent=None, separators=(',', ':')))


    # route definitions
    config.add_route('ogcproxy', '/ogcproxy')
    config.add_route('print_create', '/printmulti/create.json')
    config.add_route('print_progress', '/printprogress')
    config.add_route('print_cancel', '/printcancel')
    config.add_route('dev', '/dev')
    config.add_route('checker', '/checker')
    config.add_route('checker_dev', '/checker_dev')


    # required to find code decorated by view_config
    config.scan(ignore=['print3.tests', 'print3.models.bod'])
    return config.make_wsgi_app()
