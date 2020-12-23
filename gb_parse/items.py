# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class GbParseItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class AutoYoulaItem(scrapy.Item):
    _id = scrapy.Field()
    title = scrapy.Field()
    images = scrapy.Field()
    description = scrapy.Field()
    url = scrapy.Field()
    autor = scrapy.Field()
    specifications = scrapy.Field()

class InstagramTagItem(scrapy.Item):
    _id = scrapy.Field()
    date_parse = scrapy.Field()
    data = scrapy.Field()


class InstagramPostItem(scrapy.Item):
    _id = scrapy.Field()
    date_parse = scrapy.Field()
    data = scrapy.Field()

class InstagramUsersItem(scrapy.Item):
    _id = scrapy.Field()
    date_parse = scrapy.Field()
    user_data = scrapy.Field()


class InstagramFollowItem(scrapy.Item):
    _id = scrapy.Field()
    date_parse = scrapy.Field()
    user_id = scrapy.Field()
    user_name = scrapy.Field()
    type = scrapy.Field()
    follow_id = scrapy.Field()
    follow_name = scrapy.Field()

class InstaPathItem(scrapy.Item):
    _id = scrapy.Field()
    parent = scrapy.Field()
    children = scrapy.Field()



