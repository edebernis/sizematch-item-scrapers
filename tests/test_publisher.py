#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from mock import Mock
from pytest import fixture
from pika.channel import Channel
from pika import BasicProperties, SelectConnection
from publisher import Publisher


@fixture
def publisher():
    publisher = Publisher.create({
        'exchange': 'exchange',
        'queue': 'queue',
        'routing_key': 'exchange.queue',
        'app_id': 'app'
    })

    publisher._deliveries = []
    publisher._acked = 0
    publisher._nacked = 0
    publisher._message_number = 0

    return publisher


def test_publish(publisher, monkeypatch):
    with monkeypatch.context() as m:
        publisher._channel = Channel(
            SelectConnection(), 1, lambda: 1)
        m.setattr(
            publisher._channel,
            '_state',
            Channel.OPEN)

        mock_publish = Mock()
        m.setattr(
            publisher._channel, 'basic_publish', mock_publish)

        item = {'url': 'https://www.example.com/page'}
        publisher._publish(item)

        mock_publish.assert_called_once_with(
            exchange='exchange',
            routing_key='exchange.queue',
            body=json.dumps(item, ensure_ascii=False),
            properties=BasicProperties(
                app_id='app',
                content_type='application/json',
                delivery_mode=1),
            mandatory=True)
