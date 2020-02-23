# -*- coding: utf-8 -*-

import re
import logging
import requests

from urls_publisher import Scraper

logger = logging.getLogger(__name__)


class IKEAScraper(Scraper):
    CATEGORY_URLS_REGEX = re.compile(r'http.+/cat/([^/]+)/', (re.I + re.M))
    PRODUCT_URLS_REGEX = re.compile(r'http.+/p/([^/]+)/', (re.I + re.M))

    def __init__(self, config):
        super(IKEAScraper, self).__init__(config)

    def _fetch_categories(self):
        logger.debug('Fetching categories')

        url = '{}/{}/cat/products-products/'.format(self.base_url, self.lang)
        response = requests.get(url)

        categories = IKEAScraper.CATEGORY_URLS_REGEX.findall(response.text)
        logger.debug('Fetched {} categories'.format(len(categories)))

        return categories

    def _fetch_products(self, category):
        logger.debug('Fetching products of category {}'.format(category))

        url = '{}/{}/cat/{}/'.format(self.base_url, self.lang, category)
        response = requests.get(url)

        products = IKEAScraper.PRODUCT_URLS_REGEX.findall(response.text)
        logger.debug('Fetched {} products for category {}'
                     .format(len(products), category))

        return products

    def get_urls(self):
        urls = set()
        for category in self._fetch_categories():
            products = self._fetch_products(category)
            urls.update(products)

        return urls
