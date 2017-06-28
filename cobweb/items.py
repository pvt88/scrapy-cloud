# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
#       http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class IPItem(Item):
    status = Field()
    date = Field()
    lat = Field()
    lon = Field()
    timezone = Field()
    org = Field()

class PropertyItem(Item):
	vendor = Field()
	created_date = Field()
	last_crawled_date = Field()
	last_indexed_date = Field()
	property_id = Field()
	link = Field()
	property_size = Field()
	property_size_unit = Field()
	property_price = Field()
	property_price_unit = Field()
	property_area = Field()
	posted_date = Field()

class HouseItem(Item):
	vendor = Field()
	link = Field()
	crawled_date = Field()
	posted_date = Field()
	expire_date = Field()
	title = Field()
	description = Field()
	address = Field()
	area = Field()
	price = Field()
	price_unit = Field()
	price_per_sqm = Field()
	property_size = Field()
	property_size_unit = Field()
	distance_to_road = Field()
	frontage = Field()
	num_floors = Field()
	num_bedrooms = Field()
	num_bathrooms = Field()
	house_orientation = Field()
	balcony_orientation = Field()
	furniture = Field()
	images = Field()
	videos = Field()
	listing_type = Field()
	contact_name = Field()
	contact_address = Field()
	contact_phone = Field()
	contact_mobile = Field()
	project_name = Field()
	project_owner = Field()
	project_scale = Field()
	project_link = Field()
