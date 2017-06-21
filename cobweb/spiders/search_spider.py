import httplib
import scrapy

from datetime import datetime
from cobweb.items import PropertyItem
from cobweb.utilities import extract_number, extract_property_id

class SearchSpider(scrapy.Spider):
    name = 'search_spider'

    def __init__(self, vendor=None, crawl_url=None, max_depth=2, *args, **kwargs):
        super(SearchSpider, self).__init__(*args, **kwargs)
        self.vendor = vendor
        self.crawl_url = crawl_url
        self.index = 1
        self.max_depth = max_depth
        self.start_urls = [self.vendor + self.crawl_url]

    def parse(self, response):
        if not isinstance(response, scrapy.http.response.html.HtmlResponse): 
            response = scrapy.http.response.html.HtmlResponse(response.url,body=response.body)

        selector = scrapy.Selector(response)

        search_results = selector.xpath(u'//div[@class="Main"]//h3//a//@href').extract()

        page_numbers = selector.xpath(u'//div[@class="background-pager-right-controls"]//a//@href').extract()
        if page_numbers:
            last_index = int(extract_number(page_numbers[-1]))
        else:
            last_index = 0

        for row in search_results:
            item = PropertyItem()
            item["vendor"] = self.vendor
            item["link"] = self.vendor + row
            item["created_date"] = datetime.utcnow()
            item["last_indexed_date"] = datetime.utcnow()
            item["last_crawled_date"] = None
            item["property_id"] =  extract_property_id(item["link"])
            yield item

        
        if self.index < last_index and self.index < self.max_depth:
            self.index += 1 
            next_url = self.vendor + self.crawl_url + "/p" + str(self.index)
            yield scrapy.Request(next_url, callback=self.parse)


