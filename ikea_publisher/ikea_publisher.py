# -*- coding: utf-8 -*-

from urls_publisher import Scraper


class IKEAScraper(Scraper):
    def __init__(self, config):
        super(IKEAScraper, self).__init__(config)

    def get_urls(self):
        pass
