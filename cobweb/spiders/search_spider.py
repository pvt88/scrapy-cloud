import httplib
import scrapy

from datetime import datetime
from cobweb.items import PropertyItem
from cobweb.utilities import extract_number

class SearchSpider(scrapy.Spider):
    MAX_DEPTH = 10;
    name = 'search_spider'

    def __init__(self, vendor=None, crawl_url=None, *args, **kwargs):
        super(SearchSpider, self).__init__(*args, **kwargs)
        self.vendor = vendor
        self.crawl_url = crawl_url
        self.index = 1
        self.start_urls = [self.vendor + self.crawl_url]

    def parse(self, response):
        #check if response it not a HtmlResponse already
        if not isinstance(response, scrapy.http.response.html.HtmlResponse): 
            response = scrapy.http.response.html.HtmlResponse(response.url,body=response.body)

        selector = scrapy.Selector(response)

        search_results = selector.xpath(u'//div[@class="Main"]//h3//a//@href').extract()

        last_index = int(extract_number(selector.xpath(u'//div[@class="background-pager-right-controls"]//a//@href').extract()[-1]))

        for row in search_results:
            item = PropertyItem()
            item["vendor"] = self.vendor
            item["link"] = self.vendor + row
            item["created_date"] = datetime.utcnow()
            item["last_crawled_date"] = None
            yield item

        
        if self.index < last_index and self.index < self.MAX_DEPTH:
            self.index += 1 
            next_url = self.vendor + self.crawl_url + "/p" + str(self.index)
            print "Parsing the next page: {}".format(next_url)
            yield scrapy.Request(next_url, callback=self.parse)


