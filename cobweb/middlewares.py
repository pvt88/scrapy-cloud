# -*- coding: utf-8 -*-

# Implement your custom middlewares here. 
# 
# See the official documentation:
#     http://doc.scrapy.org/en/latest/topics/downloader-middleware.html

import random
import logging

from twisted.internet import defer
from twisted.internet.error import TimeoutError, DNSLookupError, \
        ConnectionRefusedError, ConnectionDone, ConnectError, \
        ConnectionLost, TCPTimedOutError

from scrapy.exceptions import NotConfigured
from scrapy.utils.response import response_status_message
from scrapy.xlib.tx import ResponseFailed

from scrapy.conf import settings

log = logging.getLogger('scrapy.middlewares')

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
        request.meta['download_timeout'] = 60

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

class RetryMiddleware(object):
    EXCEPTIONS_TO_RETRY = (defer.TimeoutError, TimeoutError, DNSLookupError,
                           ConnectionRefusedError, ConnectionDone, ConnectError,
                           ConnectionLost, TCPTimedOutError, ResponseFailed,
                           IOError, AttributeError)

    def __init__(self, settings):
        if not settings.getbool('RETRY_ENABLED'):
            raise NotConfigured
        self.max_retry_times = settings.getint('RETRY_TIMES')
        self.retry_http_codes = set(int(x) for x in settings.getlist('RETRY_HTTP_CODES'))
        self.priority_adjust = settings.getint('RETRY_PRIORITY_ADJUST')

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        return response

    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) \
                and not request.meta.get('dont_retry', False):
             return self._retry(request, exception, spider)

    def _retry(self, request, reason, spider):
        retries = request.meta.get('retry_times', 0) + 1

        if retries <= self.max_retry_times:
            log.debug("Retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                         extra={'spider': spider})
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.dont_filter = True
            retryreq.priority = request.priority + self.priority_adjust
            return retryreq
        else:
            log.debug("Gave up retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                         extra={'spider': spider})
