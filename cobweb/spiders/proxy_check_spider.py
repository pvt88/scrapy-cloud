import scrapy

from datetime import datetime
from cobweb.items import ProxyItem

class ProxyCheckSpider(scrapy.Spider):
    name = 'proxy_check_spider'

    def __init__(self, url=None, max_depth=500, *args, **kwargs):
        super(ProxyCheckSpider, self).__init__(*args, **kwargs)
        self.start_urls.append(url)
        self.index = 1
        self.max_depth = int(max_depth)

    def parse(self, response):
        item = ProxyItem()
        item["status"] = response.status
        item['date'] = datetime.utcnow()
        item['ip'] = response.meta.get('proxy')

        yield item

        if self.index < self.max_depth:
            self.index += 1
            yield scrapy.Request(self.start_urls[0], dont_filter=True, callback=self.parse)

