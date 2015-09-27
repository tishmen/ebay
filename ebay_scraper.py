import random
import time
import sys
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

random.seed(datetime.now())
headers = {
    'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:40.0) Gecko/2010'
        '0101 Firefox/40.0'
}


def uniquify(products):
    unique = []
    seen = []
    for product in products:
        if product['id'] in seen:
            continue
        seen.append(product['id'])
        unique.append(product)
    print('removed {} duplicates'.format(len(products) - len(unique)))
    return unique


def do_request(url, throttle=False, min_sleep=1, max_sleep=10):
    if throttle:
        sleep = random.uniform(min_sleep, max_sleep)
        print('sleeping {} seconds'.format(sleep))
        time.sleep(sleep)
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(
            'bad status code {} for {}'.format(response.status_code, url)
        )
    print('got {}'.format(url))
    return BeautifulSoup(response.content, 'html.parser')


def parse_products(soup):
    products = []
    for result in soup.select('.sresult'):
        id_ = result['listingid']
        url = result.select_one('.lvtitle a')['href']
        title = result.select_one('.lvtitle a').string
        image = result.select_one('.lvpic img')['src']
        span = result.select_one('.prc span')
        if not span:
            continue
        price = float(span.get_text().strip().split('$')[-1].replace(',', ''))
        product = {
            'id': id_,
            'url': url,
            'title': title,
            'image': image,
            'price': price
        }
        products.append(product)
    print('parsed {} products'.format(len(products)))
    return products


def scrape_products(seller):
    products = []
    url = 'http://www.ebay.com/sch/m.html?_ssn={}&_pgn=1&_skc=0&_ipg=200&LH_S'\
        'old=1&LH_Complete=1'.format(seller)
    while True:
        soup = do_request(url)
        products.extend(parse_products(soup))
        next_url = soup.select_one('.pagn-next a')
        if not next_url or next_url.get('aria-disabled'):
            break
        url = next_url['href'].replace(
            '&rt=nc', '&_ipg=200&LH_Sold=1&LH_Complete=1'
        )
    products = uniquify(products)
    print('got total {} products'.format(len(products)))
    return products


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('please supply seller as argument')
        sys.exit()
    seller = sys.argv[1]
    print('starting scrape for {}'.format(seller))
    products = scrape_products(seller)
    print('stoping scrape for {}'.format(seller))
    timestamp = datetime.now().isoformat()
    path = '{}.json'.format(timestamp)
    with open(path, 'w') as f:
        json.dump(products, f, sort_keys=True, indent=4)
    print('saved out file as {}'.format(path))
