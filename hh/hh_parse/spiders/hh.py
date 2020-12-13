import scrapy
from ..loaders import HhLoader

class HhSpider(scrapy.Spider):
    name = 'hh'
    db_type = 'MONGO'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']

    xpath_query = {
        'pagination': '//a[@class="bloko-button HH-Pager-Control"]',
        'vacancies': '//a[@data-qa="vacancy-serp__vacancy-title"]'
    }

    vacancy_data = {
            'title': '//h1[@data-qa="vacancy-title"]//text()',
            'salary': '//p[@class="vacancy-salary"]//text()',
            'description': '//div[@data-qa="vacancy-description"]//text()',
            'skills': '//span[@data-qa="bloko-tag__text"]//text()',
            'author': '//a[@data-qa="vacancy-company-name"]//@href',
        }

    author_data = {
        'author_name': '//span[@data-qa="company-header-title-name"]//text()',
        'website': '//a[@data-qa="sidebar-company-site"]//@href',
        'spheres': '//div[@class="company-vacancies-group__title"]//text()',
        'info': '//div[@data-qa="company-description-text"]//text()',
    }

    #  def __init__(self, *args, **kwargs):
   #     super().__init__(*args, **kwargs)
    #    self.db = pymongo.MongoClient()['parse_hh'][self.name]


    def parse(self, response):
        for pag_page in response.xpath(self.xpath_query['pagination']):
            yield response.follow(pag_page.attrib.get('href'), callback=self.parse)

        for vacancy_page in response.xpath(self.xpath_query['vacancies']):
            yield response.follow(vacancy_page.attrib.get('href'), callback=self.vacancy_parse)

    def vacancy_parse(self, response):
        loader = HhLoader(response=response)
        loader.add_value('url', response.url)
        for name, selector in self.vacancy_data.items():
            loader.add_xpath(name, selector)

        yield loader.load_item()
        yield response.follow(response.xpath(self.vacancy_data['author']).get(), callback=self.author_parse)

    def author_parse(self, response):
        loader = HhLoader(response=response)
        loader.add_value('author_url', response.url)
        for name, selector in self.author_data.items():
            loader.add_xpath(name, selector)

        yield loader.load_item()
        yield response.follow(response.xpath('//a[@data-qa="employer-page__employer-vacancies-link"]//@href').get(),
                              callback=self.parse)
