#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from mock import Mock
from pytest import fixture
from ikea_publisher import IKEAScraper


categories = None


@fixture
def scraper():
    return IKEAScraper({
        'base_url': 'https://www.ikea.com',
        'lang': 'gb/en'
    })


def test_fetch_categories(scraper):
    global categories
    categories = scraper._fetch_categories()
    assert len(categories) > 0


def test_fetch_products(scraper):
    global categories
    products = scraper._fetch_products(list(categories)[0])
    assert len(products) > 0


def test_get_urls(scraper, monkeypatch):
    with monkeypatch.context() as m:
        categories = {'category1', 'category2', 'category3'}
        mock_fetch_categories = Mock(return_value=categories)
        m.setattr(scraper, '_fetch_categories', mock_fetch_categories)

        products = [
            'https://www.ikea.com/products/1',
            'https://www.ikea.com/products/2'
        ]
        mock_fetch_products = Mock(return_value=products)
        m.setattr(scraper, '_fetch_products', mock_fetch_products)

        urls = scraper.get_urls()

        mock_fetch_categories.assert_called_once()
        assert mock_fetch_products.call_count == 3
        assert urls == set(products)
