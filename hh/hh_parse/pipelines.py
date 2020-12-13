# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient
from urllib.parse import urljoin

class HhParsePipeline:
    def __init__(self):
        self.db = MongoClient()['parse_hh']

    def process_item(self, item, spider):
        collection = self.db['hh']
        try:
            item['author'] = urljoin('https://hh.ru', item['author'])
        except KeyError:
            pass
        finally:
            collection.insert_one(item)
        return item
