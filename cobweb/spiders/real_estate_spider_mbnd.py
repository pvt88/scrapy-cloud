# -*- coding: utf-8 -*-
import scrapy
import logging

from datetime import datetime
from cobweb.items import HouseItem
from cobweb.utilities import strip, extract_number, extract_unit, extract_property_id

log = logging.getLogger('cobweb.scrapy.spiders.RealEstateSpider')


class RealEstateSpiderMBND(scrapy.Spider):
    SEPARATOR = '/'

    name = 'real_estate_spider_mbnd'

    def __init__(self, vendor=None, crawl_url=None, type=None, *args, **kwargs):
        super(RealEstateSpiderMBND, self).__init__(*args, **kwargs)
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
        item['key'] = item['vendor'] + ":" + item['property_id'] + ":" + item['type']
        item['crawled_date'] = datetime.utcnow()

        item['posted_date'] = strip(response.css(u'span[id="MainContent_ctlDetailBox_lblDateCreated"]::text').extract())

        #Property General Information
        item["title"] = strip(response.css(u'.navi-title::text').extract())
        description = response.css(u'.box-description::text').extract()
        if description:
            item["description"] = " ".join([line.strip() for line in description])
        
        price = strip(response.css(u'span[id="MainContent_ctlDetailBox_lblPrice"]::text').extract())
        item["price_raw"] = price
        item["price"] = extract_number(price)
        item["price_unit"] = extract_unit(price)

        # response.css(u'span[id="MainContent_ctlDetailBox_lblSurface"]::text').extract()
        property_size = strip(selector.xpath(u'//th[contains(text(),"Diện tích")]/following::span[1]//text()').extract())
        item["property_size_raw"] = property_size
        item["property_size"] = extract_number(property_size)
        item["property_size_unit"] = extract_unit(property_size)

        if item["price"] and item["property_size"]:
            item["price_per_sqm"] = item["price"] / item["property_size"]
        else:
            item["price_per_sqm"] = None

        item["ward"] = strip(response.css(u'span[id="MainContent_ctlDetailBox_lblWard"] a::text').extract())
        item["district"] = strip(response.css(u'span[id="MainContent_ctlDetailBox_lblDistrict"] a::text').extract())
        item["city"] = strip(response.css(u'span[id="MainContent_ctlDetailBox_lblCity"] a::text').extract())

        address = strip(response.css(u'span[id="MainContent_ctlDetailBox_lblStreet"]::text').extract())
        if address != "":
            item["address"] = address

        #Property Specifications
        # response.css(u'span[id="MainContent_ctlDetailBox_lblLegalStatus"]::text').extract()
        item["ownership_certificate"] = strip(selector.xpath(u'//th[contains(text(),"Tình trạng pháp lý")]/following::span[1]//text()').extract())
        # response.css(u'span[id="MainContent_ctlDetailBox_lblFrontRoadWidth"]::text').extract()
        item["road_width"] = strip(selector.xpath(u'//th[contains(text(),"Đường trước nhà")]/following::span[1]//text()').extract())
        # MainContent_ctlDetailBox_lblFloor
        item["num_floors"] = extract_number(strip(selector.xpath(u'//th[contains(text(),"Số tầng")]/following::span[1]//text()').extract()))
        # MainContent_ctlDetailBox_lblBedRoom
        item["num_bedrooms"] = extract_number(strip(selector.xpath(u'//th[contains(text(),"Phòng ngủ")]/following::span[1]//text()').extract()))
        # MainContent_ctlDetailBox_lblBathRoom
        item["num_bathrooms"] = extract_number(strip(selector.xpath(u'//th[contains(text(),"Phòng tắm")]/following::span[1]//text()').extract()))
        # MainContent_ctlDetailBox_lblUtility
        item["furniture"] = " " + ','.join(selector.xpath(u'//th[contains(text(),"Tiện ích")]/following::span[1]//text()').extract()).strip()
        #item["frontage"] = extract_number(strip(selector.xpath(u'//div[contains(text(),"M\u1eb7t ti\u1ec1n")]/following::div[1]//text()').extract()))
        # MainContent_ctlDetailBox_lblFengShuiDirection
        item["house_orientation"] = strip(selector.xpath(u'//th[contains(text(),"Hướng")]/following::span[1]//text()').extract())
        #item["balcony_orientation"] = strip(selector.xpath(u'//div[contains(text(),"H\u01b0\u1edbng ban c\xf4ng")]/following::div[1]//text()').extract())
        #item["distance_to_road"] = extract_number(strip(selector.xpath(u'//div[contains(text(),"\u0110\u01b0\u1eddng v\xe0o")]/following::div[1]//text()').extract()))

        #Media Information
        images = selector.xpath(u'//div[@class="flexslider"]//img//@src').extract()
        if images:
            item["images"] = images
        else:
            item["images"] = None
            
        #videos = selector.xpath(u'//div[@id="LeftMainContent__productDetail_ltVideo"]//iframe//@src').extract()
        #if videos:
        #    item["videos"] = videos
        #else:
        #    item["videos"] = None

        #Seller Information
        #TODO: extract this from the url
        item["listing_type"] = self.type
        item["contact_name"] = strip(response.css(u'.name-contact a::text').extract())
        #item["contact_phone"] = strip(selector.xpath(u'//div[contains(text(),"\u0110i\u1ec7n tho\u1ea1i")]/following::div[1]//text()').extract())
        #item["contact_mobile"] = strip(selector.xpath(u'//div[contains(text(),"Mobile")]/following::div[1]//text()').extract())
        contact_address = strip(response.css(u'span[id="MainContent_ctlDetailBox_lblAddressContact"]::text').extract())
        if contact_address != "":
            item["contact_address"] = contact_address
        contact_link = strip(response.css(u'.name-contact a::attr(href)').extract())
        if contact_link:
            item["contact_link"] = self.vendor + "/doanh-nghiep/detail" + contact_link

        #Project Information
        item["project_name"] = strip(response.css(u'span[id="MainContent_ctlDetailBox_lblProject"] a::text').extract())
        #item["project_owner"] = strip(selector.xpath(u'//div[contains(text(),"Ch\u1ee7 \u0111\u1ea7u t\u01b0")]/following::div[1]//text()').extract())
        #item["project_scale"] = strip(selector.xpath(u'//div[contains(text(),"Quy m\xf4")]/following::div[1]//text()').extract())
        item["project_link"] = strip(response.css(u'span[id="MainContent_ctlDetailBox_lblProject"] a::attr(href)').extract())
        
        yield item

