# -*- coding: utf-8 -*-

# Scrapy settings for cobweb project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
from cobweb.utilities import load_list_from_file

import cobweb.resources.configs as configs

BOT_NAME = 'Googlebot'

SPIDER_MODULES = ['cobweb.spiders']
NEWSPIDER_MODULE = 'cobweb.spiders'


# Settings for RandomUserAgentMiddleware
REFERER_LIST = load_list_from_file('/cobweb/resources/referers.txt')
USER_AGENT_LIST = load_list_from_file('/cobweb/resources/useragents.txt')

# Settings for RandomProxyMiddleware
# Proxy list containing entries like <http://host1:port1>
RANDOM_PROXY_HTTP_PROXIES = load_list_from_file('/cobweb/resources/prod_proxies.txt')
# Mode to pick the next proxy: 1. Randomly 2. In the order in the proxy list
RANDOM_PROXY_MODE = 1

# Retry many times since proxies often fail
RETRY_TIMES = 1000
# Retry on most error codes since proxies fail for different reasons
RETRY_HTTP_CODES = [500, 503, 504, 514, 400, 401, 403, 404, 408]

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS=32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY=8
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN=16
#CONCURRENT_REQUESTS_PER_IP=16

# Disable cookies (enabled by default)
COOKIES_ENABLED=False

# Enable or disable downloader middlewares or your custom middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'cobweb.middlewares.random_useragent.RandomUserAgentMiddleware': 400,
    'cobweb.middlewares.random_proxy.RandomProxyMiddleware': 600,
}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   'cobweb.pipelines.mongodb.MongoDBPipeline': 100,
   #'cobweb.pipelines.dynamodb.DynamoDBPipeline': 101,
}

MONGODB_CREDENTIALS = configs.MONGODB_CREDENTIALS

AWS_ACCESS_KEY_ID = configs.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = configs.AWS_SECRET_ACCESS_KEY
DYNAMODB_PIPELINE_REGION_NAME = configs.DYNAMODB_PIPELINE_REGION_NAME
DYNAMODB_PIPELINE_TABLE_NAME = configs.DYNAMODB_PIPELINE_TABLE_NAME
