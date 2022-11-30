import argparse
import dataclasses

import cchardet
import os
import os.path as os_path
import sqlite3
from multiprocessing import Pool
from typing import Set, Optional
from urllib.parse import urljoin, quote as url_quote

import requests
import bs4

BASE_URL = 'https://docs.aws.amazon.com'
_cchardet = cchardet  # Prevent optimizer from removing the import.
requests_session = requests.Session()


@dataclasses.dataclass
class Entry:
    name: str
    type: str
    relative_path: str


def get_url(path: str) -> bytes:
    response = requests_session.get(urljoin(BASE_URL, path))
    response.raise_for_status()
    return response.content


def list_toc() -> Set[str]:
    page = get_url('/cdk/api/v2/docs/aws-construct-library.html').decode('utf8')
    soup = bs4.BeautifulSoup(page, 'lxml')
    return {a['href'] for a in soup.select('a.navItem')}


ENTRY_TYPE_MAPPING = {
    'class': 'Class',
    'interface': 'Interface',
    'enum': 'Enum',
}


def get_entry_type(title: str, default: str = 'Guide') -> str:
    first_word = title.split(' ')[0]
    return ENTRY_TYPE_MAPPING.get(first_word.lower().strip(), default)


def should_skip(docset_path: str) -> bool:
    if not docset_path.endswith('.html'):
        return False

    if os_path.exists(docset_path):
        return True

    return False


def process_page(documents_path: str, page_path: str) -> Optional[Entry]:
    docset_path = os_path.join(documents_path, page_path.lstrip('/'))

    if should_skip(docset_path):
        return None

    print(str(docset_path))
    page = get_url(page_path).decode('utf8')

    soup = bs4.BeautifulSoup(page, 'lxml')

    for script in soup.select('script'):
        script.decompose()

    soup.select_one('.fixedHeaderContainer').decompose()
    soup.select_one('.navPusher')['style'] = 'padding-top: 0;'
    soup.select_one('.docMainWrapper')['style'] = 'max-width: 100%; margin: 0;'
    soup.select_one('.docsNavContainer').decompose()
    soup.select_one('.mainContainer > .wrapper')['style'] = 'max-width: 100%; margin: 0;'
    soup.select_one('.docs-prevnext').decompose()
    soup.select_one('nav.onPageNav').decompose()
    soup.select_one('footer').decompose()
    soup.select_one('h1')['style'] = 'margin: 10px 0;'  # Remove whitespace around page title.

    if soup.select_one('header.postHeader').text == '':
        # Remove whitespace that occurs in regular reference pages.
        soup.select_one('header.postHeader').decompose()

    # Convert all absolute links to relative ones.
    for selector, attr in [
        ('[href]', 'href'),
        ('img', 'src'),
    ]:
        for elem in soup.select(selector):
            if elem[attr].startswith('/'):
                elem[attr] = os_path.relpath(elem[attr], os_path.dirname(page_path))

    # Set up the Dash Table of Contents.
    for selector in ['h2', 'h3', 'h4', 'h5', 'h6']:
        for elem in soup.select(selector):
            elem.select_one('a.hash-link').decompose()
            elem.select_one('a')['name'] = '//apple_ref/cpp/Section/' + url_quote(elem.text)
            elem.select_one('a')['class'] += ['dashAnchor']

    soup.select_one('html').insert(0, bs4.Comment(f'Online page at {urljoin(BASE_URL, page_path)}'))

    page_title = (soup.select_one('header h1') or soup.select_one('article h1')).text
    entry_type = get_entry_type(page_title)

    if entry_type in ['Class', 'Interface', 'Enum']:
        entry_title = page_path.split('/')[-1].removesuffix('.html')
    else:
        entry_title = page_title

    os.makedirs(os_path.dirname(docset_path), exist_ok=True)
    with open(docset_path, 'w') as fp:
        fp.write(str(soup))

    return Entry(
        name=entry_title,
        type=entry_type,
        relative_path=page_path,
    )


def copy_file(documents_path, file_path: str):
    docset_path = os_path.join(documents_path, file_path.lstrip('/'))

    if should_skip(docset_path):
        return

    os.makedirs(os_path.dirname(docset_path), exist_ok=True)

    data = get_url(file_path)

    with open(docset_path, 'wb') as fp:
        fp.write(data)


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--index', dest='index_path', required=True)
    args.add_argument('--documents', dest='documents_path', required=True)
    args = args.parse_args()

    index_path = os_path.abspath(args.index_path)
    documents_path = os_path.abspath(args.documents_path)

    if os_path.exists(args.index_path):
        raise RuntimeError('The index must not exist!')

    if not os_path.exists(args.documents_path):
        raise RuntimeError('The documents path must exist!')

    copy_file(documents_path, '/cdk/api/v2/css/default.min.css')
    copy_file(documents_path, '/cdk/api/v2/css/main.css')
    copy_file(documents_path, '/cdk/api/v2/img/dotnet32.png')
    copy_file(documents_path, '/cdk/api/v2/img/go32.png')
    copy_file(documents_path, '/cdk/api/v2/img/java32.png')
    copy_file(documents_path, '/cdk/api/v2/img/python32.png')
    copy_file(documents_path, '/cdk/api/v2/img/typescript32.png')

    with Pool(processes=os.cpu_count()+1) as pool:
        index = pool.starmap(
            process_page,
            [
                (documents_path, page_path)
                for page_path in list_toc()
            ],
            chunksize=100,
        )

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
