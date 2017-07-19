# -*- coding: utf-8 -*-

from pymongo import MongoClient # pymongo>=3.2

from scrapy.conf import settings
from scrapy.exceptions import DropItem
from scrapy import log
from cobweb.items import HouseItem, PropertyItem, ProxyItem

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
                raise DropItem("Missing {}!".format(data))

        if valid:
            if isinstance(item, ProxyItem):
                self.collection = self.db['proxies']
                self.collection.update({"ip": item['ip']},
                                       {"$setOnInsert": {"date": item['date'],
                                                         "status": item['status']
                                                         },
                                        },
                                       upsert=True)
                log.msg("Added Proxy Item to database!", level=log.DEBUG, spider=spider)


            if isinstance(item, PropertyItem):
                self.collection = self.db['property_list']

                self.collection.update({"property_id": item['property_id'],
                                        "vendor": item['vendor'],
                                        "type": item['type']},
                                       {"$setOnInsert": {"created_date": item['created_date'],
                                                         "listing_type": item['listing_type'],
                                                         "last_indexed_date": item['last_indexed_date'],
                                                         "property_size_raw": item['property_size_raw'],
                                                         "property_size": item['property_size'],
                                                         "property_size_unit": item['property_size_unit'],
                                                         "property_price_raw": item['property_price_raw'],
                                                         "property_price": item['property_price'],
                                                         "property_price_unit": item['property_price_unit'],
                                                         "property_area": item['property_area'],
                                                         "posted_date": item['posted_date'],
                                                         "link": item['link']
                                                        },
                                       },
                                       upsert=True)

                log.msg("Update Property Item in MongoDB database!", level=log.DEBUG, spider=spider)
                
        return item