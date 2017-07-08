# -*- coding: utf-8 -*-

# Implement your custom middlewares here. 
# 
# See the official documentation:
#     http://doc.scrapy.org/en/latest/topics/downloader-middleware.html

import random
import logging

from scrapy.conf import settings

log = logging.getLogger('cobweb.scrapy.middlewares.RandomProxyMiddleware')

class RandomProxyMiddleware(object):
    def __init__(self, settings):
        self.proxies = settings.get('RANDOM_PROXY_HTTP_PROXIES')
        self.mode = settings.get('RANDOM_PROXY_MODE')

        if self.proxies is None:
            raise KeyError('HTTP_PROXIES setting is missing')

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_request(self, request, spider):
        if len(self.proxies) == 0:
            raise ValueError('No Proxy Left!!!')

        if self.mode == 2:
            proxy_address = self.proxies[0]
        else:
            proxy_address = random.choice(self.proxies)

        log.debug('Using proxy <%s>' % (proxy_address))

        request.meta['proxy'] = proxy_address
        request.meta['download_timeout'] = 10

    def process_exception(self, request, exception, spider):
        if 'proxy' not in request.meta:
            return

        proxy = request.meta['proxy']
        try:
            self.proxies.remove(proxy)
        except ValueError:
            pass

        log.debug('Removing failed proxy <%s>, %d proxies left' % (
                    proxy, len(self.proxies)))
