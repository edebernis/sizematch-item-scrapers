#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from importlib import import_module
import requests


class Scraper:
    def __init__(self, config):
        self.config = config

    @staticmethod
    def create(config):
        scraper_class = _load_scraper(config.get('name'))
        if scraper_class is not None:
            return scraper_class(config)

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
        raise NotImplementedError()


def _load_scraper(name):
    return {
        'ikea': getattr(import_module('publisher.scrapers.ikea'), 'IKEA'),
    }.get(name)
