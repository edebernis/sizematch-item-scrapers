#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import logging

from . import Scraper


class IKEA(Scraper):
    MAIN_CATEGORY = "products-products"
    CATEGORY_URLS_REGEX = re.compile(r'http.+/cat/([a-z0-9\-\_]+)(?:\?|/)',
                                     (re.I + re.M))
    PRODUCT_URLS_REGEX = re.compile(r'http.+/p/([a-z0-9\-\_]+)(?:\?|/)',
                                    (re.I + re.M))

    def __init__(self, source, lang, args):
        super(IKEA, self).__init__(source, lang)

        self.base_url = args.get('base_url')

    def _get_page(self, category, page=None):
        logging.debug('Fetching items urls of category {}, page {}'.format(
            category, page if page else 1))

        url = '{}/cat/{}/'.format(self.base_url, category)
        if page is not None:
            url = '{}page-{}/'.format(url, page)

        res = self.do_request('get', url)
        if not res:
            logging.error('Failed to get category {}'
                          .format(category))
            return set(), set()

        return (set(IKEA.CATEGORY_URLS_REGEX.findall(res.text)),
                set(IKEA.PRODUCT_URLS_REGEX.findall(res.text)))

    def _get_category(self, category):
        categories = set()
        urls = set()
        page = None

        while True:
            new_categories, new_urls = self._get_page(category, page)

            if new_categories.issubset(categories) and \
               new_urls.issubset(urls):
                return categories, urls

            categories.update(new_categories)
            urls.update(new_urls)

            page = page+1 if page else 2

    def _get_all(self, category, categories, urls):
        if category in categories:
            return

        new_categories, new_urls = self._get_category(category)

        categories.add(category)
        urls.update(new_urls)

        for new_category in new_categories:
            self._get_all(new_category, categories, urls)

        return categories, urls

    def get_items_urls(self):
        categories, urls = self._get_all(
            category=IKEA.MAIN_CATEGORY,
            categories=set(),
            urls=set())

        result = {
            'categories': len(categories),
            'items': len(urls)
        }

        return [['{}/p/{}'.format(self.base_url, url)]
                for url in urls], result
