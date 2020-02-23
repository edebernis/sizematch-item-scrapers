# -*- coding: utf-8 -*-

__version__ = "0.0.1"

import logging

from .ikea_publisher import IKEAScraper  # noqa: F401


def setup_logger(level):
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    ch = logging.StreamHandler()
    ch.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
