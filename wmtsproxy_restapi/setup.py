#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='wmtsproxy_restapi',
      version='0.1',
      description='REST configuration server for wmtsproxy',
      author='Omniscale GmbH & Co. KG',
      author_email='support@omniscale.de',
      packages=find_packages(),
      license='Apache 2',
      install_requires=[
        "Flask",
      ]
)
