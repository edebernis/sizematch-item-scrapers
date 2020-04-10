#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, abort
from celery import Celery
from celery.result import AsyncResult
from item_scrapers import Publisher, Scraper
import os
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


def create_publisher():
    return Publisher.create(
        os.environ.get('RABBITMQ_HOST'),
        os.environ.get('RABBITMQ_PORT', 5672),
        os.environ.get('RABBITMQ_USERNAME'),
        os.environ.get('RABBITMQ_PASSWORD'),
        os.environ.get('RABBITMQ_VHOST', ''),
        os.environ.get('RABBITMQ_CONNECTION_ATTEMPTS', 3),
        os.environ.get('RABBITMQ_HEARTBEAT', 3600),
        os.environ.get('RABBITMQ_APP_ID'))


###############################################################################
# MAIN
###############################################################################

if os.environ.get('debug', False):
    logging.basicConfig(level=logging.DEBUG)

app = application = create_flask_app()
celery = create_celery_app(app)
publisher = create_publisher()


@celery.task()
def scrape_task(source, lang, scraper_args, exchange_name, routing_key,
                queue_name):
    scraper = Scraper.create(source, lang, scraper_args)
    return publisher.run(scraper, exchange_name, routing_key, queue_name)


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


@app.route('/sources/<source>/<lang>/scrape', methods=['POST'])
def scrape(source, lang):
    if not request.json:
        abort(400, 'No parameters provided')

    scraper_args = request.json.get('scraper_args')
    exchange_name = request.json.get('exchange')
    routing_key = request.json.get('routing_key')
    queue_name = request.json.get('queue')

    if None in (scraper_args, exchange_name, routing_key, queue_name):
        abort(400, 'Parameters scraper_args, exchange, routing_key and queue \
are mandatory')

    result = scrape_task.delay(
        source, lang, scraper_args, exchange_name, routing_key, queue_name
    )

    return {
        'task': {
            'id': result.id,
            'state': result.state,
            'args': {
                'source': source,
                'lang': lang,
                'scraper_args': scraper_args,
                'exchange': exchange_name,
                'routing_key': routing_key,
                'queue': queue_name
            }
        }
    }
