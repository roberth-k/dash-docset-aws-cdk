import bs4
import cchardet
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



ENTRY_TYPE_PREFIX_MAPPING = {
    'class': 'Class',
    'interface': 'Interface',
    'enum': 'Enum',
}

ENTRY_TYPE_SUFFIX_MAPPING = {
    'module': 'Module',
}


def get_entry_type(title: str, default: str = 'Guide') -> str:
    return (
            ENTRY_TYPE_PREFIX_MAPPING.get(title.split(' ')[0].lower().strip())
            or ENTRY_TYPE_SUFFIX_MAPPING.get(title.split(' ')[-1].lower().strip())
            or default
    )
