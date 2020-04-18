#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from . import BaseScraper
from sizematch.protobuf.items.items_pb2 import Lang

import re
import logging


MAIN_CATEGORY = "products-products"
CATEGORY_URLS_REGEX = re.compile(r'http.+/cat/([a-z0-9\-\_]+)(?:\?|/)',
                                 (re.I + re.M))
PRODUCT_URLS_REGEX = re.compile(r'http.+/p/([a-z0-9\-\_]+)(?:\?|/)',
                                (re.I + re.M))


class Scraper(BaseScraper):
    LANGS = [
        Lang.EN,
        Lang.FR
    ]

    def __init__(self, config):
        super(Scraper, self).__init__(config)

        self.base_url = config.get('base_url')
        self.suffix = config.get('suffix')

    def _get_base_url(self, lang):
        return '{}/{}'.format(
            self.base_url,
            self.suffix.get(Lang.Name(lang).lower())
        )

    def _get_page(self, lang, category, page=None):
        logging.debug('Fetching items urls of category {}, page {}'.format(
            category, page if page else 1))

        url = '{}/cat/{}/'.format(self._get_base_url(lang), category)
        if page is not None:
            url = '{}page-{}/'.format(url, page)

        res = self.do_request('get', url)
        if not res:
            logging.error('Failed to get category {}'
                          .format(category))
            return set(), set()

        return (set(CATEGORY_URLS_REGEX.findall(res.text)),
                set(PRODUCT_URLS_REGEX.findall(res.text)))

    def _get_category(self, lang, category):
        categories = set()
        urls = set()
        page = None

        while True:
            new_categories, new_urls = self._get_page(lang, category, page)

            if new_categories.issubset(categories) and \
               new_urls.issubset(urls):
                return categories, urls

            categories.update(new_categories)
            urls.update(new_urls)

            page = page+1 if page else 2

    def _get_all(self, lang, category, categories, urls):
        if category in categories:
            return

        new_categories, new_urls = self._get_category(lang, category)

        categories.add(category)
        urls.update(new_urls)

        for new_category in new_categories:
            self._get_all(lang, new_category, categories, urls)

        return categories, urls

    def get_items_urls(self, lang):
        categories, urls = self._get_all(
            lang=lang,
            category=MAIN_CATEGORY,
            categories=set(),
            urls=set()
        )

        result = {
            'categories': len(categories),
            'items': len(urls)
        }

        return [
            ['{}/p/{}'.format(self._get_base_url(lang), url)]
            for url in urls
        ], result
