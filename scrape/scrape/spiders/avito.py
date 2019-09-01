import scrapy
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import re

query = 'https://www.avito.ru/{}/kvartiry/prodam?q=купить%20квартиру'
region = 'mahachkala'
# region = 'rossiya'

spider_settings = {
    'AUTOTHROTTLE_ENABLED': True,
    # 'AUTOTHROTTLE_START_DELAY': 2.0,
    # 'AUTOTHROTTLE_MAX_DELAY': 10.0,
    'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.5,
    'CONCURRENT_REQUESTS': 300,
    'CONCURRENT_REQUESTS_PER_DOMAIN': 300,
    # 'DOWNLOAD_DELAY': 3.0,
    # 'DOWNLOAD_TIMEOUT': 20,
    # 'ROTATING_PROXY_LIST_PATH': 'proxies.txt',
    # 'USER_AGENTS': [
    #     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
    #     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36',
    #     'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
    # ],
    # 'ROTATING_PROXY_PAGE_RETRY_TIMES': 3,
    # 'DOWNLOADER_MIDDLEWARES': {
    #     'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
    #     'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
    #     'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    #     'scrapy_useragents.downloadermiddlewares.useragents.UserAgentsMiddleware': 700,
    # },
}

HDR = {
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': 1,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
}


def get_number(line):
    return re.search(r'\b\d+\b', line).group(0)


class AvitoSpider(scrapy.Spider):
    name = "avito"
    save_file = 'avito.txt'
    custom_settings = spider_settings

    def start_requests(self):
        url = query.format(region)
        yield scrapy.Request(url=url, headers=HDR, callback=self.parse_page)

    def parse_page(self, response):
        soup = BeautifulSoup(response.text, 'lxml')
        flats = soup.find(class_='js-catalog_serp')
        for link in flats.find_all('a'):
            href = link.get('href')
            if href and '/kvartiry/' in href:
                yield response.follow(href, headers=HDR, callback=self.parse_item)

        pages = soup.find(class_='pagination-page pagination-page_current')
        for link in pages.find_all('a'):
            href = link.get('href')
            if href and '?p=' in href:
                yield response.follow(href, headers=HDR, callback=self.parse_page)

    def parse_item(self, response):
        with open(self.save_file, 'a+', encoding='utf8') as file:
            soup = BeautifulSoup(response.text, 'lxml')

            price = soup.find(class_='js-item-price', attrs={'itemprop': 'price'})
            price = price.get('content')

            ads_id = soup.find(attrs={'data-marker': 'item-view/item-id'})
            ads_id = ads_id.get_text()
            ads_id = get_number(ads_id)

            views_count = soup.find(class_='title-info-metadata-item title-info-metadata-views')
            views_count = views_count.get_text()
            views_count = get_number(views_count)

            res = [price, ads_id, views_count, response.url]
            file.write('\t'.join(res) + '\n')


def read_lines(filename):
    with open(filename, encoding='utf-8') as file:
        lines = []
        for line in file.readlines():
            line = line.strip()
            if line:
                lines.append(line)

        return lines


def save_unique_lines(filename):
    lines = read_lines(filename)
    lines = list(set(lines))
    with open(filename, 'w', encoding='utf-8') as file:
        for line in lines:
            file.write('{}\n'.format(line))


if __name__ == '__main__':
    process = CrawlerProcess()
    # process = CrawlerProcess(get_project_settings())
    process.crawl(AvitoSpider)
    process.start()
