#!/usr/bin/env python
# -*- coding: latin-1 -*-
#                                   __
#                                  /\ \
#     __      __       __    ____  \_\ \
#   /'_ `\  /'__`\   /'__`\ /',__\ /'_` \
#  /\ \L\ \/\ \L\.\_/\  __//\__, `/\ \L\ \
#  \ \____ \ \__/.\_\ \____\/\____\ \___,_\
#   \/___L\ \/__/\/_/\/____/\/___/ \/__,_ /
#     /\____/
#     \_/__/

import os
import sys
from distutils.core import setup

here = os.path.abspath(os.path.dirname(__file__))

# 'setup.py publish' shortcut.
if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist bdist_wheel')
    os.system('twine upload dist/*')
    sys.exit()

requires = [
    'six',
    'pip',
    'google_api_python_client',
    'enum34',
    'decorator',
]

about = {}
with open(os.path.join(here, 'gaesd', '__version__.py')) as f:
    exec (f.read(), about)

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    packages=['gaesd', 'gaesd/core', 'gaesd/core/dispatchers'],
    license=about['__license__'],
    requires=requires,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language:: Python:: 2.6',
        'Programming Language:: Python:: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)
