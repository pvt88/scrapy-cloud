import scrapy
import json

from datetime import datetime

from cobweb.items import IPItem

class IPSpider(scrapy.Spider):
    name = 'ip_spider'
    start_urls = [
    	"http://ip-api.com/json"
    ]

    def parse(self, response):
        item = IPItem()
        item["status"] = response.status
        item['date'] = datetime.utcnow()

        obj = json.loads(response.body_as_unicode())
        item['lat'] = obj.get('lat')
        item['lon'] = obj.get('lon')
        item['timezone'] = obj.get('timezone')
        item['org'] = obj.get('org')

        #item['json'] = json.loads(response.body_as_unicode())

        yield item
