from typing import Tuple, Set
import bs4
import requests
from urllib.parse import urljoin
from database import GBDataBase
import time
import datetime as dt


class GbBlogParse:
    _headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0",
    }

    def __init__(self, start_url):
        self.start_url = start_url
        self.page_done = set()
        self.db = GBDataBase('sqlite:///gb_blog.db')

    def _get(self, url):
        while True:
            try:
                response = requests.get(url)
                if response.status_code != 200:
                    raise Exception
                self.page_done.add(url)
                return bs4.BeautifulSoup(response.text, 'lxml')
            except Exception:
                time.sleep(0.5)

    def get_comments(self, url):
        while True:
            try:
                response = requests.get(url, headers=self._headers)
                if (response.status_code != 200) and (response.status_code != 206):
                    raise Exception
                return response.json()
            except Exception:
                time.sleep(0.5)


    def run(self, url=None):
        if not url:
            url = self.start_url

        if url not in self.page_done:
            soup = self._get(url)
            posts, pagination = self.parse(soup)
            for post_url in posts:
                page_data = self.page_parse(self._get(post_url), post_url)
                self.save(page_data)

            for pag_url in pagination:
                self.run(pag_url)

    def parse(self, soup) -> Tuple[Set[str], Set[str]]:
        pag_ul = soup.find('ul', attrs={'class': 'gb__pagination'})
        paginations = set(
            urljoin(self.start_url, p_url.get('href')) for p_url in pag_ul.find_all('a') if p_url.get('href')
        )
        posts_wrapper = soup.find('div', attrs={'class': 'post-items-wrapper'})

        posts = set(
            urljoin(self.start_url, post_url.get('href')) for post_url in
            posts_wrapper.find_all('a', attrs={'class': 'post-item__title'})
        )

        return posts, paginations

    def page_parse(self, soup, url) -> dict:
        template= {
            'url': url,
            'title': soup.find('h1', attrs={'class': 'blogpost-title'}).text,
            'writer': {
                'name': soup.find('div', attrs={'itemprop': 'author'}).text,
                'url': urljoin(self.start_url, soup.find('div', attrs={'itemprop': 'author'}).parent.get('href'))
            },
            'image': soup.find('img').get('src'),
            'date': dt.datetime.strptime(soup.find('time').get('datetime'), '%Y-%m-%dT%H:%M:%S%z'),
            'tags': [],
            'comments': []
        }
        keywords = soup.find('i', attrs={'class': 'i i-tag m-r-xs text-muted text-xs'})
        if keywords:
            keywords = keywords.get('keywords').split(',')
            for el in keywords:
                template['tags'].append({'url': f'{self.start_url}?tag={el}', 'name': el})

        comments_url = f'https://geekbrains.ru/api/v2/comments?commentable_type=Post&commentable_id={soup.find("comments").get("commentable-id")}&order=desc'
        comments = self.get_comments(comments_url)

        def split_comments(comments):
            for comment in comments:
                template['comments'].append({
                    'author_name': comment['comment']['user']['full_name'],
                    'author_url': comment['comment']['user']['url'],
                    'text': comment['comment']['body']})
                if len(comment['comment']['children']) > 0:
                    split_comments(comment['comment']['children'])

        if comments:
            split_comments(comments)

        return template



    def save(self, post_data: dict):
        self.db.create_post(post_data)


if __name__ == '__main__':
    parser = GbBlogParse('https://geekbrains.ru/posts')
    parser.run()