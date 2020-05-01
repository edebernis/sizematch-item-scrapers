#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .utils import urljoin

from urllib.parse import urlsplit, urlunsplit
import re
import time


class Source:
    def __init__(self, name, config):
        self.name = name
        self.config = config

    def get_langs(self):
        return self.config.get('langs')

    def get_brands(self):
        return self.config.get('brands', [None])

    def _get_url_regex(self, regex):
        return re.compile('(?P<url>{})(?:\\?|/|#)'.format(regex))

    def get_categories_regex(self):
        return self._get_url_regex(
            self.config.get('categories').get('urlRegex')
        )

    def get_products_regex(self):
        return self._get_url_regex(
            self.config.get('products').get('urlRegex')
        )

    def get_base_url(self, lang, brand):
        base_url = self.config.get('baseUrl')
        selector = self.config.get('langSelector')
        if selector:
            return {
                'baseUrlSuffix': self._get_base_url_suffix,
                'baseUrlTLD': self._get_base_url_tld
            }.get(selector.get('mode'))(base_url, lang)

        return base_url

    def _get_base_url_suffix(self, base_url, lang):
        return urljoin(
            base_url,
            self.config.get('langSelector').get('mapping').get(lang)
        )

    def _get_base_url_tld(self, base_url, lang):
        url = urlsplit(base_url)
        netloc = re.sub(
            r'[a-z]+(:[0-9]+)?$',
            r'{}\1'.format(
                self.config.get('langSelector').get('mapping').get(lang)
            ),
            url.netloc)
        return urlunsplit(
            (url.scheme, netloc, url.path, url.query, url.fragment)
        )

    def _get_category_url(self, category, lang, brand):
        url = category.url
        params = {}

        if self.config.get('categories').get('trailing_slash') and \
           not url.endswith('/'):
            url += '/'

        selector = self.config.get('brandSelector')
        if selector and selector.get('mode') == 'categoryQueryParam':
            params.update(selector.get('mapping').get(brand))

        return url, params

    def paginate_category(self, category, lang, brand):
        url, params = self._get_category_url(category, lang, brand)
        pagination = self.config.get('categories').get('pagination')

        yield url, params
        yield from {
                'urlPathSuffix': self._paginate_category_path_suffix,
                'queryParam': self._paginate_category_query_param
            }.get(pagination.get('mode'))(url, params, pagination)

    def _paginate_category_path_suffix(self, url, params, pagination):
        start = int(pagination.get('start', 2))
        end = int(pagination.get('end', 1000))
        step = int(pagination.get('step', 1))
        for page in range(start, end, step):
            page_url = urljoin(url, pagination.get('format').format(page))
            yield page_url, params

    def _paginate_category_query_param(self, url, params, pagination):
        start = int(pagination.get('start', 2))
        end = int(pagination.get('end', 1000))
        step = int(pagination.get('step', 1))
        for page in range(start, end, step):
            params[pagination.get('key')] = page
            yield url, params

    def apply_delay(self):
        if 'delay' in self.config:
            time.sleep(int(self.config.get('delay')))
