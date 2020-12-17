import json
import scrapy
from ..items import InstagramPostItem, InstagramTagItem, InstagramUsersItem, InstagramFollowItem
import datetime

class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    db_type = 'MONGO'
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']

    query_hash = {'tag_paginate': '9b498c08113f1e09617a1703c22b2f32',
                  'followers': 'c76146de99bb02f6415203be841dd25a',
                  'following': 'd04b0a864b4b54837c0d870b0e77e076'}

    def __init__(self, login, password, *args, **kwargs):
        self.login = login
        self.password = password
        self.tag_list = ['python', 'data_science', 'machine_learning']
        self.users_list = ['geekbrains.ru', 'jetbrains']
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
                #for tag in self.tag_list:
                 #  yield response.follow(f'/explore/tags/{tag}', callback=self.tag_parse)
                for user in self.users_list:
                    yield response.follow(f'https://www.instagram.com/{user}/', callback=self.user_parse)

    def user_parse(self, response):
        user_data = self.js_data_extract(response)['entry_data']['ProfilePage'][0]['graphql']['user']
        yield InstagramUsersItem(date_parse=datetime.datetime.now(), user_data=user_data)
        yield from self.get_following(response, user_data)
        yield from self.get_followers(response, user_data)

    def tag_parse(self, response):
        tag = self.js_data_extract(response)['entry_data']['TagPage'][0]['graphql']['hashtag']
        yield InstagramTagItem(date_parse=datetime.datetime.now(),
               data={'tag_id': tag['id'], 'tag_name': tag['name'], 'tag_picture': tag['profile_pic_url']})
        yield from self.get_tag_posts(tag, response)

    def tag_api_parse(self, response):
        yield from self.get_tag_posts(response.json()['data']['hashtag'], response)


    def get_followers(self, response, user_data, variables=None,):
        try:
            data = response.json()
            if data['data']['user']['edge_followed_by']['page_info']['has_next_page']:
                variables = {
                    'id': user_data['id'],
                    'first': 100,
                    'end_cursor': data['data']['user']['edge_followed_by']['page_info']['end_cursor']}
                yield response.follow(
                    f'/graphql/query/?query_hash={self.query_hash["followers"]}&variables={json.dumps(variables)}',
                    callback=self.get_followers, cb_kwargs={'user_data': user_data})
            yield from self.get_follower_page(response, user_data)
        except json.decoder.JSONDecodeError:
            variables = {
                'id': user_data['id'],
                'first': 100
            }
            yield response.follow(
                f'/graphql/query/?query_hash={self.query_hash["followers"]}&variables={json.dumps(variables)}',
                callback=self.get_followers, cb_kwargs={'user_data': user_data})

    @staticmethod
    def get_follower_page(response, user_data):
        followers = response.json()['data']['user']['edge_followed_by']['edges']
        for node in followers:
            yield InstagramUsersItem(date_parse=datetime.datetime.now(), user_data=node['node'])
            yield InstagramFollowItem(
                date_parse=datetime.datetime.now(),
                user_id=user_data['id'],
                user_name=user_data['username'],
                type='follower',
                follow_id=node['node']['id'],
                follow_name=node['node']['username'])


    def get_following(self, response, user_data, variables=None, ):
        try:
            data = response.json()
            if data['data']['user']['edge_follow']['page_info']['has_next_page']:
                variables = {
                    'id': user_data['id'],
                    'first': 100,
                    'end_cursor': data['data']['user']['edge_follow']['page_info']['end_cursor']}
                yield response.follow(
                    f'/graphql/query/?query_hash={self.query_hash["following"]}&variables={json.dumps(variables)}',
                    callback=self.get_following, cb_kwargs={'user_data': user_data})
            yield from self.get_following_page(response, user_data)
        except json.decoder.JSONDecodeError:
            variables = {
                'id': user_data['id'],
                'first': 100
            }
            yield response.follow(
                f'/graphql/query/?query_hash={self.query_hash["following"]}&variables={json.dumps(variables)}',
                callback=self.get_following, cb_kwargs={'user_data': user_data})

    @staticmethod
    def get_following_page(response, user_data):
        following = response.json()['data']['user']['edge_follow']['edges']
        for node in following:
            yield InstagramUsersItem(date_parse=datetime.datetime.now(), user_data=node['node'])
            yield InstagramFollowItem(
                date_parse=datetime.datetime.now(),
                user_id=user_data['id'],
                user_name=user_data['username'],
                type='following',
                follow_id=node['node']['id'],
                follow_name=node['node']['username'])


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