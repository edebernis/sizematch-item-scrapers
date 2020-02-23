#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import base64
import logging

from urls_publisher import URLsPublisher
from ikea_publisher import IKEAScraper


def _main(config):
    scraper = IKEAScraper(config)
    URLsPublisher.create(scraper, config) \
                 .run()


def main_pubsub(event, context):
    """Google Background Cloud Function to be triggered by Pub/Sub"""
    logging.info("""This Function was triggered by messageId {} published at {}
    """.format(context.event_id, context.timestamp))

    if 'data' not in event:
        raise RuntimeError('No config data specified')

    config_str = base64.b64decode(event['data']).decode('utf-8')
    config = json.loads(config_str)

    _main(config)
