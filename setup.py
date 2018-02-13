import os

from setuptools import setup, find_packages

setup(name='print3',
      version='0.0.1',
      description='Print service for geo.admin.ch',
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
