#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sizematch.protobuf.items.items_pb2 import Item, Lang
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from importlib import import_module
import requests


class Scraper:
    def __init__(self, source, lang):
        self.source = source
        self.lang = lang

    @staticmethod
    def create(source, lang, args):
        _lang = Lang.Value(lang.upper())
        if _lang is None:
            raise Exception('Unsupported lang: %s' % lang)

        scraper_class = _load_scraper(source)
        if scraper_class is not None:
            return scraper_class(source, _lang, args)

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
        items_urls, result = self.get_items_urls()
        items = [Item(source=self.source, urls=urls, lang=self.lang)
                 for urls in items_urls]

        return items, result

    def get_items_urls(self):
        raise NotImplementedError()


def _load_scraper(source):
    return {
        'ikea': getattr(import_module('item_scrapers.scrapers.ikea'), 'IKEA'),
    }.get(source)
