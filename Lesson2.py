import os
import time
import datetime as dt
import requests
import bs4
import pymongo
import dotenv
from urllib.parse import urljoin

dotenv.load_dotenv('.env')


class MagnitParse:
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0"
    }

    def __init__(self, start_url):
        self.start_url = start_url
        client = pymongo.MongoClient(os.getenv('DATA_BASE'))
        self.db = client['gb_parse']
        self.months_template = {'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6, 'июля': 7,
                                'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12}

        self.product_template = {
            'url': lambda soup: urljoin(self.start_url, soup.get('href')),
            'promo_name': lambda soup: soup.find('div', attrs={'class': 'card-sale__header'}).text,
            'product_name': lambda soup: soup.find('div', attrs={'class': 'card-sale__title'}).text,
            'old_price': lambda soup: float(
                soup.find('div', attrs={'class': 'label__price label__price_old'}).findChild(
                    'span', attrs={'class': 'label__price-integer'}).text + '.' + soup.find('div', attrs={'class':
                    'label__price label__price_old'}).findChild(
                    'span', attrs={'class': 'label__price-decimal'}).text),
            'new_price': lambda soup: float(
                soup.find('div', attrs={'class': 'label__price label__price_new'}).findChild(
                    'span', attrs={'class': 'label__price-integer'}).text + '.' + soup.find('div', attrs={'class':
                     'label__price label__price_new'}).findChild(
                    'span', attrs={'class': 'label__price-decimal'}).text),
            'image_url': lambda soup: urljoin(self.start_url, soup.find('img').get('data-src')),
            "date_from": lambda soup: self.to_datetime(
                soup.find('div', attrs={'class': 'card-sale__date'}).findChild('p').text),
            "date_to": lambda soup: self.to_datetime(
                soup.find('div', attrs={'class': 'card-sale__date'}).findChild('p').find_next_sibling('p').text),
        }

    def to_datetime(self, text):
        day = int(text.split(' ')[1])
        month = self.months_template[text.split(' ')[2]]
        if month > 10:
            return dt.datetime(dt.datetime.now().year, month, day)
        if month < 10:
            return dt.datetime(dt.datetime.now().year + 1, month, day)

    @staticmethod
    def _get(*args, **kwargs):
        while True:
            try:
                response = requests.get(*args, **kwargs)
                if response.status_code != 200:
                    raise Exception
                return response
            except Exception:
                time.sleep(0.5)

    def soup(self, url) -> bs4.BeautifulSoup:
        response = self._get(url, headers=self.headers)
        return bs4.BeautifulSoup(response.text, 'lxml')

    def run(self):
        soup = self.soup(self.start_url)
        for product in self.parse(soup):
            self.save(product)

    def parse(self, soup):
        catalog = soup.find('div', attrs={'class': 'сatalogue__main'})

        for product in catalog.find_all('a', recursive=False):
            pr_data = self.get_product(product)
            yield pr_data

    def get_product(self, product_soup) -> dict:

        result = {}
        for key, value in self.product_template.items():
            try:
                result[key] = value(product_soup)
            except Exception as e:
                continue
        return result

    def save(self, product):
        collection = self.db['magnit']
        collection.insert_one(product)


if __name__ == '__main__':
    parser = MagnitParse('https://magnit.ru/promo/?geo=moskva')
    parser.run()
