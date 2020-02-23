#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import argparse

from urls_publisher import URLsPublisher
from ikea_publisher import IKEAScraper, setup_logger


def main(args):
    scraper = IKEAScraper(
        {
            'base_url': 'https://www.ikea.com',
            'lang': 'gb/en'
        })
    URLsPublisher.create(scraper, args) \
                 .run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IKEA URLs Publisher')
    parser.add_argument(
        "-v", "--verbose", help="Debug mode", action="store_true")
    args = parser.parse_args()

    setup_logger(logging.DEBUG if args.verbose else logging.INFO)
    main(args)
