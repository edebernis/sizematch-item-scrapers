#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from setuptools import setup, find_packages


version = re.search(r'^__version__\s*=\s*"(.*)"',
                    open('item_scrapers/__init__.py').read(), re.M) \
            .group(1)


with open("README.md", "rb") as f:
    long_descr = f.read().decode("utf-8")


setup(
    name="sizematch-item-scrapers",
    packages=find_packages(),
    version=version,
    description="Scrape items and publish them into RabbitMQ",
    long_description=long_descr,
    author="Emeric de Bernis",
    author_email="emeric.debernis@gmail.com",
    install_requires=[
        "requests>=2.21.0",
        "pika>=1.1.0"
    ],
    tests_require=[
        'pytest>=5.4.1',
        'mock>=4.0.2',
        'requests-mock>=1.7.0',
        'pika>=1.1.0'
    ]
)
