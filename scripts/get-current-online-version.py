#!/usr/bin/env python

import requests
import bs4


def main():
    response = requests.get('https://docs.aws.amazon.com/cdk/api/v2/docs/aws-construct-library.html')
    response.raise_for_status()
    soup = bs4.BeautifulSoup(response.text, 'lxml')
    version = soup.select_one('header > a[href="/cdk/api/v2/versions.html"] > h3').text
    print(version)


if __name__ == '__main__':
    main()
