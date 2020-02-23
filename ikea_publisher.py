#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

from urls_publisher import URLsPublisher
from ikea_publisher import IKEAScraper


def main(args):
    scraper = IKEAScraper(args)
    URLsPublisher.create(scraper, args) \
                 .run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IKEA URLs Publisher')
    args = parser.parse_args()

    main(args)
