# -*- coding: utf-8 -*-

# Implement your custom middlewares here. 
# 
# See the official documentation:
#     http://doc.scrapy.org/en/latest/topics/downloader-middleware.html

import random
import logging

from scrapy.conf import settings

log = logging.getLogger('scrapy.proxies')

class RandomUserAgentMiddleware(object):
    def process_request(self, request, spider):
        ua  = random.choice(settings.get('USER_AGENT_LIST'))
        if ua:
            request.headers.setdefault('User-Agent', ua)

        re  = random.choice(settings.get('REFERER_LIST'))
        if re:
            request.headers.setdefault('Referer', re)

class RandomProxyMiddleware(object):
    def __init__(self, settings):
        self.proxies = settings.get('HTTP_PROXIES')

        if self.proxies is None:
            raise KeyError('HTTP_PROXIES setting is missing')

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_request(self, request, spider):
        if len(self.proxies) == 0:
            raise ValueError('No Proxy Left!!!')

        proxy_address = random.choice(self.proxies)

        log.debug('Using proxy <%s>, %d proxies left' % (
                    proxy_address, len(self.proxies)))

        request.meta['proxy'] = proxy_address
        request.meta['download_timeout'] = 10

    def process_exception(self, request, exception, spider):
    	if 'proxy' not in request.meta:
            return

        proxy = request.meta['proxy']
        try:
            self.proxies.remove(proxy)
        except KeyError:
            pass

        log.info('Removing failed proxy <%s>, %d proxies left' % (
                    proxy, len(self.proxies)))
