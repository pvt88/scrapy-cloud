import httplib
import scrapy

from datetime import datetime

from cobweb.items import IPItem

class IPSpider(scrapy.Spider):
    name = 'ip_spider'
    start_urls = [
    	"http://ifconfig.me/ip"
    ]

    def parse(self, response):
        item = IPItem()
        item["status"] = response.status
        item['date'] = datetime.utcnow()
        if item["status"] == httplib.OK:
            item['ip_address'] = response.css('body p::text').extract()[0]

        yield item
