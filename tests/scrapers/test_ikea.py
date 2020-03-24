#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from mock import Mock
from pytest import fixture
from publisher import Scraper, Item


categories = None


@fixture
def scraper():
    return Scraper.create({
        'name': 'ikea',
        'base_url': 'https://www.ikea.com',
        'lang': 'gb/en'
    })


def test_fetch_categories(scraper):
    global categories
    categories = scraper._fetch_categories()
    assert len(categories) > 0


def test_fetch_items(scraper):
    global categories
    items = scraper._fetch_items(list(categories)[0])
    assert len(items) > 0


def test_scrape(scraper, monkeypatch):
    with monkeypatch.context() as m:
        categories = {'category1', 'category2', 'category3'}
        mock_fetch_categories = Mock(return_value=categories)
        m.setattr(scraper, '_fetch_categories', mock_fetch_categories)

        items = [
            Item(['https://www.ikea.com/products/1'], 'en'),
            Item(['https://www.ikea.com/products/2'], 'en')
        ]
        mock_fetch_items = Mock(return_value=items)
        m.setattr(scraper, '_fetch_items', mock_fetch_items)

        result = scraper.scrape()

        mock_fetch_categories.assert_called_once()
        assert mock_fetch_items.call_count == 3
        assert set(result) == set(items)
