import scrapy

from datetime import datetime
from cobweb.items import PropertyItem
from cobweb.utilities import extract_number, extract_unit, extract_property_id, strip, extract_listing_type


class SearchSpiderTBDS(scrapy.Spider):
    name = 'search_spider_tbds'

    def __init__(self, vendor=None, crawl_url=None, type=None, max_depth=2, start_index=1, *args, **kwargs):
        super(SearchSpiderTBDS, self).__init__(*args, **kwargs)
        self.vendor = vendor
        self.crawl_url = crawl_url
        self.index = int(start_index)
        self.type = type
        self.listing_type = extract_listing_type(self.crawl_url)
        self.max_depth = int(max_depth)
        self.start_urls = [self.vendor + self.crawl_url + "/p" + str(self.index)]

    def parse(self, response):
        if not isinstance(response, scrapy.http.response.html.HtmlResponse): 
            response = scrapy.http.response.html.HtmlResponse(response.url, body=response.body)

        search_results = response.css(u'.col-gr-75per .group-prd li')

        for row in search_results:
            item = PropertyItem()
            item["vendor"] = self.vendor
            item["type"] = self.type
            item["listing_type"] = self.listing_type
            item["created_date"] = datetime.utcnow()
            item["last_indexed_date"] = datetime.utcnow()
            item["last_crawled_date"] = None

            subdomain = row.css(u'.content .title a::attr(href)').extract()
            if subdomain:
                item["link"] = self.vendor + subdomain[0].strip()

            item["property_id"] = extract_property_id(item["link"])

            info = row.css(u'.content .info span::text').extract()
            if len(info) > 0:
                price = info[0].strip()
                item["property_price_raw"] = price
                item["property_price"] = extract_number(price)
                item["property_price_unit"] = extract_unit(price)

            if len(info) > 1:
                property_size = info[1].strip()
                item["property_size_raw"] = property_size
                item["property_size"] = extract_number(property_size)
                item["property_size_unit"] = extract_unit(property_size)

            property_area = row.css(u'.content .fsize-13::text').extract()
            if len(property_area) > 1:
                item["property_area"] = property_area[1].strip()

            item["posted_date"] = None
            yield item
        
        if self.index < self.max_depth and len(search_results) > 0:
            self.index += 1 
            next_url = self.vendor + self.crawl_url + "/p" + str(self.index)
            yield scrapy.Request(next_url, callback=self.parse)
