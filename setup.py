#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import io
from setuptools import setup, find_packages

setup(name='django-expenses',
      version='0.4.2',
      description='A comprehensive system for managing expenses',
      keywords='django,expenses',
      author='Chris Warrick',
      author_email='chris@chriswarrick.com',
      url='https://github.com/Kwpolska/django-expenses',
      license='3-clause BSD',
      long_description=io.open('./README.rst', 'r', encoding='utf-8').read(),
      platforms='any',
      zip_safe=False,
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 3',
                   'Framework :: Django',
                   'License :: OSI Approved :: BSD License',
                   'Topic :: Office/Business :: Financial'
                   ],
      packages=find_packages(),
      install_requires=[
          'Django>=2.1', 'Babel', 'pygal',
          'django-oauth-toolkit', 'iso8601'
      ],
      )
