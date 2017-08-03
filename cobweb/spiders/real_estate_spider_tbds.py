# -*- coding: utf-8 -*-
import scrapy
import logging

from datetime import datetime
from cobweb.items import HouseItem
from cobweb.utilities import strip, extract_number, extract_unit, extract_property_id

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
        if item['property_id']:
            item['key'] = item['vendor'] + ":" + item['property_id'] + ":" + item['type']
        else:
            item['key'] = item['vendor'] + ":" + "FAILURE" + ":" + item['type']

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

        property_size = strip(selector.xpath(u'//span[contains(text(),"Diện tích")]/following::span[1]//text()').extract())
        item["property_size_raw"] = property_size
        item["property_size"] = extract_number(property_size)
        item["property_size_unit"] = extract_unit(property_size)

        if item["price"] and item["property_size"]:
            item["price_per_sqm"] = item["price"] / item["property_size"]
        else:
            item["price_per_sqm"] = None

        address_infor = response.css(u'.folder-title .pull-left::text').extract()
        if len(address_infor) > 1:
            address = strip(address_infor[2])
            if address != "":
                item["address"] = address

        #Property Specifications
        num_bedrooms = selector.xpath(u'//ul[@class="list-info clearfix"]/li[self::li//text()[contains(.,"S\u1ed1 ph\xf2ng")]]//text()').extract()
        if num_bedrooms and len(num_bedrooms) > 2:
            item["num_bedrooms"] = num_bedrooms[1].strip()

        num_bathrooms = selector.xpath( u'//ul[@class="list-info clearfix"]/li[self::li//text()[contains(.,"S\u1ed1 toilet")]]//text()').extract()
        if num_bathrooms and len(num_bathrooms) > 2:
            item["num_bathrooms"] = num_bathrooms[1].strip()

        num_floors = selector.xpath(
            u'//ul[@class="list-info clearfix"]/li[self::li//text()[contains(.,"S\u1ed1 t\u1ea7ng")]]//text()').extract()
        if num_floors and len(num_floors) > 2:
            item["num_floors"] = num_floors[1].strip()

        distance_to_road = selector.xpath(
                u'//ul[@class="list-info clearfix"]/li[self::li//text()[contains(.,"\u0110\u01b0\u1eddng v\xe0o")]]//text()').extract()
        if distance_to_road and len(distance_to_road) > 2:
                item["distance_to_road"] = distance_to_road[1].strip()

        frontage = selector.xpath(
            u'//ul[@class="list-info clearfix"]/li[self::li//text()[contains(.,"M\u1eb7t ti\u1ec1n")]]//text()').extract()
        if frontage and len(frontage) > 2:
            item["frontage"] = frontage[1].strip()

        house_orientation = selector.xpath(u'//ul[@class="list-info clearfix"]/li[self::li//text()[contains(.,"H\u01b0\u1edbng nh\xe0")]]//text()').extract()
        if house_orientation and len(house_orientation) > 2:
                item["house_orientation"] = house_orientation[1].strip()

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


