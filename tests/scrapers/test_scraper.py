#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests_mock
from pytest import fixture, raises
from publisher import Scraper


@fixture
def scraper():
    return Scraper({})


def test_do_request(scraper):
    with requests_mock.mock() as m:
        m.get('https://www.example.com/', text='data')
        response = scraper.do_request('get', 'https://www.example.com/')
        assert response.text == 'data'


def test_scrape(scraper):
    with raises(NotImplementedError):
        scraper.scrape()
