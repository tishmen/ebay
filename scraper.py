import random
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

random.seed(datetime.now())


class BadStatusCode(Exception):

    pass


class Scraper(object):

    def __init__(self):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:40.0) Ge'
            'cko/20100101 Firefox/40.0'
        }
        self.min_sleep = 1
        self.max_sleep = 10

    def get_soup(self, url, throttle=False):
        if throttle:
            sleep = random.uniform(self.min_sleep, self.max_sleep)
            print('sleeping {} seconds'.format(sleep))
            time.sleep(sleep)
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise BadStatusCode(
                'bad status code {} for {}'.format(response.status_code, url)
            )
        print('got {}'.format(url))
        return BeautifulSoup(response.content, 'html.parser')


class EbayScraper(Scraper):

    def uniquify(self, data):
        unique = []
        seen = []
        for entry in data:
            if entry['id'] in seen:
                continue
            seen.append(entry['id'])
            unique.append(entry)
        print('removed {} duplicates'.format(len(data) - len(unique)))
        return unique

    def parse_products(self, soup):
        products = []
        for result in soup.select('.sresult'):
            id_ = result['listingid']
            url = result.select_one('.lvtitle a')['href']
            image = result.select_one('.lvpic img')['src']
            product = {
                'id': id_,
                'url': url,
                'image': image,
            }
            products.append(product)
        print('parsed {} products'.format(len(products)))
        return products

    def scrape(self, seller):
        products = []
        url = 'http://www.ebay.com/sch/m.html?_ssn={}&_pgn=1&_skc=0&_ipg=200&'\
            'LH_Sold=1&LH_Complete=1'.format(seller)
        while True:
            soup = self.get_soup(url)
            products.extend(self.parse_products(soup))
            next_url = soup.select_one('.pagn-next a')
            if not next_url or next_url.get('aria-disabled'):
                break
            url = next_url['href'].replace(
                '&rt=nc', '&_ipg=200&LH_Sold=1&LH_Complete=1'
            )
        products = self.uniquify(products)
        print('got total {} products'.format(len(products)))
        return products


class GoogleScraper(Scraper):

    def uniquify(self, data):
        unique = set(data)
        print('removed {} duplicates'.format(len(data) - len(unique)))
        return list(unique)

    def parse_links(self, soup):
        links = [el['href'] for el in soup.select('.g .r a')]
        print('parsed {} links'.format(len(links)))
        return links

    def extract_amazon(self, links):
        links = [link for link in links if 'amazon.com' in link]
        print('parsed {} amazon links'.format(len(links)))
        return links

    def scrape(self, data, count):
        results = []
        for entry in data[:count]:
            links = []
            url = 'https://www.google.com/searchbyimage?image_url={}'.format(
                entry['image']
            )
            while True:
                soup = self.get_soup(url, throttle=True)
                links.extend(self.parse_links(soup))
                next_url = soup.select_one('#pnnext')
                if not next_url:
                    break
                url = (
                    'https://www.google.com' +
                    soup.select_one('#pnnext')['href']
                )
            links = self.extract_amazon(links)
            links = self.uniquify(links)
            print(
                'got total {} links for {}'.format(len(links), entry['image'])
            )
            results.append({'ebay_link': entry['url'], 'amazon_links': links})
        return results


if __name__ == '__main__':
    seller = count = None
    while not seller:
        seller = input('Type in seller: ')
    while not count:
        try:
            count = int(input('Number of Ebay products to check on Google: '))
        except ValueError:
            pass
    print('starting scraper for {}'.format(seller))
    ebay_scraper = EbayScraper()
    data = ebay_scraper.scrape(seller)
    google_scraper = GoogleScraper()
    data = google_scraper.scrape(data, count)
    print('stoping scraper for {}'.format(seller))
    timestamp = datetime.now().isoformat()
    path = '{}-{}.json'.format(seller, timestamp)
    with open(path, 'w') as f:
        json.dump(data, f, sort_keys=True, indent=4)
    print('saved out file as {}'.format(path))
