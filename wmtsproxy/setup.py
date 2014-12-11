#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='wmtsproxy',
      version='0.1.2',
      description='WMTSProxy makes WMS/WMTS layers available as WMTS',
      author='Omniscale GmbH & Co. KG',
      author_email='support@omniscale.de',
      packages=find_packages(),
      license='Apache 2',
      install_requires=[
        "PyYAML",
        "requests",
        "mapproxy>=1.7.0",
      ]
)
