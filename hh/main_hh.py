from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from hh.hh_parse.spiders.hh import HhSpider


if __name__ == '__main__':
    crawl_settings = Settings()
    crawl_settings.setmodule('hh_parse.settings')
    crawl_proc = CrawlerProcess(settings=crawl_settings)
    crawl_proc.crawl(HhSpider)
    crawl_proc.start()