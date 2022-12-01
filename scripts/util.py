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


def get_entry_type(title: str) -> str:
    title = ''.join(c for c in title.lower() if c.isalnum() or c == ' ').strip()
    first_word = title.split(' ')[0]
    last_word = title.split(' ')[-1]

    match first_word, last_word:
        case _, 'module':
            return 'Module'
        case 'class', 'construct' if title.startswith('class cfn'):
            return 'Resource'  # L1 construct
        case _, 'construct':
            return 'Constructor'
        case 'class', _:
            return 'Class'
        case 'enum', _:
            return 'Enum'
        case 'interface', _ if title.startswith('interface i'):
            return 'Interface'
        case 'interface', _ if title.startswith('interface cfn') and title.endswith('props'):
            return 'Property'  # L1 construct props
        case 'interface', _ if title.endswith('props'):
            return 'Property'  # L2 construct props
        case 'interface', _:
            return 'Struct'
        case _:
            return 'Guide'
