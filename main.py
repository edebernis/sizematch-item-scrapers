#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from item_scrapers import Source, Scraper, Publisher

from flask import Flask, abort
from celery import Celery
from celery.result import AsyncResult
import os
import yaml
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


def load_sources():
    sources = {}
    for root, _, files in os.walk(os.environ.get('SOURCES_DIRECTORY')):
        for file in files:
            name, ext = tuple(os.path.splitext(file))
            if ext.lower() in ('.yml', '.yaml'):
                path = os.path.join(root, file)
                config = yaml.safe_load(open(path).read())
                sources[name] = Source(name, config)

    return sources


def create_scraper():
    return Scraper()


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
        os.environ.get('PUBLISHER_EXCHANGE_NAME'),
        os.environ.get('PUBLISHER_ROUTING_KEY_PREFIX'),
        os.environ.get('PUBLISHER_QUEUE_NAME_PREFIX'))


###############################################################################
# MAIN
###############################################################################

if os.environ.get('debug', False):
    logging.basicConfig(level=logging.DEBUG)

sources = load_sources()
scraper = create_scraper()
publisher = create_publisher()

app = application = create_flask_app()
celery = create_celery_app(app)


@celery.task()
def scrape_task(source_name):
    source = sources.get(source_name)
    items = scraper.scrape(source)
    publisher.publish(source, items)


@app.route('/sources/<source>/scrape', methods=['POST'])
def scrape(source):
    if source not in sources:
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
