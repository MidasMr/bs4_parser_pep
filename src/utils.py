from requests import RequestException

from bs4 import BeautifulSoup

from exceptions import ParserFindTagException


FIND_TAG_ERROR_MESSAGE = 'Не найден тег {tag} {attrs}'
REQUEST_ERROR_MESSAGE = 'Возникла ошибка при загрузке страницы {url}'


def get_response(session, url):
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        return response
    except RequestException:
        raise RequestException(
            REQUEST_ERROR_MESSAGE.format(url=url),
            stack_info=True
        )


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=({} if attrs is None else attrs))
    if searched_tag is None:
        raise ParserFindTagException(
            FIND_TAG_ERROR_MESSAGE.format(tag=tag, attrs=attrs)
        )
    return searched_tag


def get_soup(session, url):
    response = get_response(session, url)
    if response is None:
        raise RequestException(
            REQUEST_ERROR_MESSAGE.format(url=url),
            stack_info=True
        )
    return BeautifulSoup(response.text, features='lxml')
