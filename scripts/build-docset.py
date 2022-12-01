#!/usr/bin/env python
from multiprocessing import Pool

import argparse
import bs4
import dataclasses
import functools
import glob2
import os
import sqlite3
from typing import Optional
from urllib.parse import urljoin, quote as url_quote

import util


@dataclasses.dataclass
class Entry:
    name: str
    type: str
    relative_path: str


TABLE_OF_CONTENTS_MAPPING = [
    ('h2', None, None, 'Section'),
    ('h3', 'h2', 'Construct Props', 'Attribute'),
    ('h3', 'h2', 'Methods', 'Method'),
    ('h3', 'h2', 'Properties', 'Property'),
    ('h3', 'h2', 'Members', 'Value'),
    ('h3', None, None, 'Guide'),
    ('h4', None, None, 'Guide'),
    ('h5', None, None, 'Guide'),
    ('h6', None, None, 'Guide'),
]


def embed_dash_toc(soup: bs4.BeautifulSoup):
    memory = {}

    def set_entry_type(elem, entry_type):
        #  All headers should already have an internal anchor point.
        a = elem.select_one('a')
        a['name'] = f'//apple_ref/cpp/{entry_type}/{url_quote(elem.text)}'
        if 'class' not in elem:
            a['class'] = []
        a['class'] += ['dashAnchor']

    for elem in soup.select_one('article > div > span').children:
        for this_tag, last_sibling_tag, last_sibling_text, toc_entry_type in TABLE_OF_CONTENTS_MAPPING:
            if elem.name != this_tag:
                continue

            if last_sibling_tag is None:
                set_entry_type(elem, toc_entry_type)
                break

            if memory.get(last_sibling_tag) == last_sibling_text:
                set_entry_type(elem, toc_entry_type)
                break

        memory[elem.name] = elem.text


def rewrite_links(soup: bs4.BeautifulSoup, relative_path: str):
    # Convert all absolute links to relative ones.
    for selector, attr in [
        ('[href]', 'href'),
        ('img', 'src'),
    ]:
        for elem in soup.select(selector):
            if elem[attr].startswith(('/cdk/api/v2/docs/', '/cdk/api/v2/img/', '/cdk/api/v2/css/')):
                # Pages indexed in the docset must be linked using relative URL-s.
                elem[attr] = os.path.relpath(elem[attr], start=os.path.dirname('/'+relative_path))
            elif '/' not in elem[attr]:
                # Sometimes the links are already relative -- don't touch them.
                pass
            else:
                # External pages.
                elem[attr] = urljoin(util.BASE_URL, elem[attr])


def get_entry_title(page_title: str, entry_type: str, relative_path: str) -> str:
    if entry_type in ['Class', 'Interface', 'Enum']:
        return relative_path \
            .split('/')[-1] \
            .removesuffix('.html') \
            .removeprefix('aws-cdk-lib.') \
            .removeprefix('@aws-cdk_')
    elif entry_type in ['Module']:
        return page_title \
            .removesuffix(' module') \
            .removeprefix('aws-cdk-lib.') \
            .removeprefix('@aws-cdk/')
    else:
        return page_title


def render_page(source_path: str, source_dir: str, target_dir: str, expect_version: str) -> Optional[Entry]:
    relative_path = os.path.relpath(source_path, start=source_dir)
    target_path = os.path.join(target_dir, relative_path)

    if os.path.exists(target_path):
        return None

    print(os.path.relpath(target_path))

    with open(source_path, 'r') as fp:
        soup = util.load_bs4(fp)

    if (page_version := util.get_page_version(soup)) != expect_version:
        raise RuntimeError(f'Page version is {page_version}; expected {expect_version}.')

    for script in soup.select('script'):
        script.decompose()

    soup.select_one('.fixedHeaderContainer').decompose()  # Remove blue bar at the top.
    soup.select_one('.navPusher')['style'] = 'padding-top: 0;'  # Remove spacing that accommodated for the bue bar.
    soup.select_one('.docMainWrapper')['style'] = 'max-width: 100%; margin: 0;'  # Remove horizontal whitespace.
    soup.select_one('.docsNavContainer').decompose()  # Remove navigation column on the left.
    soup.select_one('.mainContainer > .wrapper')['style'] = 'max-width: 100%; margin: 0;'  # Remove horizontal whitespace.
    soup.select_one('.docs-prevnext').decompose()  # Remove Prev/Next navigation buttons.
    soup.select_one('nav.onPageNav').decompose()  # Remove on-page navigation column.
    soup.select_one('footer').decompose()  # Remove footer.
    soup.select_one('h1')['style'] = 'margin: 10px 0;'  # Remove whitespace around page title.

    if soup.select_one('header.postHeader').text == '':
        # Remove whitespace that occurs in regular reference pages.
        soup.select_one('header.postHeader').decompose()

    for a in soup.select('a.hash-link'):
        a.decompose()

    rewrite_links(soup, relative_path)
    embed_dash_toc(soup)

    soup.select_one('html').insert(0, bs4.Comment(f'Online page at {urljoin(util.BASE_URL, relative_path)}'))

    page_title = soup.select_one('h1').text
    entry_type = util.get_entry_type(page_title)

    entry_title = get_entry_title(page_title, entry_type, relative_path)

    # Adds the fully qualified name of this object to the top of the page.
    bookmark = soup.new_tag('span')
    bookmark.string = relative_path.split('/')[-1].removesuffix('.html')
    soup.select_one('h1').parent.insert(0, bookmark)

    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    with open(target_path, 'w') as fp:
        fp.write(str(soup))

    return Entry(
        name=entry_title,
        type=entry_type,
        relative_path=relative_path,
    )


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--source-dir', dest='source_dir', required=True)
    args.add_argument('--target-dir', dest='target_dir', required=True)
    args.add_argument('--index', dest='index_path', required=True)
    args.add_argument('--expect-version', dest='expect_version', required=True)
    args = args.parse_args()

    source_dir: str = os.path.abspath(args.source_dir)
    target_dir: str = os.path.abspath(args.target_dir)
    index_path: str = os.path.abspath(args.index_path)
    expect_version: str = args.expect_version

    if not os.path.exists(target_dir):
        raise RuntimeError('Target directory does not exist!')

    files = glob2.glob(os.path.join(source_dir, '**/*.html'))

    with Pool(processes=os.cpu_count()+1) as pool:
        index = pool.map(
            functools.partial(
                render_page,
                source_dir=source_dir,
                target_dir=target_dir,
                expect_version=expect_version),
            files,
            chunksize=1)

    with sqlite3.connect(index_path, timeout=30.0) as conn:
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT)')
        c.execute('CREATE UNIQUE INDEX IF NOT EXISTS anchor ON searchIndex (name, type, path)')
        c.executemany(
            '''INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?)''',
            [
                (entry.name, entry.type, entry.relative_path)
                for entry in index
                if entry
            ],
        )
        conn.commit()


if __name__ == '__main__':
    main()
