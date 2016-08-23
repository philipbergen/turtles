#!/usr/bin/env python

import os
import re
import sys
from codecs import open

from setuptools import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py register')
    os.system('python setup.py sdist upload')
    # os.system('python setup.py bdist_wheel upload --universal')
    sys.exit()

requires = open('requirements.txt').read().splitlines()
version = '0.0.1'

def read(f):
    return open(f, encoding='utf-8').read()

setup(
    name='turtles',
    version=version,
    description='The turtles CI framework',
    long_description=read('README.rst'),
    author='Philip Bergen',
    author_email='philip.bergen@me.com',
    url='https://github.com/philipbergen/turtles',
    packages=['turtles'],
    package_data={'': ['LICENSE'], 'turtles': []},
    include_package_data=True,
    entry_points = {
        'console_scripts': ['trtl=turtles.trtl:cli'],
    },
    install_requires=requires,
    license='MIT',
    zip_safe=False,
    classifiers=(
        # 'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    )
)
