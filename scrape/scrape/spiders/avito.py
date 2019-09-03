import scrapy
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import re
from furl import furl
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "property.settings")
django.setup()

from flats.models import *

query = 'https://www.avito.ru/{}/kvartiry/prodam?p={}&view=gallery'
region = 'mahachkala'
# region = 'rossiya'


spider_settings = {
    'AUTOTHROTTLE_ENABLED': True,
    'AUTOTHROTTLE_START_DELAY': 2.0,
    # 'AUTOTHROTTLE_MAX_DELAY': 10.0,
    'AUTOTHROTTLE_TARGET_CONCURRENCY': 3.0,
    'CONCURRENT_REQUESTS': 300,
    'CONCURRENT_REQUESTS_PER_DOMAIN': 300,
    'DOWNLOAD_DELAY': 1.5,
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
    #
    # },
    'COOKIES_ENABLED': True,
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
    return re.search(r"[-+]?\d*\.\d+|\d+", line).group(0)


class AvitoSpider(scrapy.Spider):
    name = "avito"
    save_file = 'avito.txt'
    custom_settings = spider_settings

    def start_requests(self):
        url = query.format(region, 1)
        yield scrapy.Request(url=url, headers=HDR, callback=self.handle_last)

    def handle_last(self, response):
        soup = BeautifulSoup(response.text, 'lxml')
        pages = soup.find(class_='pagination-pages clearfix')
        link = pages.find_all('a')[-1]
        href = link.get('href')
        f = furl(href)
        last_page = f.args['p']
        yield scrapy.Request(
            url=query.format(region, last_page),
            headers=HDR,
            meta={'dont_redirect': True, "handle_httpstatus_list": [302]},
            callback=self.parse_page
        )

    def parse_page(self, response):
        # if response.url == 'https://www.avito.ru/blocked':
        if response.status == 302:
            print('BLOCKED')
            return scrapy.Request(url=response.url, headers=HDR, callback=self.parse_page)

        soup = BeautifulSoup(response.text, 'lxml')
        flats = soup.find(class_='js-catalog_serp')
        for link in flats.find_all('a'):
            href = link.get('href')
            if href and '/kvartiry/' in href:
                yield response.follow(
                    href,
                    headers=HDR,
                    meta={'dont_redirect': True, "handle_httpstatus_list": [302]},
                    callback=self.parse_item
                )

        pages = soup.find(class_='pagination-pages clearfix')
        for link in pages.find_all('a'):
            href = link.get('href')
            if href and '?p=' in href:
                yield response.follow(
                    href,
                    headers=HDR,
                    meta={'dont_redirect': True, "handle_httpstatus_list": [302]},
                    callback=self.parse_page
                )

    def parse_item(self, response):
        if response.status == 302:
            print('BLOCKED')
            return scrapy.Request(url=response.url, headers=HDR, callback=self.parse_item)

        soup = BeautifulSoup(response.text, 'lxml')

        price = soup.find(class_='js-item-price', attrs={'itemprop': 'price'})
        price = price.get('content')

        ads_id = soup.find(attrs={'data-marker': 'item-view/item-id'})
        ads_id = ads_id.get_text()
        ads_id = get_number(ads_id)

        views_count = soup.find(class_='title-info-metadata-item title-info-metadata-views')
        views_count = views_count.get_text()
        views_count = get_number(views_count)

        params = soup.find(class_='item-params-list')
        params = params.find_all(class_='item-params-list-item')
        params = [param.get_text() for param in params]

        flat_fields = {}

        for item in params:
            name, value = item.split(':')
            name = name.strip().lower()
            if name == 'тип дома':
                flat_fields['building_type'] = value
            if name == 'этажей в доме':
                flat_fields['floors_amount'] = get_number(value)
            if name == 'этаж':
                flat_fields['floor'] = get_number(value)
            if name == 'количество комнат':
                try:
                    value = str(get_number(value))
                except AttributeError:
                    pass
                finally:
                    flat_fields['rooms'] = value
            if name == 'общая площадь':
                flat_fields['square'] = get_number(value)
            if name == 'жилая площадь':
                flat_fields['living_square'] = get_number(value)
            if name == 'площадь кухни':
                flat_fields['kitchen_square'] = get_number(value)
            if name == 'срок сдачи':
                flat_fields['finish_date'] = value
            if name == 'отделка':
                flat_fields['decoration'] = value
        flat_fields['views_count'] = views_count
        flat_fields['price'] = price
        flat_fields['url'] = response.url

        flat, created = Flat.objects.update_or_create(
            flat_id=ads_id,
            defaults=flat_fields
        )


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
