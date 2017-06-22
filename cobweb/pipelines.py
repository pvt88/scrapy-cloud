# -*- coding: utf-8 -*-

# Implement your pipelines here. For an overview of the scrapy architecture, refer to the official documentation:
#
#     http://doc.scrapy.org/en/latest/topics/architecture.html

from pymongo import MongoClient # pymongo>=3.2

from scrapy.conf import settings
from scrapy.exceptions import DropItem
from scrapy import log

from items import IPItem, HouseItem, PropertyItem

# For example, here is an implementation of a pipeline that processes
# and stores the spider's crawled data into MongoDB database.
class MongoDBPipeline(object):

    def __init__(self):
        # See PyMongo docs for more details about the connection options:
        #
        #   https://api.mongodb.org/python/3.0/api/pymongo/mongo_client.html#pymongo.mongo_client.MongoClient
        #
        mongodb_credentials = settings.get('MONGODB_CREDENTIALS')
        client = MongoClient(mongodb_credentials['server'],
                             mongodb_credentials['port'],
                             connectTimeoutMS=30000,
                             socketTimeoutMS=None,
                             socketKeepAlive=True)

        self.db = client[mongodb_credentials['database']]
        #self.db.authenticate(mongodb_credentials['username'], mongodb_credentials['password'])

    def process_item(self, item, spider):
        valid = True
        for data in item:
            if not data:
                valid = False
                raise DropItem("Missing {0}!".format(data))

        if valid:
            if isinstance(item, HouseItem): 
                self.collection = self.db['houses']
                self.collection.insert(dict(item))
                log.msg("Added houses to database!", level=log.DEBUG, spider=spider)

            if isinstance(item, PropertyItem):
                self.collection = self.db['property_list_rental']
                self.collection.update({"link": item['link'], 
                                        "property_id": item['property_id'],
                                        "vendor": item['vendor']},
                                       {"$setOnInsert": {"created_date": item['created_date'],
                                                         "last_indexed_date": item['last_indexed_date'],
                                                         "property_size": item['property_size'],
                                                         "property_size_unit": item['property_size_unit'],
                                                         "property_price": item['property_price'],
                                                         "property_price_unit": item['property_price_unit'],
                                                         "property_area": item['property_area'],
                                                         "posted_date": item['posted_date']
                                                        },
                                       },
                                       upsert=True)

                log.msg("Update PropertyItem in MongoDB database!", level=log.DEBUG, spider=spider)
                
        return item