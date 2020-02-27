# -*- coding: utf-8 -*-

import re
import logging

from urls_publisher import Scraper


class IKEAScraper(Scraper):
    CATEGORY_URLS_REGEX = re.compile(r'http.+/cat/([^/]+)/', (re.I + re.M))
    PRODUCT_URLS_REGEX = re.compile(r'http.+/p/([^/]+)/', (re.I + re.M))

    def __init__(self, config):
        super(IKEAScraper, self).__init__(config)

        self.base_url = config.get('base_url')
        self.lang = config.get('lang')

    def _fetch_categories(self):
        logging.debug('Fetching categories')

        url = '{}/{}/cat/products-products/'.format(self.base_url, self.lang)
        res = self.do_request('get', url)
        if not res:
            logging.error('Failed to fetch categories')
            return None

        categories = set(IKEAScraper.CATEGORY_URLS_REGEX.findall(res.text))
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

        products = IKEAScraper.PRODUCT_URLS_REGEX.findall(res.text)
        logging.debug('Fetched {} products for category {}'
                      .format(len(products), category))

        return products

    def get_urls(self):
        urls = set()

        categories = self._fetch_categories()
        if not categories:
            return None

        for category in categories:
            products = self._fetch_products(category)
            if products:
                urls.update(products)

        return urls
