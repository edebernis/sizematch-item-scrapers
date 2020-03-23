#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from google.cloud import secretmanager_v1beta1 as secretmanager
import os
import sys
import json
import base64
import logging

from publisher import Publisher, Scraper


def get_secret(secret_id, version='latest'):
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.environ.get('GCP_PROJECT')
    name = client.secret_version_path(project_id, secret_id, version)
    response = client.access_secret_version(name)
    return response.payload.data.decode('utf-8')


def load_config(event):
    config = {
        'scraper': {},
        'publisher': {}
    }
    try:
        new_config = base64.b64decode(event.get('data')).decode('utf-8')
        config.update(json.loads(new_config))

        config['publisher']['host'] = os.environ.get('RABBITMQ_HOST')
        config['publisher']['port'] = os.environ.get('RABBITMQ_PORT')
        config['publisher']['username'] = os.environ.get('RABBITMQ_USER')
        config['publisher']['password'] = get_secret('rabbitmq-password')
    except Exception:
        logging.exception('Failed to load configuration')
        return

    return config


def main(config):
    scraper = Scraper.create(config.get('scraper'))
    publisher = Publisher.create(config.get('publisher'))

    publisher.run(scraper)


def entrypoint_pubsub(event, context):
    """Google Background Cloud Function to be triggered by Pub/Sub"""
    logging.info("""This Function was triggered by messageId {} published at {}
    """.format(context.event_id, context.timestamp))

    config = load_config(event)
    if not config:
        sys.exit(1)

    if config.get('debug', False):
        logging.basicConfig(level=logging.DEBUG)

    main(config)
