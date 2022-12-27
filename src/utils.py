import logging

# Импорт базового класса ошибок библиотеки request.
from requests import RequestException

from constants import EXPECTED_STATUS
from exceptions import ParserFindTagException


def get_response(session, url):
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        return response
    except RequestException:
        logging.exception(
            f'Возникла ошибка при загрузке страницы {url}',
            stack_info=True
        )


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag


def get_result(pep_status_list):
    result = [('Статус', 'Количество')]
    statuses = {
        'Active': 0,
        'Accepted': 0,
        'Deferred': 0,
        'Final': 0,
        'Provisional': 0,
        'Rejected': 0,
        'Superseded': 0,
        'Withdrawn': 0,
        'Draft': 0,
    }

    for status in pep_status_list:
        expected_status = EXPECTED_STATUS.get(status[0])
        if status[1] not in expected_status:
            message = (
                'Несовпадающие статусы '
                f'ссылка: {status[2]} '
                f'Статус в карточке: {status[1]} '
                f'Ожидаемые статусы: {expected_status}'
            )
            logging.error(message)
            continue
        statuses[status[1]] += 1

    for key, value in statuses.items():
        result.append((key, value))
    result.append(('Всего', len(pep_status_list)))
    return result
