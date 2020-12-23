import json
import scrapy
from ..items import InstagramPostItem, InstagramTagItem, InstagramUsersItem, InstagramFollowItem, InstaPathItem
import datetime
from anytree import Node
from collections import deque

class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    db_type = 'MONGO'
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']

    query_hash = {'tag_paginate': '9b498c08113f1e09617a1703c22b2f32',
                  'followers': 'c76146de99bb02f6415203be841dd25a',
                  'following': 'd04b0a864b4b54837c0d870b0e77e076'}
    resp = ''
    flag = False
    tree = {}


    def __init__(self, login, password, user1, user2, *args, **kwargs):
        self.login = login
        self.password = password
        self.tag_list = ['python', 'data_science', 'machine_learning']
        self.user1 = user1
        self.user2 = user2
        self.users_deque = deque()
        self.checked_followers = []
        self.tree[self.user1] = Node(self.user1)
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
                #for user in self.users_list:
                yield response.follow(f'https://www.instagram.com/{self.user1}/', callback=self.user_parse)

    def user_parse(self, response):
        user_data = {'id': self.js_data_extract(response)['entry_data']['ProfilePage'][0]['graphql']['user']['id'],
                     'username': self.js_data_extract(response)['entry_data']['ProfilePage'][0]['graphql']['user']['username'],
                      'followers':[], 'following':[]}
        self.resp = response
        #yield InstagramUsersItem(date_parse=datetime.datetime.now(), user_data=user_data)
        #yield from self.get_following(response, user_data)
        yield from self.get_followers(response, user_data)

    def tag_parse(self, response):
        tag = self.js_data_extract(response)['entry_data']['TagPage'][0]['graphql']['hashtag']
        yield InstagramTagItem(date_parse=datetime.datetime.now(),
               data={'tag_id': tag['id'], 'tag_name': tag['name'], 'tag_picture': tag['profile_pic_url']})
        yield from self.get_tag_posts(tag, response)

    def tag_api_parse(self, response):
        yield from self.get_tag_posts(response.json()['data']['hashtag'], response)


    def get_followers(self, response, user_data):
        try:
            data = response.json()
            self.get_follower_page(response, user_data)
            if data['data']['user']['edge_followed_by']['page_info']['has_next_page']:
                variables = {
                    'id': user_data['id'],
                    'fetch_mutual': True,
                    'first': 100,
                    'after': data['data']['user']['edge_followed_by']['page_info']['end_cursor']}
                yield response.follow(
                    f'/graphql/query/?query_hash={self.query_hash["followers"]}&variables={json.dumps(variables)}',
                    callback=self.get_followers, cb_kwargs={'user_data': user_data})
            else:
                yield from self.get_following(self.resp, user_data)
        except json.decoder.JSONDecodeError:
            variables = {
                'id': user_data['id'],
                'fetch_mutual': True,
                'first': 100
            }
            yield response.follow(
                f'/graphql/query/?query_hash={self.query_hash["followers"]}&variables={json.dumps(variables)}',
                callback=self.get_followers, cb_kwargs={'user_data': user_data})

    def get_follower_page(self, response, user_data):
        followers = response.json()['data']['user']['edge_followed_by']['edges']
        for node in followers:
            user_data['followers'].append({'id': node['node']['id'], 'username': node['node']['username']})



    def get_following(self, response, user_data, variables=None, ):
        try:
            data = response.json()
            self.get_following_page(response, user_data)
            if data['data']['user']['edge_follow']['page_info']['has_next_page']:
                variables = {
                    'id': user_data['id'],
                    'first': 100,
                    'after': data['data']['user']['edge_follow']['page_info']['end_cursor']}
                yield response.follow(
                    f'/graphql/query/?query_hash={self.query_hash["following"]}&variables={json.dumps(variables)}',
                    callback=self.get_following, cb_kwargs={'user_data': user_data})
            else:
                yield from self.get_mutual_users(user_data)
        except json.decoder.JSONDecodeError:
            variables = {
                'id': user_data['id'],
                'first': 100
            }
            yield response.follow(
                f'/graphql/query/?query_hash={self.query_hash["following"]}&variables={json.dumps(variables)}',
                callback=self.get_following, cb_kwargs={'user_data': user_data})


    def get_following_page(self, response, user_data):
        following = response.json()['data']['user']['edge_follow']['edges']
        for node in following:
            user_data['following'].append({'id': node['node']['id'], 'username': node['node']['username']})

    def get_mutual_users(self, user_data):
        mutual_followers = []
        self.checked_followers.append(user_data['username'])
        for el in user_data['followers']:
            if el in user_data['following']:
                self.tree[el['username']] = Node(el['username'], parent=self.tree[user_data['username']])
                if el['username'] == self.user2:
                    print(f'Found path through {self.tree[el["username"]].depth} handshakes. \n '
                          f'The path is:{[node.name for node in self.tree[el["username"]].path]}')
                    self.flag = True
                    break
                if self.tree[el["username"]].depth > 6:
                    print('The 6 handshakes theory did not work out')
                    self.flag = True
                    break
                mutual_followers.append(el['username'])
      #  yield InstaPathItem(parent={'id': user_data['id'], 'username': user_data['username']},
        #                    children=mutual_followers)
        new_mutual_followers = []
        for el in mutual_followers:
            if el not in self.checked_followers:
                new_mutual_followers.append(el)
        self.users_deque.extend(new_mutual_followers)
        if len(self.users_deque) > 0 and not self.flag:
            yield self.resp.follow(f'https://www.instagram.com/{self.users_deque.popleft()}/', callback=self.user_parse)





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