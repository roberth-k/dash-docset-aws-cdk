#!/usr/bin/env python

import util


def main():
    page = util.download_file('/cdk/api/v2/docs/aws-construct-library.html')
    soup = util.load_bs4(page.decode('utf8'))
    version = util.get_page_version(soup)
    print(version)


if __name__ == '__main__':
    main()
