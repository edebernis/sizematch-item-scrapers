#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from item_scrapers.publisher import Publisher

from flask import Flask, abort
from celery import Celery
from celery.result import AsyncResult
from importlib import import_module
import os
import json
import logging


def create_flask_app():
    amqp_url = 'amqp://{}:{}@{}:{}/{}'.format(
        os.environ.get('RABBITMQ_USERNAME'),
        os.environ.get('RABBITMQ_PASSWORD'),
        os.environ.get('RABBITMQ_HOST'),
        os.environ.get('RABBITMQ_PORT', 5672),
        os.environ.get('RABBITMQ_VHOST', '')
    )
    rpc_url = 'rpc://{}:{}@{}:{}/{}'.format(
        os.environ.get('RABBITMQ_USERNAME'),
        os.environ.get('RABBITMQ_PASSWORD'),
        os.environ.get('RABBITMQ_HOST'),
        os.environ.get('RABBITMQ_PORT', 5672),
        os.environ.get('RABBITMQ_VHOST', '')
    )

    app = Flask(__name__)
    app.config.update(
        CELERY_BROKER_URL=amqp_url,
        CELERY_RESULT_BACKEND=rpc_url
    )
    return app


def create_celery_app(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


def create_scrapers():
    scrapers_conf = json.loads(
        open(os.environ.get('SCRAPERS_CONF_FILE')).read()
    )
    return {
        conf.get('name'): getattr(
            import_module('item_scrapers.scrapers.%s' % conf.get('name')),
            'Scraper'
        )(conf)
        for conf in scrapers_conf
    }


def create_publisher():
    return Publisher.create(
        os.environ.get('RABBITMQ_HOST'),
        os.environ.get('RABBITMQ_PORT', 5672),
        os.environ.get('RABBITMQ_USERNAME'),
        os.environ.get('RABBITMQ_PASSWORD'),
        os.environ.get('RABBITMQ_VHOST', ''),
        os.environ.get('RABBITMQ_CONNECTION_ATTEMPTS', 3),
        os.environ.get('RABBITMQ_HEARTBEAT', 3600),
        os.environ.get('RABBITMQ_APP_ID'),
        os.environ.get('PUBLISHER_EXCHANGE_NAME'))


###############################################################################
# MAIN
###############################################################################

if os.environ.get('debug', False):
    logging.basicConfig(level=logging.DEBUG)

scrapers = create_scrapers()
publisher = create_publisher()

app = application = create_flask_app()
celery = create_celery_app(app)


@celery.task()
def scrape_task(source):
    scraper = scrapers.get(source)
    return publisher.run(scraper)


@app.route('/sources/<source>/scrape', methods=['POST'])
def scrape(source):
    scraper = scrapers.get(source)
    if scraper is None:
        abort(400, 'Unknown source')

    result = scrape_task.delay(source)
    return {
        'task': {
            'id': result.id,
            'state': result.state,
            'source': source
        }
    }


@app.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    result = AsyncResult(task_id, app=celery)
    task = {
        'id': result.id,
        'state': result.state
    }
    if result.ready():
        task.update({
            'info': result.info
        })
    return {'task': task}
