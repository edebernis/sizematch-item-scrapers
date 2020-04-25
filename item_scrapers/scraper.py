#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sizematch.protobuf.items.items_pb2 import Item, Lang
from .utils import urljoin

from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import requests
import logging
import itertools


class Product:
    def __init__(self, id, urls, slug=None):
        self.id = id
        self.urls = urls
        self.slug = slug

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Product):
            return NotImplemented

        return self.id == self.id

    def __repr__(self):
        return "Product id={} urls={} slug={}".format(
            self.id, self.urls, self.slug
        )


class Category:
    def __init__(self, id, url, slug=None):
        self.id = id
        self.url = url
        self.slug = slug

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Category):
            return NotImplemented

        return self.id == self.id

    def __repr__(self):
        return "Category id={} url={} slug={}".format(
            self.id, self.url, self.slug
        )


class Scraper:
    def __init__(self):
        pass

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

    def _gen_user_agent(self):
        return 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) \
AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'

    def _get_accept_language_header(self, lang):
        return {
            'en': 'en-GB,en;q=0.9,en-US;q=0.8',
            'fr': 'fr-FR;q=0.9,fr;q=0.8'
        }.get(lang.lower())

    def _get_headers(self, lang):
        return {
            'Accept-Language': self._get_accept_language_header(lang),
            'User-Agent': self._gen_user_agent()
        }

    def _do_request(self, method, url, params, lang, timeout=5, retries=1):
        protocol = url.split(':', 1)[0]
        session = self._get_session(protocol, retries)
        headers = self._get_headers(lang)

        try:
            logging.debug('Fetch URL={}, Params={}'.format(url, params))
            return getattr(session, method.lower())(
                url,
                params=params,
                timeout=timeout,
                headers=headers,
                allow_redirects=False
            )
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError):
            return None

    def _fetch(self, url, params, lang):
        res = self._do_request('get', url, params, lang)
        if not res:
            logging.warning(
                'Failed to fetch page. URL={}, Params={}'.format(url, params)
            )
            return ""

        return res.text

    def _paginate(self, category, products, source, lang, brand):
        for url, params in source.paginate_category(category, lang, brand):
            html = self._fetch(url, params, lang)

            new_categories = {
                Category(
                    id=match.group('id'),
                    url=urljoin(
                        source.get_base_url(lang, brand),
                        match.group('url')
                    ),
                    slug=match.groupdict().get('slug')  # None if undefined
                )
                for match in source.get_categories_regex()
                                   .finditer(html)
            }

            new_products = {
                Product(
                    id=match.group('id'),
                    urls=[urljoin(
                        source.get_base_url(lang, brand),
                        match.group('url')
                    )],
                    slug=match.groupdict().get('slug')  # None if undefined
                )
                for match in source.get_products_regex()
                                   .finditer(html)
            }

            yield new_categories, new_products

            # Apply delay if any
            source.apply_delay()

    def _scrape_category(self, category, products, source, lang, brand):
        categories = set()
        for new_categories, new_products in self._paginate(
            category, products, source, lang, brand
        ):
            if new_categories.issubset(categories) and \
               new_products.issubset(products):
                return set(list(categories)[:2])

            categories.update(new_categories)
            products.update(new_products)

    def _walk(self, category, categories, products, source, lang, brand):
        categories.add(category)

        for cat in self._scrape_category(
          category, products, source, lang, brand
        ):
            if cat not in categories:
                self._walk(cat, categories, products, source, lang, brand)

    def _get_all(self, source, lang, brand):
        categories = set()
        products = set()
        base_category = Category(
            id=0,
            url=source.get_base_url(lang, brand),
            slug='base-category'
        )

        self._walk(base_category, categories, products, source, lang, brand)
        return categories, products

    def scrape(self, source):
        for lang, brand in itertools.product(
          source.get_langs(),
          source.get_brands()
        ):
            categories, products = self._get_all(source, lang, brand)
            logging.info("[Lang {}, Brand {}] {} categories, {} products"
                         .format(lang, brand, len(categories), len(products)))

            for product in products:
                yield Item(
                    source=source.name,
                    lang=Lang.Value(lang.upper()),
                    brand=brand,
                    urls=product.urls
                )
