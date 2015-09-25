import sys
import json
import math
import requests
from datetime import datetime
from bs4 import BeautifulSoup


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


def do_request(url):
    response = requests.get(url)
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
        title = result.select_one('.lvtitle a').string
        image = result.select_one('.lvpic img')['src']
        span = result.select_one('.prc span')
        if not span:
            continue
        price = float(span.get_text().strip().split('$')[-1].replace(',', ''))
        product = {
            'id': id_,
            'title': title,
            'image': image,
            'price': price
        }
        products.append(product)
    print('parsed {} products'.format(len(products)))
    return products


def scrape_products(seller):
    page = 1
    start_url = 'http://www.ebay.com/sch/m.html?_ssn={}&_ipg=200&_pgn={}'
    soup = do_request(start_url.format(seller, page))
    products = parse_products(soup)
    product_count = int(soup.select_one('.rcnt').string.replace(',', ''))
    page_count = int(math.ceil(product_count / 200.0))
    for i in range(page, page_count):
        soup = do_request(start_url.format(seller, i + 1))
        products.extend(parse_products(soup))
    print('parsed total {} products'.format(len(products)))
    return uniquify(products)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('please supply seller as argument')
        sys.exit()
    seller = sys.argv[1]
    print('starting scrape for {}'.format(seller))
    products = scrape_products(seller)
    print('got total {} products'.format(len(products)))
    print('stoping scrape for {}'.format(seller))
    timestamp = datetime.now().isoformat()
    path = '{}_{}.json'.format(seller, timestamp)
    with open(path, 'w') as f:
        json.dump(products, f, sort_keys=True, indent=4)
    print('saved out file as {}'.format(path))
