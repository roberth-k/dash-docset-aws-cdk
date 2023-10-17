#!/usr/bin/env python

import argparse
import functools
import os
from multiprocessing.pool import ThreadPool

import util


def download(link: str, target_dir: str):
    target_path = os.path.join(target_dir, link.lstrip('/'))
    if os.path.exists(target_path):
        return
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    response = util.download_file(link)
    with open(target_path, 'wb') as fp:
        fp.write(response)
    print(target_path)


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--expect-version', dest='expect_version', required=True)
    args.add_argument('--target-dir', dest='target_dir', required=True)
    args = args.parse_args()

    data = util.download_file('/cdk/api/v2/docs/aws-construct-library.html')
    soup = util.load_bs4(data)

    if (page_version := util.get_page_version(soup)) != args.expect_version:
        raise RuntimeError(f'Page version is {page_version}; expected {args.expect_version}.')

    files = {a['href'] for a in soup.select('a.navItem')}
    files.add('/cdk/api/v2/css/default.min.css')
    files.add('/cdk/api/v2/css/main.css')
    files.add('/cdk/api/v2/img/dotnet32.png')
    files.add('/cdk/api/v2/img/go32.png')
    files.add('/cdk/api/v2/img/java32.png')
    files.add('/cdk/api/v2/img/python32.png')
    files.add('/cdk/api/v2/img/typescript32.png')
    files.add('/cdk/api/v2/img/favicon-32x32.png')
    files.add('/cdk/api/v2/img/cfn--resources-stable-success.svg')
    files.add('/cdk/api/v2/img/cdk--constructs-experimental-important.svg')
    files.add('/cdk/api/v2/img/experimental-important.svg')
    files.add('/cdk/api/v2/img/cdk--constructs-developer--preview-informational.svg')
    files.add('/cdk/api/v2/img/cdk--constructs-stable-success.svg')
    files.add('/cdk/api/v2/img/jsconstructs.svg')
    files.add('/cdk/api/v2/img/pyconstructs.svg')
    files.add('/cdk/api/v2/img/nuconstructs.svg')
    files.add('/cdk/api/v2/img/maven-badge.svg')

    with ThreadPool(processes=os.cpu_count()*4) as thread_pool:
        thread_pool.map(functools.partial(download, target_dir=args.target_dir), files)


if __name__ == '__main__':
    main()
