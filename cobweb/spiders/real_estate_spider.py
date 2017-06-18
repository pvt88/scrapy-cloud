import httplib
import scrapy

from datetime import datetime
from cobweb.items import HouseItem
from cobweb.utilities import strip, extract_number, extract_unit

class RealEstateSpider(scrapy.Spider):
    SEPARATOR = '/'

    name = 'real_estate_spider'

    def __init__(self, vendor=None, crawl_url=None, *args, **kwargs):
        super(RealEstateSpider, self).__init__(*args, **kwargs)
        self.vendor = vendor
        sub_domains = [s for s in crawl_url.split(self.SEPARATOR) if s]
        self.area_subdomain = sub_domains[0]
        self.property_subdomain = sub_domains[1]
        self.start_urls = [self.vendor + self.SEPARATOR + self.area_subdomain + self.SEPARATOR + self.property_subdomain]

    def parse(self, response):
        #check if response it not a HtmlResponse already
        if not isinstance(response, scrapy.http.response.html.HtmlResponse): 
            response = scrapy.http.response.html.HtmlResponse(response.url,body=response.body)

        selector = scrapy.Selector(response)

        item = HouseItem()

        #Listing Site Information
        item['vendor'] = self.vendor
        item["link"] = response.url
        item['crawled_date'] = datetime.utcnow()
        item["posted_date"] = response.css('.prd-more-info div::text').extract()[2].strip()
        item["expire_date"] = response.css('.prd-more-info div::text').extract()[3].strip()

        #Property General Information
        item["title"] = response.css('.pm-title h1::text').extract()[0].strip()
        item["description"] = " ".join([str.strip() for str in response.css('.pm-content .pm-desc::text').extract()])
        
        price = response.css('.kqchitiet .gia-title strong::text').extract()[0].strip()
        item["price"] = extract_number(price)
        item["price_unit"] = extract_unit(price)

        property_size = response.css('.kqchitiet .gia-title strong::text').extract()[1].strip()
        item["property_size"] = extract_number(property_size)
        item["property_size_unit"] = extract_unit(property_size)

        #TODO: There might be more correct information about the size in the description
        item["price_per_sqm"] = item["price"] / item["property_size"] 

        item["area"] = strip(selector.xpath(u'//span[@class="diadiem-title mar-right-15"]//a/@href').extract())
        addresses = selector.xpath(u'//div[contains(text(),"\u0110\u1ecba ch\u1ec9")]/following::div[1]//text()').extract()
        if addresses:
            item["address"] = addresses[0].strip()
        
        #Property Specifications
        item["num_floors"] = extract_number(strip(selector.xpath(u'//div[contains(text(),"S\u1ed1 t\u1ea7ng")]/following::div[1]//text()').extract()))
        item["num_bedrooms"] = extract_number(strip(selector.xpath(u'//div[contains(text(),"S\u1ed1 ph\xf2ng ng\u1ee7")]/following::div[1]//text()').extract()))
        item["num_bathrooms"] = extract_number(strip(selector.xpath(u'//div[contains(text(),"S\u1ed1 toilet")]/following::div[1]//text()').extract()))
        item["furniture"] = strip(selector.xpath(u'//div[contains(text(),"N\u1ed9i th\u1ea5t\r\n")]/following::div[1]//text()').extract())
        item["frontage"] = extract_number(strip(selector.xpath(u'//div[contains(text(),"M\u1eb7t ti\u1ec1n")]/following::div[1]//text()').extract()))
        item["house_orientation"] = strip(selector.xpath(u'//div[contains(text(),"\nH\u01b0\u1edbng nh\xe0")]/following::div[1]//text()').extract())
        item["balcony_orientation"] = strip(selector.xpath(u'//div[contains(text(),"H\u01b0\u1edbng ban c\xf4ng")]/following::div[1]//text()').extract())
        item["distance_to_road"] = extract_number(strip(selector.xpath(u'//div[contains(text(),"\u0110\u01b0\u1eddng v\xe0o")]/following::div[1]//text()').extract()))

        #Media Information
        images = selector.xpath(u'//div[@class="list-img"]//img//@src').extract()
        if images:
            item["images"] = images    
            
        videos = selector.xpath(u'//div[@id="LeftMainContent__productDetail_ltVideo"]//iframe//@src').extract()
        if videos:
            item["videos"] = videos 

        #Seller Information
        item["listing_type"] = strip(selector.xpath(u'//div[contains(text(),"Lo\u1ea1i tin rao")]/following::div[1]//text()').extract())
        item["contact_name"] = strip(selector.xpath(u'//div[contains(text(),"T\xean li\xean l\u1ea1c")]/following::div[1]//text()').extract())
        item["contact_phone"] = strip(selector.xpath(u'//div[contains(text(),"\u0110i\u1ec7n tho\u1ea1i")]/following::div[1]//text()').extract())
        item["contact_mobile"] = strip(selector.xpath(u'//div[contains(text(),"Mobile")]/following::div[1]//text()').extract())
        if len(addresses) == 2:
            item["contact_address"] = addresses[1].strip()

        #Project Information
        item["project_name"] = strip(selector.xpath(u'//div[contains(text(),"T\xean d\u1ef1 \xe1n")]/following::div[1]//text()').extract())
        item["project_owner"] = strip(selector.xpath(u'//div[contains(text(),"Ch\u1ee7 \u0111\u1ea7u t\u01b0")]/following::div[1]//text()').extract())
        item["project_scale"] = strip(selector.xpath(u'//div[contains(text(),"Quy m\xf4")]/following::div[1]//text()').extract())
        item["project_link"] = strip(selector.xpath(u'//a[@id="LeftMainContent__productDetail_linkProject"]/@href').extract())
        
        yield item

