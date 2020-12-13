import re
from scrapy import Selector
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose
from .items import HhItem

def author_name_in(data: list):
    if len(data) > 1:
        if data[0] != data[1]:
            data = ''.join(data[:2])
        if data[-1] == ' ':
            data = data[:-1]
    return data


class HhLoader(ItemLoader):
    default_item_class = HhItem
    title_out = TakeFirst()
    url_out = TakeFirst()
    salary_in = ''.join
    salary_out = TakeFirst()
    description_in = ''.join
    description_out = TakeFirst()
    skills_in = ', '.join
    skills_out = TakeFirst()
    author_out = TakeFirst()
    author_name_in = author_name_in
    author_name_out = TakeFirst()
    author_url_out = TakeFirst()
    website_out = TakeFirst()
    spheres_in = ', '.join
    spheres_out = TakeFirst()
    info_in = ''.join
    info_out = TakeFirst()
