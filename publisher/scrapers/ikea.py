#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import logging

from publisher.scrapers import Scraper, Item


class IKEA(Scraper):
    SOURCE = 'ikea'
    CATEGORY_URLS_REGEX = re.compile(r'http.+/cat/([^/]+)/', (re.I + re.M))
    PRODUCT_URLS_REGEX = re.compile(r'http.+/p/([^/]+)/', (re.I + re.M))

    def __init__(self, args):
        self.base_url = args.get('base_url')
        self.lang = args.get('lang')
        self.categories_limit = args.get('categories_limit')
        self._result = {}

    def _fetch_categories(self):
        logging.debug('Fetching categories')

        url = '{}/{}/cat/products-products/'.format(self.base_url, self.lang)
        res = self.do_request('get', url)
        if not res:
            logging.error('Failed to fetch categories')
            return None

        categories = set(IKEA.CATEGORY_URLS_REGEX.findall(res.text))
        logging.debug('Fetched {} categories'.format(len(categories)))

        return list(categories)

    def _fetch_items(self, category):
        logging.debug('Fetching items of category {}'.format(category))

        url = '{}/{}/cat/{}/'.format(self.base_url, self.lang, category)
        res = self.do_request('get', url)
        if not res:
            logging.error('Failed to fetch items for category {}'
                          .format(category))
            return None

        items_url = IKEA.PRODUCT_URLS_REGEX.findall(res.text)
        logging.debug('Fetched {} items for category {}'
                      .format(len(items_url), category))

        return [
            Item(
                source=IKEA.SOURCE,
                urls=['{}/{}/p/{}'.format(self.base_url, self.lang, url)],
                lang=self.lang
            )
            for url in items_url]

    def scrape(self):
        """This method cannot be a generator as we need to remove
           duplicates"""
        categories = self._fetch_categories()
        if not categories:
            return []

        if self.categories_limit:
            categories = categories[:self.categories_limit]

        self._result['categories'] = len(categories)

        items = set()
        for category in categories:
            _items = self._fetch_items(category)
            if _items:
                items.update(_items)

        self._result['items'] = len(items)
        return list(items)

    def result(self):
        return self._result
