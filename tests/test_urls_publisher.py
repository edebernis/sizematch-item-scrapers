#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests_mock
from mock import Mock
from pytest import fixture, raises
from pika.channel import Channel
from pika import BasicProperties, SelectConnection
from urls_publisher import Scraper, URLsPublisher


@fixture
def scraper():
    return Scraper({})


@fixture
def urls_publisher(scraper):
    urls_publisher = URLsPublisher.create(scraper, {
        'exchange': 'exchange',
        'queue': 'queue',
        'routing_key': 'exchange.queue',
        'app_id': 'app'
    })

    urls_publisher.publisher._deliveries = []
    urls_publisher.publisher._acked = 0
    urls_publisher.publisher._nacked = 0
    urls_publisher.publisher._message_number = 0

    return urls_publisher


def test_scraper_do_request(scraper):
    with requests_mock.mock() as m:
        m.get('https://www.example.com/', text='data')
        response = scraper.do_request('get', 'https://www.example.com/')
        assert response.text == 'data'


def test_scraper_get_urls(scraper):
    with raises(NotImplementedError):
        scraper.get_urls()


def test_publisher_publish(urls_publisher, monkeypatch):
    with monkeypatch.context() as m:
        urls_publisher.publisher._channel = Channel(
            SelectConnection(), 1, lambda: 1)
        m.setattr(
            urls_publisher.publisher._channel,
            '_state',
            Channel.OPEN)

        mock_publish = Mock()
        m.setattr(
            urls_publisher.publisher._channel, 'basic_publish', mock_publish)

        message = {'url': 'https://www.example.com/page'}
        urls_publisher.publisher.publish(message)

        mock_publish.assert_called_once_with(
            exchange='exchange',
            routing_key='exchange.queue',
            body=json.dumps(message, ensure_ascii=False),
            properties=BasicProperties(
                app_id='app',
                content_type='application/json',
                delivery_mode=1))
