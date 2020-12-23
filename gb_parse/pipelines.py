# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from itemadapter import ItemAdapter
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline
from pymongo import MongoClient


class GbParsePipeline:
    def __init__(self):
        self.db = MongoClient()['parse_instagram']

    def process_item(self, item, spider):
        collection = self.db[spider.name]
        collection.insert_one(item)
        return item


class GbImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        try:
            for num in range(len(item['data']['thumbnail_resources'])):
                yield Request(item['data']['thumbnail_resources'][num].get('src', []))
        except KeyError:
            yield Request(item['data']['tag_picture'])


    def item_completed(self, results, item, info):
        try:
            item['data']['thumbnail_resources'] = [itm[1] for itm in results]
            return item
        except KeyError:
            item['data']['tag_picture'] = [itm[1] for itm in results]
            return item
        