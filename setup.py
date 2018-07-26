#!/usr/bin/env python
from setuptools import setup

setup(
    setup_requires=['pbr>=4.2.0'],
    package_dir={'':'src/'}, # Needed for distutils
    pbr=True
)
