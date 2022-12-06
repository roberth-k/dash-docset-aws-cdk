from typing import List, Tuple

import bs4
import cchardet
import re
import requests
from urllib.parse import urljoin

BASE_URL = 'https://docs.aws.amazon.com'
REQUESTS_SESSION = requests.Session()
_cchardet = cchardet  # Prevent optimizer from removing the import.


def download_file(path: str) -> bytes:
    response = REQUESTS_SESSION.get(urljoin(BASE_URL, path))
    response.raise_for_status()
    return response.content


def get_page_version(soup: bs4.BeautifulSoup) -> str:
    return soup.select_one('header > a[href="/cdk/api/v2/versions.html"] > h3').text


def load_bs4(data) -> bs4.BeautifulSoup:
    if isinstance(data, bytes):
        data = data.decode('utf8')

    return bs4.BeautifulSoup(data, 'lxml')


def get_entry_type(title: str) -> str:
    # Strip special characters (such as the 🔹used by experimental constructs).
    title = ''.join(c for c in title if c.isascii() or c == ' ').strip()

    if '_patterns' not in get_entry_type.__dict__:
        get_entry_type._patterns = [
            (re.compile(pattern), result)
            for pattern, result in [
                (r'^.* module$', 'Module'),
                (r'^class Cfn.* \(construct\)$', 'Resource'),  # L1 construct
                (r'^.* \(construct\)$', 'Constructor'),
                (r'^class .*$', 'Class'),
                (r'^enum .*$', 'Enum'),
                (r'^interface I[A-Z].*$', 'Interface'),
                (r'^interface Cfn.*Props$', 'Property'),  # L1 construct props
                (r'^interface .*Props$', 'Property'),  # L2 construct props
                (r'^interface .*$', 'Struct'),
            ]
        ]

    patterns: List[Tuple[re.Pattern, str]] = get_entry_type._patterns

    for pattern, result in patterns:
        if pattern.match(title):
            return result

    return 'Guide'


def get_entry_title(page_title: str, entry_type: str, relative_path: str) -> str:
    page_title = page_title.strip()

    match entry_type:
        case 'Guide':
            return page_title
        case 'Module':
            return page_title \
                .removesuffix(' module') \
                .removeprefix('@aws-cdk/') \
                .removeprefix('aws-cdk-lib.')
        case _:
            return relative_path \
                .split('/')[-1] \
                .removesuffix('.html') \
                .removeprefix('@aws-cdk_aws-') \
                .removeprefix('aws-cdk-lib.aws_') \
                .replace('.', ' ', 1)
