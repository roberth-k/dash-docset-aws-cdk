#!/usr/bin/env python

import argparse
import dataclasses
import functools
import os
from multiprocessing.pool import ThreadPool
from typing import Callable

import util


@dataclasses.dataclass
class SourceFile:
    relative_path: str
    data: bytes


def download(link: str, callback: Callable[[SourceFile], None]):
    response = util.download_file(link)
    source_file = SourceFile(
        relative_path=link.lstrip('/'),
        data=response)
    callback(source_file)
    print(source_file)


def run(expect_version: str, callback: Callable[[SourceFile], None]):
    data = util.download_file('/cdk/api/v2/docs/aws-construct-library.html')
    soup = util.load_bs4(data)

    if (page_version := util.get_page_version(soup)) != expect_version:
        raise RuntimeError(f'Page version is {page_version}; expected {expect_version}.')

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
        thread_pool.map(functools.partial(download, callback=callback), files)


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--expect-version', dest='expect_version', required=True)
    args.add_argument('--target-dir', dest='target_dir', required=True)
    args = args.parse_args()

    def callback(source_file: SourceFile):
        target_path = os.path.join(args.target_dir, source_file.relative_path)
        if os.path.exists(target_path):
            return
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'wb') as fp:
            fp.write(source_file.data)

    run(expect_version=args.expect_version,
        callback=callback)


if __name__ == '__main__':
    main()
