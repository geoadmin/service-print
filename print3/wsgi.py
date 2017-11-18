# -*- coding: utf-8 -

import os
import multiprocessing
from gunicorn.app.base import BaseApplication
from gunicorn.six import iteritems
from print3.main import app as application


def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1


class StandaloneApplication(BaseApplication):

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


if __name__ == '__main__':
    WSGI_PORT = str(os.environ.get('WSGI_PORT'))
    options = {
        'bind': '%s:%s' % ('0.0.0.0', WSGI_PORT),
        'worker_class': 'gevent',
        'workers': number_of_workers(),
    }
    StandaloneApplication(application, options).run()
