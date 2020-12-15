import json
import scrapy
from ..items import InstagramPostItem, InstagramTagItem
import datetime

class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    db_type = 'MONGO'
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']

    query_hash = {'tag_paginate': '9b498c08113f1e09617a1703c22b2f32'}

    def __init__(self, login, password, tag_list, *args, **kwargs):
        self.login = login
        self.password = password
        self.tag_list = ['python', 'data_science', 'machine_learning']
        super(InstagramSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        try:
            js_data = self.js_data_extract(response)
            yield scrapy.FormRequest(
                self.login_url,
                method='POST',
                callback=self.parse,
                formdata={
                    'username': self.login,
                    'enc_password': self.password,
                },
                headers={'X-CSRFToken': js_data['config']['csrf_token']}
            )
        except AttributeError:
            if response.json().get('authenticated'):
                for tag in self.tag_list:
                    yield response.follow(f'/explore/tags/{tag}', callback=self.tag_parse)


    def tag_parse(self, response):
        tag = self.js_data_extract(response)['entry_data']['TagPage'][0]['graphql']['hashtag']
        yield InstagramTagItem(date_parse=datetime.datetime.now(),
                data={'tag_id': tag['id'], 'tag_name': tag['name'], 'tag_picture': tag['profile_pic_url']})
        yield from self.get_tag_posts(tag, response)

    def tag_api_parse(self, response):
        yield from self.get_tag_posts(response.json()['data']['hashtag'], response)


    def get_tag_posts(self, tag, response):
        if tag['edge_hashtag_to_media']['page_info']['has_next_page']:
            variables = {
                'tag_name': tag['name'],
                'first': 100,
                'after': tag['edge_hashtag_to_media']['page_info']['end_cursor'],
            }
            yield response.follow(f'/graphql/query/?query_hash={self.query_hash["tag_paginate"]}&variables={json.dumps(variables)}',
                                  callback=self.tag_api_parse)
        yield from self.get_post(tag['edge_hashtag_to_media']['edges'])

    @staticmethod
    def get_post(edges):
        for node in edges:
            yield InstagramPostItem(date_parse=datetime.datetime.now(), data=node['node'])


    def js_data_extract(self, response):
        script = response.xpath('//script[contains(text(), "window._sharedData = ")]/text()').get()
        return json.loads(script.replace("window._sharedData = ", '')[:-1])