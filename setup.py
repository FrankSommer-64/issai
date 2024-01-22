# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    bsd3_license = f.read()

setup(
    name='issai',
    version='0.1.0',
    description='Framework to run tests specified in Kiwi Test Case Management System',
    long_description=readme,
    author='Frank Sommer',
    author_email='frank@sherpa-software.de',
    url='https://github.com/frsommer64/issai',
    license=bsd3_license,
    packages=find_packages(exclude=('tests', 'docs'))
)
