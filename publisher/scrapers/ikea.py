#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import logging

from publisher.scrapers import Scraper


class IKEA(Scraper):
    CATEGORY_URLS_REGEX = re.compile(r'http.+/cat/([^/]+)/', (re.I + re.M))
    PRODUCT_URLS_REGEX = re.compile(r'http.+/p/([^/]+)/', (re.I + re.M))

    def __init__(self, config):
        super(IKEA, self).__init__(config)

        self.base_url = config.get('base_url')
        self.lang = config.get('lang')

    def _fetch_categories(self):
        logging.debug('Fetching categories')

        url = '{}/{}/cat/products-products/'.format(self.base_url, self.lang)
        res = self.do_request('get', url)
        if not res:
            logging.error('Failed to fetch categories')
            return None

        categories = set(IKEA.CATEGORY_URLS_REGEX.findall(res.text))
        logging.debug('Fetched {} categories'.format(len(categories)))

        return categories

    def _fetch_products(self, category):
        logging.debug('Fetching products of category {}'.format(category))

        url = '{}/{}/cat/{}/'.format(self.base_url, self.lang, category)
        res = self.do_request('get', url)
        if not res:
            logging.error('Failed to fetch products for category {}'
                          .format(category))
            return None

        products = IKEA.PRODUCT_URLS_REGEX.findall(res.text)
        logging.debug('Fetched {} products for category {}'
                      .format(len(products), category))

        return products

    def scrape(self):
        """This method cannot be a generator as we need to remove
           duplicates"""
        urls = set()

        categories = self._fetch_categories()
        if not categories:
            return []

        for category in list(categories)[:1]:
            products = self._fetch_products(category)
            if products:
                products_urls = [
                    '{}/{}/p/{}'.format(self.base_url, self.lang, product)
                    for product in products
                ]
                urls.update(products_urls)

        return [{'url': url} for url in urls]
