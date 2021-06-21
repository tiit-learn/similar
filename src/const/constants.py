import os

PROJECT_URL = 'https://%s/' % os.getenv('site')
DB_NAME = 'projects.db'
TEMP_DIR = 'temp'
TOTAL_PAGES = 10

# Нужно передать в настройки etc
TRUST_NAME = os.getenv('USER_CHECK')
TRUST_PASSWD = os.getenv('USER_CHECK_PSW')
COOKIE_NAME = os.getenv('site') + '.json'

os.environ['GLOBAL_BLACK_URLS'] = '''youtube.com'''

BAD_TITLE = ['Web Server Is Down',
             'Oops, Something Lost',
             'Хостинг Аккаунт Был Заблокирован',
             'Welcome To Nginx!',
             'Congratulations, The Site Was Created Successfully!',
             '404 Not Found',
             '403 Forbidden',
             'Error 403 (Forbidden)',
             '502 Bad Gateway',
             '509 Bandwidth Limit Exceeded',
             '522: Connection Timed Out',
             '526: Invalid Ssl Certificate',
             'Доступ К Сайту Ограничен',
             'Страница Не Найдена',
             'Сайт Заблокирован Или Еще Не Активировался',
             'Temporarily Unavailable',
             'Suspected Phishing Site',
             'Returning An Unknown Error',
             'Apache Http Server Test',
             'Default Web Site Pag',
             'Privacy Error',
             '[.M] Masterhost - Профессиональный Хостинг',
             'Gateway Time-Out',
             'Срок Регистрации Домена',
             'Этот Домен Припаркован Компанией Timeweb',
             'Ой...',
             'Account Suspended',
             'Not Found',
             'Resources And Information.',
             'Web Server\'S Default Page',
             'Is For Sale',
             'This Site Has Been Seized',
             'Dns Resolution Error',
             'Server Error',
             'Работа Сайта Временно Приостановлена']

WAITE_TITLES = ['Just A Moment...',
                'Just a moment please...',
                'Cloudflare']

DDOS_TITLES = ['Attention Required! | Cloudflare',
               'Ddos-Guard',
               'Access Denied',
               'Security Check ...',
               'Bot Verification',
               'Visitor Anti-Robot Validation']
