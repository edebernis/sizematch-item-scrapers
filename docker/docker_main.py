#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging

from urls_publisher import URLsPublisher
from ikea_publisher import IKEAScraper


def load_config():
    config = {
        'scraper': {},
        'publisher': {}
    }
    try:
        new_config = open(os.environ.get('CONFIG_FILE')).read()
        config.update(json.loads(new_config))

        config['publisher']['host'] = os.environ.get('RABBITMQ_HOST')
        config['publisher']['port'] = os.environ.get('RABBITMQ_PORT')
        config['publisher']['username'] = os.environ.get('RABBITMQ_USER')
        config['publisher']['password'] = os.environ.get('RABBITMQ_PASS')
    except Exception:
        logging.exception('Failed to load configuration')
        return

    return config


def main(config):
    scraper = IKEAScraper(config.get('scraper'))
    URLsPublisher.create(scraper, config.get('publisher')) \
                 .run()


if __name__ == '__main__':
    config = load_config()
    if not config:
        sys.exit(1)

    if config.get('debug', False):
        logging.basicConfig(level=logging.DEBUG)

    main(config)
