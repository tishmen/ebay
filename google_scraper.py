import random
import json
import sys
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

random.seed(datetime.now())
headers = {
    'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:40.0) Gecko/2010'
        '0101 Firefox/40.0'
}


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


def parse_links(soup):
    links = [el['href'] for el in soup.select('.g .r a')]
    print('parsed {} links'.format(len(links)))
    return links


def scrape_links(image_url):
    links = []
    url = 'https://www.google.com/searchbyimage?image_url={}'.format(image_url)
    while True:
        soup = do_request(url, throttle=True)
        links.extend(parse_links(soup))
        next_url = soup.select_one('#pnnext')
        if not next_url:
            break
        url = 'https://www.google.com' + soup.select_one('#pnnext')['href']
    print('got total {} links'.format(len(links)))
    return set(links)


def extract_amazon_links(links):
    return [link for link in links if 'amazon.com' in link]


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('please supply seller as argument')
        sys.exit()
    image_url = sys.argv[1]
    print('starting scrape for {}'.format(image_url))
    links = scrape_links(image_url)
    print('stoping scrape for {}'.format(image_url))
    timestamp = datetime.now().isoformat()
    path = '{}.json'.format(timestamp)
    with open(path, 'w') as f:
        json.dump(links, f, sort_keys=True, indent=4)
    print('saved out file as {}'.format(path))
