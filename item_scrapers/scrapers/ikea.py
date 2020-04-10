#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import logging

from . import Scraper


class IKEA(Scraper):
    CATEGORY_URLS_REGEX = re.compile(r'http.+/cat/([^/]+)/', (re.I + re.M))
    PRODUCT_URLS_REGEX = re.compile(r'http.+/p/([^/]+)/', (re.I + re.M))

    def __init__(self, source, lang, args):
        super(IKEA, self).__init__(source, lang)

        self.base_url = args.get('base_url')
        self.categories_limit = args.get('categories_limit')

    def _fetch_categories(self):
        logging.debug('Fetching categories')

        url = '{}/cat/products-products/'.format(self.base_url)
        res = self.do_request('get', url)
        if not res:
            logging.error('Failed to fetch categories')
            return None

        categories = set(IKEA.CATEGORY_URLS_REGEX.findall(res.text))
        logging.debug('Fetched {} categories'.format(len(categories)))

        return list(categories)

    def _fetch_items_urls(self, category):
        logging.debug('Fetching items urls of category {}'.format(category))

        url = '{}/cat/{}/'.format(self.base_url, category)
        res = self.do_request('get', url)
        if not res:
            logging.error('Failed to fetch items urls for category {}'
                          .format(category))
            return None

        items_urls = IKEA.PRODUCT_URLS_REGEX.findall(res.text)
        logging.debug('Fetched {} items urls for category {}'
                      .format(len(items_urls), category))

        return items_urls

    def get_items_urls(self):
        """This method cannot be a generator as we need to remove
           duplicates"""
        result = {}

        categories = self._fetch_categories()
        if not categories:
            return []

        if self.categories_limit:
            categories = categories[:self.categories_limit]

        result['categories'] = len(categories)

        # Remove duplicate urls
        items_urls = set()
        for category in categories:
            urls = self._fetch_items_urls(category)
            if urls:
                items_urls.update(urls)

        result['items'] = len(items_urls)

        return [['{}/p/{}'.format(self.base_url, url)]
                for url in items_urls], result
