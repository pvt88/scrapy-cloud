import scrapy

from datetime import datetime
from cobweb.items import PropertyItem
from cobweb.utilities import extract_number, extract_unit, extract_property_id, strip

class SearchSpider(scrapy.Spider):
    name = 'search_spider'

    def __init__(self, vendor=None, crawl_url=None, max_depth=2, start_index=1, *args, **kwargs):
        super(SearchSpider, self).__init__(*args, **kwargs)
        self.vendor = vendor
        self.crawl_url = crawl_url
        self.index = int(start_index)
        self.max_depth = int(max_depth)
        self.start_urls = [self.vendor + self.crawl_url + "/p" + str(self.index)]

    def parse(self, response):
        if not isinstance(response, scrapy.http.response.html.HtmlResponse): 
            response = scrapy.http.response.html.HtmlResponse(response.url,body=response.body)

        search_results = response.css(u'.search-productItem')        

        for row in search_results:
            item = PropertyItem()
            item["vendor"] = self.vendor
            item["created_date"] = datetime.utcnow()
            item["last_indexed_date"] = datetime.utcnow()
            item["last_crawled_date"] = None

            subdomain = row.css(u'.p-title a::attr(href)').extract()
            if subdomain:
                item["link"] = self.vendor + subdomain[0].strip()

            item["property_id"] = extract_property_id(item["link"])
        
            price = strip(row.css(u'.product-price::text').extract())
            item["property_price_raw"] = price
            item["property_price"] = extract_number(price)
            item["property_price_unit"] = extract_unit(price)

            property_size = strip(row.css(u'.product-area::text').extract())
            item["property_size_raw"] = property_size
            item["property_size"] = extract_number(property_size)
            item["property_size_unit"] = extract_unit(property_size)

            item["property_area"] = strip(row.css(u'.product-city-dist::text').extract())

            item["posted_date"] = strip(row.css(u'.floatright::text').extract())

            yield item
        
        if self.index < self.max_depth and len(search_results) > 0:
            self.index += 1 
            next_url = self.vendor + self.crawl_url + "/p" + str(self.index)
            yield scrapy.Request(next_url, callback=self.parse)
