# -*- coding: utf-8 -*-

# Implement your custom middlewares here. 
# 
# See the official documentation:
#     http://doc.scrapy.org/en/latest/topics/downloader-middleware.html

import random
import logging

from scrapy.conf import settings

log = logging.getLogger('cobweb.scrapy.middlewares.RandomUserAgentMiddleware')

class RandomUserAgentMiddleware(object):
    def process_request(self, request, spider):
        ua  = random.choice(settings.get('USER_AGENT_LIST'))
        if ua:
            request.headers.setdefault('User-Agent', ua)

        re  = random.choice(settings.get('REFERER_LIST'))
        if re:
            request.headers.setdefault('Referer', re)
