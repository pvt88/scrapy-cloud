import scrapy

from datetime import datetime
from cobweb.items import PropertyItem
from cobweb.utilities import extract_number, extract_unit, extract_property_id, strip, extract_listing_type


class SearchSpiderMBND(scrapy.Spider):
    name = 'search_spider_mbnd'

    def __init__(self, vendor=None, crawl_url=None, type=None, max_depth=2, start_index=0, *args, **kwargs):
        super(SearchSpiderMBND, self).__init__(*args, **kwargs)
        self.vendor = vendor
        self.crawl_url = crawl_url
        self.index = int(start_index)
        self.type = type
        self.listing_type = extract_listing_type(self.crawl_url)
        self.max_depth = int(max_depth)
        self.start_urls = [self.vendor + self.crawl_url + "?p=" + str(self.index)]

    def parse(self, response):
        if not isinstance(response, scrapy.http.response.html.HtmlResponse): 
            response = scrapy.http.response.html.HtmlResponse(response.url, body=response.body)

        search_results = response.css(u'.resultItem')

        for row in search_results:
            item = PropertyItem()
            item["vendor"] = self.vendor
            item["type"] = self.type
            item["listing_type"] = self.listing_type
            item["created_date"] = datetime.utcnow()
            item["last_indexed_date"] = datetime.utcnow()
            item["last_crawled_date"] = None

            subdomain = row.css(u'.row.title a::attr(href)').extract()
            if subdomain:
                item["link"] = self.vendor + subdomain[0].strip()

            item["property_id"] = extract_property_id(item["link"])

            price = strip(row.css(u'.listing-price::text').extract())
            item["property_price_raw"] = price
            item["property_price"] = extract_number(price)
            item["property_price_unit"] = extract_unit(price)

            #TODO: this one have to check the img icon to determine if it is size or number of rooms
            property_size = row.css(u'.col-xs-12.lline::text').extract()
            if property_size:
                item["property_size_raw"] = property_size[len(property_size)-1].strip()
                item["property_size"] = extract_number(item["property_size_raw"])
                item["property_size_unit"] = extract_unit(item["property_size_raw"])

            property_area = row.css(u'.row.lline .col-xs-6::text').extract()
            item["property_area"] = ', '.join([a.strip() for a in property_area])

            item["posted_date"] = strip(row.css(u'.col-lg-4.lline.hidden-xs::text').extract())

            yield item
        
        if self.index < self.max_depth and len(search_results) > 0:
            self.index += 1 
            next_url = self.vendor + self.crawl_url + "?p=" + str(self.index)
            yield scrapy.Request(next_url, callback=self.parse)
