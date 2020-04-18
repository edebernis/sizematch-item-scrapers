#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sizematch.protobuf.items.items_pb2 import Item, Lang

from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import requests


class BaseScraper:
    def __init__(self, config):
        self.name = config.get('name')
        self.routing_key = config.get('routing_key')

    def _get_session(self, protocol, retries):
        session = requests.Session()

        if retries:
            retry_obj = Retry(total=retries,
                              read=retries,
                              connect=retries,
                              backoff_factor=0.3)
            session.mount('{}://'.format(protocol),
                          HTTPAdapter(max_retries=retry_obj))

        return session

    def do_request(self, method, url, timeout=3, retries=3):
        protocol = url.split(':', 1)[0]
        session = self._get_session(protocol, retries)
        try:
            return getattr(session, method.lower())(url, timeout=timeout)
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError):
            return None

    def scrape(self):
        items = []
        results = {}
        for lang in self.__class__.LANGS:
            try:
                items_urls, result = self.get_items_urls(lang)
                items += [
                    Item(
                        source=self.name,
                        urls=urls,
                        lang=lang
                    ) for urls in items_urls
                ]
                results[Lang.Name(lang)] = result
            except Exception as e:
                results[Lang.Name(lang)] = str(e)

        return items, results

    def get_items_urls(self):
        raise NotImplementedError()
