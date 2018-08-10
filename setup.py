#!/usr/bin/env python
from setuptools import setup

setup(
    setup_requires=['pbr',"pytest-runner"],
    package_dir={'':'src/'}, # Needed for distutils
    tests_require=["pytest"],
    pbr=True
)
