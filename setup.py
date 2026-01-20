# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "device_manager_service"
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
    description="Device Manager Service",
    author_email="vasco.m.campos@inesctec.pt",
    url="",
    keywords=["OpenAPI", "Device Manager Service"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['openapi/openapi.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['device_manager_service=device_manager_service.__main__:main']},
    long_description="""\
    Device Manager Service OpenAPI definition.  This service has the following functions: scan, add, delete, send commands, view measurements and state of the devices.  Find out more: [Device Manager Service documentation](https://gitlab.inesctec.pt/cpes/european-projects/interconnect/hems/hems-documentation/-/blob/master/Microservices/Device-Manager-Service.adoc)
    """
)

