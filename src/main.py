import logging
import re
from requests import RequestException
from urllib.parse import urljoin

import requests_cache
from tqdm import tqdm

from constants import EXPECTED_STATUS, MAIN_DOC_URL, PEP_URL, BASE_DIR
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import find_tag, get_soup

COMMAND_ARGS_INFO_MESSAGE = 'Аргументы командной строки: {args}'
DOWNLOAD_INFO_MESSAGE = 'Архив был загружен и сохранён: {archive_path}'
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
    soup = get_soup(session, whats_new_url)
    sections_by_python = soup.select(
        '#what-s-new-in-python div.toctree-wrapper li.toctree-l1'
    )
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        version_link = urljoin(whats_new_url, version_a_tag['href'])
        soup = get_soup(session, version_link)
        results.append(
            (
                version_link,
                find_tag(soup, 'h1').text,
                find_tag(soup, 'dl').text.replace('\n', ' ')
            )
        )
    return results


def latest_versions(session):
    soup = get_soup(session, MAIN_DOC_URL)
    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
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
    soup = get_soup(session, downloads_url)
    pdf_a4_tag = soup.select_one(
        'div[role="main"] table.docutils a[href*="pdf-a4.zip"]'
    )
    pdf_a4_link = pdf_a4_tag['href']
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
    soup = get_soup(session, PEP_URL)
    all_tables = soup.find_all(
        'table', attrs={'class': 'pep-zero-table docutils align-default'}
    )
    result = []
    request_errors = []
    for element in tqdm(all_tables):
        for row in tqdm(element.find_all('tr')):
            status = row.find('abbr')
            if status is not None:
                table_status = status.text[1:]
            else:
                table_status = ''
            a_tag = row.find('a')
            if a_tag is not None:
                pep_link = urljoin(PEP_URL, a_tag['href'])
                soup = get_soup(session, pep_link)
                status_tag = soup.find(string='Status')
                page_status = status_tag.find_next('abbr').text
            else:
                continue
            result.append((table_status, page_status, pep_link))
    if request_errors:
        for error, url in request_errors:
            logging.error(REQUEST_ERROR_MESSAGE.format(url=url))
    statuses = {}
    for table_status, page_status, pep_link in result:
        expected_status = EXPECTED_STATUS.get(table_status)
        if page_status not in expected_status:
            logging.error(
                UNEXPECTED_PEP_STATUS_ERROR.format(
                    pep_link=pep_link,
                    page_status=page_status,
                    expected_status=expected_status
                )
            )
            continue
        if page_status in statuses:
            statuses[page_status] += 1
        else:
            statuses[page_status] = 1
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
        logging.info('Парсер запущен!')
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
        logging.error(ERROR_MESSAGE.format(error=e), stack_info=True)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
