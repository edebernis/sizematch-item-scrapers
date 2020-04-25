#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pika
import logging

LOGGER = logging.getLogger(__name__)


class Publisher:
    def __init__(self, amqp_url, app_id, exchange_name):
        self._connection = None
        self._channel = None
        self._deliveries = None
        self._acked = None
        self._nacked = None
        self._message_number = None
        self._stopping = False
        self._items = None

        self._url = amqp_url
        self._app_id = app_id
        self._exchange_name = exchange_name

    @staticmethod
    def create(host, port, username, password, vhost, connection_attempts,
               heartbeat, app_id, exchange_name):
        amqp_url = 'amqp://{}:{}@{}:{}/{}?connection_attempts={}&\
heartbeat={}'.format(
            username,
            password,
            host,
            port,
            vhost,
            connection_attempts,
            heartbeat)

        return Publisher(amqp_url, app_id, exchange_name)

    def publish(self, items):
        self._items = items
        self._start()

    def _start(self):
        self._reset()
        while not self._stopping:
            try:
                self._connection = self._connect()
                self._connection.ioloop.start()
            except KeyboardInterrupt:
                self._stop()
                if (self._connection is not None and
                        not self._connection.is_closed):
                    # Finish closing
                    self._connection.ioloop.start()

    def _reset(self):
        self._connection = None
        self._channel = None
        self._stopping = False
        self._deliveries = []
        self._acked = 0
        self._nacked = 0
        self._message_number = 0
        self._items = None

    def _on_started(self):
        try:
            for item in self._items:
                self._publish(item)
        finally:
            self._stop()

    def _connect(self):
        LOGGER.debug('Connecting to %s', self._url)
        return pika.SelectConnection(
            pika.URLParameters(self._url),
            on_open_callback=self._on_connection_open,
            on_open_error_callback=self._on_connection_open_error,
            on_close_callback=self._on_connection_closed)

    def _on_connection_open(self, _unused_connection):
        LOGGER.debug('Connection opened')
        self._open_channel()

    def _on_connection_open_error(self, _unused_connection, err):
        LOGGER.error('Connection open failed, reopening in 5 seconds: %s', err)
        self._connection.ioloop.call_later(5, self._connection.ioloop.stop)

    def _on_connection_closed(self, _unused_connection, reason):
        self._channel = None
        if self._stopping:
            self._connection.ioloop.stop()
        else:
            LOGGER.warning('Connection closed, reopening in 5 seconds: %s',
                           reason)
            self._connection.ioloop.call_later(5, self._connection.ioloop.stop)

    def _open_channel(self):
        LOGGER.debug('Creating a new channel')
        self._connection.channel(on_open_callback=self._on_channel_open)

    def _on_channel_open(self, channel):
        LOGGER.debug('Channel opened')
        self._channel = channel
        self._add_on_channel_close_callback()
        self._setup_exchange()

    def _add_on_channel_close_callback(self):
        LOGGER.debug('Adding channel close callback')
        self._channel.add_on_close_callback(self._on_channel_closed)

    def _on_channel_closed(self, channel, reason):
        LOGGER.warning('Channel %i was closed: %s', channel, reason)
        self._channel = None
        if not self._stopping:
            self._connection.close()

    def _setup_exchange(self):
        LOGGER.debug('Declaring exchange %s', self._exchange_name)
        self._channel.exchange_declare(
            exchange=self._exchange_name,
            exchange_type='direct',
            callback=self._on_exchange_declareok)

    def _on_exchange_declareok(self, _unused_frame):
        LOGGER.debug('Exchange declared')
        self._setup_queue()

    def _setup_queue(self):
        LOGGER.debug('Declaring queue %s', self._scraper.queue_name)
        self._channel.queue_declare(
            queue=self._scraper.queue_name,
            callback=self._on_queue_declareok)

    def _on_queue_declareok(self, _unused_frame):
        LOGGER.debug('Binding %s to %s with %s', self._exchange_name,
                     self._scraper.queue_name, self._scraper.routing_key)
        self._channel.queue_bind(
            self._scraper.queue_name,
            self._exchange_name,
            routing_key=self._scraper.routing_key,
            callback=self._on_bindok)

    def _on_bindok(self, _unused_frame):
        LOGGER.debug('Queue bound')
        self._enable_delivery_confirmations()

    def _enable_delivery_confirmations(self):
        LOGGER.debug('Issuing Confirm.Select RPC command')
        self._channel.confirm_delivery(self._on_delivery_confirmation)

        self._on_started()

    def _on_delivery_confirmation(self, method_frame):
        confirmation_type = method_frame.method.NAME.split('.')[1].lower()
        LOGGER.debug('Received %s for delivery tag: %i', confirmation_type,
                     method_frame.method.delivery_tag)

        if confirmation_type == 'ack':
            self._acked += 1
        elif confirmation_type == 'nack':
            self._nacked += 1

        self._deliveries.remove(method_frame.method.delivery_tag)
        LOGGER.debug(
            'Published %i messages, %i have yet to be confirmed, '
            '%i were acked and %i were nacked', self._message_number,
            len(self._deliveries), self._acked, self._nacked)

    def _publish(self, item):
        if self._channel is None or not self._channel.is_open:
            return

        properties = pika.BasicProperties(
            app_id=self._app_id,
            content_type='application/protobuf',
            delivery_mode=1)

        self._channel.basic_publish(
            exchange=self._exchange_name,
            routing_key=self._scraper.routing_key,
            body=item.SerializeToString(),
            properties=properties,
            mandatory=True)

        self._message_number += 1
        self._deliveries.append(self._message_number)

        LOGGER.debug('Published item # %i', self._message_number)

    def _stop(self):
        LOGGER.debug('Stopping publisher')
        self._stopping = True
        self._close_channel()
        self._close_connection()

    def _close_channel(self):
        if self._channel is not None:
            LOGGER.debug('Closing the channel')
            self._channel.close()

    def _close_connection(self):
        if self._connection is not None:
            LOGGER.debug('Closing connection')
            self._connection.close()
