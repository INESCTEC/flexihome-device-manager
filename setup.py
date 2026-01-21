# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "energy_manager_service"
VERSION = "1.0.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [
    "connexion>=2.0.2",
    "swagger-ui-bundle>=0.0.2",
    "python_dateutil>=2.6.0"
]

setup(
    name=NAME,
    version=VERSION,
    description="Energy Manager Service",
    author_email="igor.c.abreu@inesctec.pt",
    url="",
    keywords=["OpenAPI", "Energy Manager Service"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['openapi/openapi.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['energy_manager_service=energy_manager_service.__main__:main']},
    long_description="""\
    Energy Manager Service OpenAPI definition.This service contains the requests to get energy schedule information. It computes and indicates an optimal operation schedule for the smart appliances.
    """
)

