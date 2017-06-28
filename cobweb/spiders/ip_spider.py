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

        json = json.loads(response.body_as_unicode())
        item['lat'] = json.get('lat')
        item['lon'] = json.get('lon')
        item['timezone'] = json.get('timezone')
        item['org'] = json.get('org')

        #item['json'] = json.loads(response.body_as_unicode())

        yield item
