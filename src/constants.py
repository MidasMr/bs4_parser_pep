from pathlib import Path


# Урлы
MAIN_DOC_URL = 'https://docs.python.org/3/'
PEP_URL = 'https://peps.python.org/'

# Директории
BASE_DIR = Path(__file__).parent
DOWNLOADS_DIR = BASE_DIR / 'downloads'
LOG_DIR = BASE_DIR / 'logs'
LOF_FILE = LOG_DIR / 'parser.log'

# Настройки
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
OUTPUT_MODES = ('pretty', 'file')

# Константы для расчетов
EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}
