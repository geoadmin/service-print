import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = open(os.path.join(here, 'requirements.txt')).read().split('\n')


setup(name='print3',
      version='0.0.1',
      description='Print service for geo.admin.ch',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[],
      keywords='',
      author='',
      author_email='',
      license='MIT',
      url='https://github.com/geoadmin/service-print',
      packages=find_packages(exclude=['tests']),
      package_dir={'print3': 'print3'},
      include_package_data=True,
      zip_safe=False,
      test_suite='nose.collector',
      )
