# -*- coding: utf-8 -*-
import scrapy
import logging

from datetime import datetime
from cobweb.items import HouseItem
from cobweb.utilities import strip, extract_number, extract_unit, extract_property_id, find_index_containing_substring

log = logging.getLogger('cobweb.scrapy.spiders.RealEstateSpider')


class RealEstateSpiderTBDS(scrapy.Spider):
    name = 'real_estate_spider_tbds'

    def __init__(self, vendor=None, crawl_url=None, type=None, *args, **kwargs):
        super(RealEstateSpiderTBDS, self).__init__(*args, **kwargs)
        self.vendor = vendor
        self.type = type
        for url in crawl_url.split(','):
            log.debug('Crawling urls={}'.format(url))
            self.start_urls.append(url)

    def extract_infor(self, infor, pattern):
        index = find_index_containing_substring(infor, pattern)
        if index > 0:
            return infor[index - 1].strip()

    def parse(self, response):
        if not isinstance(response, scrapy.http.response.html.HtmlResponse): 
            response = scrapy.http.response.html.HtmlResponse(response.url, body=response.body)

        selector = scrapy.Selector(response)

        item = HouseItem()

        #Listing Site Information
        item['vendor'] = self.vendor
        item['link'] = response.url
        item['type'] = self.type
        item['property_id'] = extract_property_id(item["link"])
        item['key'] = item['vendor'] + ":" + item['property_id'] + ":" + item['type']
        item['crawled_date'] = datetime.utcnow()

        posted_date = response.css(u'.list-info.clearfix .value.line::text').extract()
        if len(posted_date) > 2:
            item['posted_date'] = "/".join([line.strip() for line in posted_date[:2]])

        #Property General Information
        item["title"] = strip(response.css(u'.folder-title h1::text').extract())
        description = response.css(u'div[id="infoDetail"]::text').extract()
        if description:
            item["description"] = " ".join([line.strip() for line in description])
        
        price = strip(selector.xpath(u'//span[contains(text(),"Giá")]/following::span[1]//text()').extract())
        item["price_raw"] = price
        item["price"] = extract_number(price)
        item["price_unit"] = extract_unit(price)

        # response.css(u'span[id="MainContent_ctlDetailBox_lblSurface"]::text').extract()
        property_size = strip(selector.xpath(u'//span[contains(text(),"Diện tích")]/following::span[1]//text()').extract())
        item["property_size_raw"] = property_size
        item["property_size"] = extract_number(property_size)
        item["property_size_unit"] = extract_unit(property_size)

        if item["price"] and item["property_size"]:
            item["price_per_sqm"] = item["price"] / item["property_size"]
        else:
            item["price_per_sqm"] = None

        address = strip(response.css(u'.folder-title .pull-left::text').extract()[2])
        if address != "":
            item["address"] = address

        #Property Specifications
        infor = selector.xpath(u'//ul[@class="list-info clearfix"]/li//text()').extract()
        if infor:
            item["road_width"] = self.extract_infor(infor, "Đường vào")
            item["num_floors"] = self.extract_infor(infor, "Số tầng")
            item["num_bedrooms"] = self.extract_infor(infor, "Số phòng")
            item["num_bathrooms"] = self.extract_infor(infor, "Số toilet")
            item["frontage"] = self.extract_infor(infor, "Mặt tiền")
            item["house_orientation"] = self.extract_infor(infor, "Hướng nhà")

        #Media Information
        images = response.css(u'.slide_show img::attr(src)').extract()
        if images:
            item["images"] = images
        else:
            item["images"] = None


        #Seller Information
        item["listing_type"] = self.type
        item["contact_name"] = strip(response.css(u'.info-contact .fweight-bold.dblue-clr::text').extract())
        item["contact_phone"] = strip(response.css(u'.info-contact span[id="toPhone"]::text').extract())
        item["contact_email"] = strip(response.css(u'.info-contact span[id="toEmail"]::text').extract())
        item["contact_address"] = strip(response.css(u'.info-contact span[id="toAddress"]::text').extract())

        yield item

