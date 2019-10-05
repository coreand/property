import scrapy
from bs4 import BeautifulSoup
from scrapy.crawler import CrawlerProcess
import re
from furl import furl
import os
import django
from urllib.request import Request, urlopen
import aiohttp
import asyncio
from fake_useragent import UserAgent
from requests_html import HTMLSession
from rotating_proxies.policy import BanDetectionPolicy
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q
import math

from scrape.scrape.moscow_stations import msc_stations, spb_stations

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "property.settings")
django.setup()

from flats.models import Flat

query = 'https://www.avito.ru/{city}/kvartiry/prodam?p={page}&view=gallery&{param}={district}'


class City:

    def __init__(self, name, param, districts) -> None:
        self.name = name
        self.districts = districts
        self.param = param


mah = City('mahachkala', 'district', ['383', '384', '385'])
moscow = City('moskva', 'metro', msc_stations)
sankt_peterburg = City('sankt-peterburg', 'metro', spb_stations)

cities = [mah, moscow, sankt_peterburg]


def reset_date_scraped():
    all_flats = Flat.objects.all()
    for flat in all_flats:
        flat.scraped_date = datetime.now() - timedelta(days=2)
        flat.save()


def get_avg_price(**kwargs):
    district = kwargs.pop('district1', None)
    square = kwargs.pop('square', None)
    q = Q()
    if district:
        q = Q(district1=district) | Q(district2=district) | Q(district3=district)
    if square is not None:
        if square[0] == '':
            square[0] = 0
        if square[1] == '':
            square[1] = math.inf
    if square:
        filtered_flats = Flat.objects.filter(q, **kwargs, square__range=square)
    else:
        filtered_flats = Flat.objects.filter(q, **kwargs)

    total_price = 0
    for flat in filtered_flats:
        total_price += flat.price
    try:
        avg_price = total_price / len(filtered_flats)
        info = [int(avg_price), int(len(filtered_flats))]
    except ZeroDivisionError:
        return ['0', '0']
    else:
        return info


class MyPolicy(BanDetectionPolicy):
    def response_is_ban(self, request, response):
        # use default rules, but also consider HTTP 200 responses
        # a ban if there is 'captcha' word in response body.
        ban = super(MyPolicy, self).response_is_ban(request, response)
        ban = ban or response.status == 302
        return ban

    def exception_is_ban(self, request, exception):
        # override method completely: don't take exceptions in account
        return None


spider_settings = {
    'AUTOTHROTTLE_ENABLED': True,
    # 'AUTOTHROTTLE_START_DELAY': 2.0,
    # 'AUTOTHROTTLE_MAX_DELAY': 10.0,
    'AUTOTHROTTLE_TARGET_CONCURRENCY': 1,
    'CONCURRENT_REQUESTS': 10,
    'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
    'DOWNLOAD_DELAY': 4,
    # 'DOWNLOAD_TIMEOUT': 20,

    # 'USER_AGENTS': [
    #     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
    #     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36',
    #     'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
    # ],
    'ROTATING_PROXY_LIST_PATH': 'proxies.txt',
    'ROTATING_PROXY_PAGE_RETRY_TIMES': 3,
    'DOWNLOADER_MIDDLEWARES': {
        'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
        'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
        # 'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
        # 'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 700,

    },
    # 'COOKIES_ENABLED': True,
    # 'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter',
    # 'ROTATING_PROXY_BAN_POLICY': 'scrape.scrape.spiders.MyBanPolicy',

}

HDR = {
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': 1,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
}


def parse_proxy():
    session = HTMLSession()
    url = 'https://free-proxy-list.net/'
    r = session.get(url)
    # r.html.render(retries=2, wait=4.0, scrolldown=2, sleep=4.0, reload=False, )
    r.html.render()
    soup = BeautifulSoup(r.html.html, 'lxml')
    soup = soup.find(class_='table table-striped table-bordered dataTable')
    soup = soup.find('tbody')
    proxies = []
    for line in soup.find_all('tr'):
        values = line.find_all('td')
        values = [value.get_text() for value in values]
        ip, port = values[:2]
        proxies.append(f'{ip}:{port}')
    return proxies


def get_proxies():
    ua = UserAgent()  # From here we generate a random user agent
    proxies = []  # Will contain proxies [ip, port]

    # Retrieve latest proxies
    proxies_req = Request('https://www.sslproxies.org/')
    proxies_req.add_header('User-Agent', ua.random)
    proxies_doc = urlopen(proxies_req).read().decode('utf8')

    soup = BeautifulSoup(proxies_doc, 'html.parser')
    proxies_table = soup.find(id='proxylisttable')

    # Save proxies in the array
    for row in proxies_table.tbody.find_all('tr'):
        proxies.append({
            'ip': row.find_all('td')[0].string,
            'port': row.find_all('td')[1].string
        })

    proxies = ['{}:{}'.format(proxy['ip'], proxy['port']) for proxy in proxies]
    return proxies


async def check_proxy(proxies):
    url = 'https://httpbin.org/ip'

    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[asyncio.create_task(fetch(session, url, proxy))
                                         for proxy in proxies])
        results = [result for result in results if result]

    with open('proxies.txt', 'w+', encoding='utf8') as file:
        file.write('\n'.join(results))


def check_real_proxy():
    # proxies1 = parse_proxy()
    proxies1 = []
    proxies2 = get_proxies()
    proxies1.extend(proxies2)

    asyncio.run(check_proxy(proxies1))


async def fetch(session, url, proxy):
    try:
        async with session.get(url, proxy="http://" + proxy, timeout=4) as response:
            await response.text()
    except:
        return ''
    else:
        return proxy


def get_number(line):
    return re.search(r"[-+]?\d*\.\d+|\d+", line).group(0)


class AvitoSpider(scrapy.Spider):
    name = "avito"
    save_file = 'avito.txt'
    custom_settings = spider_settings

    def response_is_ban(self, request, response):
        return response.status in [302, 403]

    def exception_is_ban(self, request, exception):
        return None

    def start_requests(self):
        for city in cities:
            for district in city.districts:
                url = query.format(city=city.name, page=1, district=district, param=city.param)
                yield scrapy.Request(
                    url=url,
                    headers=HDR,
                    callback=self.handle_last,
                    meta={'city': city, 'district': district}
                )

    first_page = 1

    def handle_last(self, response):
        soup = BeautifulSoup(response.text, 'lxml')
        pages = soup.find(class_='pagination-pages clearfix')
        try:
            link = pages.find_all('a')[-1]
        except AttributeError:
            with open(f"first.html", 'w+', encoding='utf8') as file:
                file.write(response.text)
            print('BLOCKED')
            return
        href = link.get('href')
        f = furl(href)
        last_page = int(f.args['p'])
        for page in range(self.first_page, last_page + 1):
            yield scrapy.Request(
                url=query.format(
                    city=response.meta['city'].name,
                    page=page,
                    district=response.meta['district'],
                    param=response.meta['city'].param
                ),
                dont_filter=True,
                headers=HDR,
                callback=self.parse_page,
                meta={'page': page, 'region': response.meta['city'].name}
            )

    def parse_page(self, response):
        # if response.url == 'https://www.avito.ru/blocked':
        #     raise ConnectionError('BLOCKED')

        soup = BeautifulSoup(response.text, 'lxml')
        flats = soup.find(class_='js-catalog_serp')
        if flats is None:
            with open(f"{response.meta['page']}.html", 'w+', encoding='utf8') as file:
                file.write(response.text)
            print('BLOCKED')
            return

        for link in flats.find_all(class_='description-title-link js-item-link'):
            href = link.get('href')
            if href and '/kvartiry/' in href:
                flat_id = furl(href).path.segments[-1].split('_')[-1]
                flat = Flat.objects.filter(flat_id=flat_id)
                if flat.exists():
                    scraped_date = flat[0].scraped_date
                    date_now = datetime.now()
                    time_dif = date_now - scraped_date
                    twenty_four_hours = timedelta(days=2, hours=0, minutes=0, seconds=0)
                    if time_dif > twenty_four_hours:
                        yield response.follow(
                            href,
                            headers=HDR,
                            callback=self.parse_item,
                            meta=response.meta
                        )
                else:
                    yield response.follow(
                        href,
                        headers=HDR,
                        callback=self.parse_item,
                        meta=response.meta

                    )

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'lxml')
        ads_id = soup.find(attrs={'data-marker': 'item-view/item-id'})
        ads_id = ads_id.get_text()
        ads_id = get_number(ads_id)

        price = soup.find(class_='js-item-price', attrs={'itemprop': 'price'})
        price = price.get('content')

        views_count = soup.find(class_='title-info-metadata-item title-info-metadata-views')
        views_count = views_count.get_text()
        views_count = get_number(views_count)

        params = soup.find(class_='item-params-list')
        params = params.find_all(class_='item-params-list-item')
        params = [param.get_text() for param in params]

        flat_fields = {}
        flat_fields['region'] = response.meta['region']

        coordinates = soup.find(class_='b-search-map expanded item-map-wrapper js-item-map-wrapper')
        latitude = coordinates['data-map-lat']
        longitude = coordinates['data-map-lon']
        if latitude:
            flat_fields['latitude'] = latitude
        if longitude:
            flat_fields['longitude'] = longitude

        districts = soup.find_all(class_='item-address-georeferences-item__content')
        if districts:
            if len(districts) == 1:
                flat_fields['district1'] = districts[0].get_text()
            elif len(districts) == 2:
                flat_fields['district1'] = districts[0].get_text()
                flat_fields['district2'] = districts[1].get_text()
            elif len(districts) >= 3:
                flat_fields['district1'] = districts[0].get_text()
                flat_fields['district2'] = districts[1].get_text()
                flat_fields['district3'] = districts[2].get_text()

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
        flat_fields['scraped_date'] = timezone.now()

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


def main():
    check_real_proxy()
    process = CrawlerProcess()
    # process = CrawlerProcess(get_project_settings())
    process.crawl(AvitoSpider)
    process.start()


def count():
    all_flats = Flat.objects.all()
    all_obj = [len(flat.region) for flat in all_flats if flat.region]
    print(max(all_obj))


if __name__ == '__main__':
    # main()
    # reset_date_scraped()
    count()
