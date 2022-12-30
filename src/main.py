from collections import defaultdict
import logging
import re
from urllib.parse import urljoin

import requests_cache
from tqdm import tqdm

from constants import EXPECTED_STATUS, MAIN_DOC_URL, PEP_URL, BASE_DIR
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import find_tag, get_soup


COMMAND_ARGS_INFO_MESSAGE = 'Аргументы командной строки: {args}'
DOWNLOAD_INFO_MESSAGE = 'Архив был загружен и сохранён: {archive_path}'
PARSER_START_MESSAGE = 'Парсер запущен!'
PARSER_FINISH_MESSAGE = 'Парсер завершил работу.'
ERROR_MESSAGE = 'Произошла ошибка в работе парсера: {error}'
REQUEST_ERROR_MESSAGE = 'Возникла ошибка при загрузке страницы {url}'
UNEXPECTED_PEP_STATUS_ERROR = (
    'Несовпадающие статусы '
    'ссылка: {pep_link} '
    'Статус в карточке: {page_status} '
    'Ожидаемые статусы: {expected_status}'
)


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    errors = []
    for section in tqdm(get_soup(
        session, whats_new_url
    ).select(
        '#what-s-new-in-python div.toctree-wrapper li.toctree-l1'
    )):
        version_a_tag = find_tag(section, 'a')
        version_link = urljoin(whats_new_url, version_a_tag['href'])
        try:
            soup = get_soup(session, version_link)
        except ConnectionError:
            errors.append(
                ConnectionError(REQUEST_ERROR_MESSAGE.format(url=version_link))
            )
            continue
        results.append(
            (
                version_link,
                find_tag(soup, 'h1').text,
                find_tag(soup, 'dl').text.replace('\n', ' ')
            )
        )
    for error in errors:
        logging.exception(error)
    return results


def latest_versions(session):
    for ul in find_tag(
        get_soup(session, MAIN_DOC_URL),
        'div',
        {'class': 'sphinxsidebarwrapper'}
    ).find_all(
        'ul'
    ):
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise NameError('Ничего не нашлось')
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append(
            (a_tag['href'], version, status)
        )
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    pdf_a4_link = get_soup(session, downloads_url).select_one(
        'div[role="main"] table.docutils a[href*="pdf-a4.zip"]'
    )['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(DOWNLOAD_INFO_MESSAGE.format(archive_path=archive_path))


def pep(session):
    errors = []
    statuses = defaultdict(int)
    elements = []
    for element in (get_soup(session, PEP_URL).find_all(
        'table', attrs={'class': 'pep-zero-table docutils align-default'}
    )):
        for row in (element.find_all('tr')):
            elements.append(row)
    for row in tqdm(elements):
        status = row.find('abbr')
        if status is not None:
            table_status = status.text[1:]
        else:
            table_status = ''
        a_tag = row.find('a')
        if a_tag is not None:
            pep_link = urljoin(PEP_URL, a_tag['href'])
            try:
                soup = get_soup(session, pep_link)
            except ConnectionError:
                errors.append(
                    ConnectionError(REQUEST_ERROR_MESSAGE.format(url=pep_link))
                )
                continue
            status_tag = soup.find(string='Status')
            page_status = status_tag.find_next('abbr').text
        else:
            continue
        expected_status = EXPECTED_STATUS.get(table_status)
        if page_status not in expected_status:
            errors.append(ValueError(
                UNEXPECTED_PEP_STATUS_ERROR.format(
                    pep_link=pep_link,
                    page_status=page_status,
                    expected_status=expected_status
                )
            ))
            continue
        statuses[page_status] += 1
    for error in errors:
        logging.exception(error)
    return [
        ('Статус', 'Количество'),
        *statuses.items(),
        ('Total', sum(statuses.values())),
    ]


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    try:
        configure_logging()
        logging.info(PARSER_START_MESSAGE)
        arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
        args = arg_parser.parse_args()
        logging.info(COMMAND_ARGS_INFO_MESSAGE.format(args=args))
        session = requests_cache.CachedSession()
        if args.clear_cache:
            session.cache.clear()
        parser_mode = args.mode
        results = MODE_TO_FUNCTION[parser_mode](session)
        if results is not None:
            control_output(results, args)
    except Exception as e:
        logging.exception(ERROR_MESSAGE.format(error=e))
    logging.info(PARSER_FINISH_MESSAGE)


if __name__ == '__main__':
    main()
