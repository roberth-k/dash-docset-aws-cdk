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
