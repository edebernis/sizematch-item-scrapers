#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from setuptools import setup, find_packages


version = re.search(r'^__version__\s*=\s*"(.*)"',
                    open('ikea_publisher/__init__.py').read(), re.M) \
            .group(1)


with open("README.md", "rb") as f:
    long_descr = f.read().decode("utf-8")


setup(
    name="ikea_publisher",
    packages=find_packages(),
    version=version,
    description="Scrape IKEA categories and products and \
publish them into RabbitMQ",
    long_description=long_descr,
    author="Emeric de Bernis",
    author_email="emeric.debernis@gmail.com",
    install_requires=[
        "requests>=2.21.0",
        "pika>=1.1.0"
    ],
    tests_require=[
        'pytest>=5.4.1',
        'mock>=4.0.2'
    ]
)
