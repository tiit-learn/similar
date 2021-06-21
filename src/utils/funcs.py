import base64
import imagehash
import json
import logging.config
import os
import pickle
import requests_html
import re
import time
from urlextract import URLExtract

from src.utils import utils, db_utils

from io import BytesIO
from PIL import Image
from selenium import webdriver, common
from urllib.parse import urlparse
# from selenium.webdriver.chrome.options import Options

from ..const.constants import *


def get_browser_chrome(url, options=None, waite=True):
    """
    Функция возвращающая объект браузера с открытой вкладкой переданного url.

    Для установки аргумента, например:
        chrome_options.add_argument("--headless")

    Нужно передать в аргумент функции options, значение "--headless", по
    умолчанию не устанавливаются аргументы.
    Функциональность
    """
    # "--headless"

    if not urlparse(url).netloc:
        url = 'http://%s' % url

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("lang=ru")
    if options:
        chrome_options.add_argument(options)
        chrome_options.add_argument("window-size=1920,925")
    prefs = {"excludeSwitches": ['enable-logging'],
             "translate_whitelists": {"ru": "ru"},
             "intl.accept_languages": 'ru,ru_EN',
             # "translate": {"enabled": "true"},
             }
    chrome_options.add_experimental_option("prefs", prefs)
    browser = webdriver.Chrome(
        'chromedriver', options=chrome_options)

    browser.maximize_window()
    browser.set_page_load_timeout(30)

    try:
        browser.get(url)
    except common.exceptions.TimeoutException:
        """Долгая загрузка"""
    except common.exceptions.WebDriverException:
        """Не загружается страница"""

    check_domains_status(browser)

    if waite:
        time.sleep(3)

    return browser


def check_domains_status(browser):
    """
    Функция проверяет статус ответа сайта, если статус плохой, функция
    вызывает исключение.
    Функциональность
    """

    b_title = browser.title

    bad_titles = BAD_TITLE
    wait_titles = WAITE_TITLES
    ddos_titles = DDOS_TITLES

    for bad_title in bad_titles:
        if bad_title.lower() in b_title.lower():
            raise common.exceptions.WebDriverException('Website Not Work')

    for ddos_title in ddos_titles:
        if ddos_title.lower() in b_title.lower():
            raise common.exceptions.WebDriverException('Website Protected')

    for wait_title in wait_titles:
        if wait_title.lower() in b_title.lower():
            print('Need wait. Dont panic!')
            time.sleep(6)


def get_response(method='GET', url='https://google.com',
                 headers=None, data=None, cookies=False, stream=False):
    """
    Функция возвращает настроенный объект Response для работы.
    Функциональность
    """
    # TODO: Соединить с get_browser_chrome
    session = requests_html.HTMLSession()
    if not headers:
        headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                   'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36 OPR/74.0.3911.218'}
        session.headers.update(headers)

    if cookies:
        with open(os.path.join('cookie', COOKIE_NAME)) as file:
            for cookie in json.loads(file.read()):
                session.cookies.set(cookie['name'], cookie['value'])

    return session.request(method, url, data=data, stream=stream)


def find_on_search_site(url):
    """
    Функция поиска на сайте
    Функциональность
    Возвращает:
    :domain: -> строка - название домена
    :find_projects: -> список списка [заголовок, ID проекта]
    """
    domain = utils.get_domain(url)

    print(' Поиск на сайте '.center(80, '-'), sep='')
    resp = get_response(url='https://www.%s/search/content?keys=%s' %
                        (os.getenv('site'), domain))
    print(('\t- %s' % domain))
    results = resp.html.xpath(
        '//div[contains(@class, "search-result views-row ")]')
    count = 0
    find_projects = []
    print()
    if len(results) != 0:
        for result in results:
            if domain.lower() in result.text.lower():
                if 'project' in result.find('a')[0].attrs['href']:
                    title = result.find('h3', first=True).text
                    url_t = result.find('a')[0].attrs['href']
                    count += 1
                    find_projects.append([title, url_t.split('/')[-1]])
                    find_out = '%s - %s - https://www.%s%s' % (
                        url_t.split('/')[-1], title, os.getenv('site'), url_t)
                    print(find_out)
    else:
        print('Нет совпадений'.center(80), sep='')
    print()
    print(''.center(80, '-'))
    print(('Найдено проектов: %s' % count).rjust(80))
    print(''.center(80, '-'))

    return domain, find_projects


def find_simular_db_from_file(img_path=False, img_base64=False, differ=80, steps=False):
    """
    Функция поиска похожего сайта в БД по картинке
    Функциональность

    Возвращает:

    :file_img_hash: - base64 картинка проверяемого URL
    :img_hash_1: - hash проверяемой картинки URL
    :c_title: - текущий заголовок проверяемого сайта
    :done: - словарь с элементами ID проектов, который содержит кортеж из данных
             БД этого проекта
    """

    print((' Поиск в БД (%s)' %
           ('FILE' if img_path else 'BASE64')).center(80, '-'), sep='')
    if img_path:
        img_hash_1, *_ = get_hash_from_file(file_path=img_path)
    if img_base64:
        img_hash_1, *_ = get_hash_from_file(img_base64=img_base64)

    all_data = db_utils.all_db_data()
    done = {}
    # обход каждой строки в БД
    for data in all_data:
        find = False
        # получение хешей в строке в БД
        img_data_2 = pickle.loads(bytes.fromhex(data[-1]))
        hash_num = 0

        # взять каждый хеш строки и сверить с img_hash_1
        for img_hash_2 in img_data_2:
            def_i = get_difference_hash(img_hash_1, img_hash_2)

            hash_num += 1
            if def_i > differ:
                if not find:
                    # Если найденных нет, то создается элемент
                    # в словаре.
                    done[data[0]] = (def_i,
                                     data[0],
                                     data[1],
                                     data[2],
                                     len(img_data_2),
                                     hash_num)
                    find = True
                    continue

                if def_i > done[data[0]][0]:
                    # Если вычесленная разница больше то, которая
                    # находится в БД, то заменить ее
                    done[data[0]] = (def_i,
                                     data[0],
                                     data[1],
                                     data[2],
                                     len(img_data_2),
                                     hash_num)

    if len(done.items()) < 1:
        print('\n', 'Нет совпадений'.center(80), sep='')
        result = 'Найдено совпадений: 0'
    else:
        print()
        for i in sorted(done.values(), key=lambda x: x[0], reverse=True):
            print('%.2f %% - %s - %s - %s - Хешей: (%s/%s)' % i)
        result = 'Найдено совпадений: %s' % len(done)
    print()
    print('-'.center(80, '-'),
          result.rjust(80),
          '-'.center(80, '-'), sep='\n')

    return done


def find_simular_db_from_url(url, differ=80, steps=False):
    """
    Функция поиска похожего сайта в БД по url
    Функциональность

    Возвращает:

    :file_img_hash: - base64 картинка проверяемого URL
    :img_hash_1: - hash проверяемой картинки URL
    :c_title: - текущий заголовок проверяемого сайта
    :done: - словарь с элементами ID проектов, который содержит кортеж из данных
             БД этого проекта
    """
    if not urlparse(url).netloc:
        url = 'http://%s' % url

    print(' Поиск в БД (URL)'.center(80, '-'), sep='')
    img_hash_1, file_img_hash, c_title, current_url = get_hash_from_url(url)
    title = '%s\n\t  %s' % (c_title.title(),
                            urlparse(url).netloc)
    print('\t- ' + current_url, '\t- ' + title, sep='\n')
    print('-'.center(80, '-'), '', sep='\n')

    all_data = db_utils.all_db_data()
    done = {}
    # обход каждой строки в БД
    for data in all_data:
        find = False
        # получение хешей в строке в БД
        img_data_2 = pickle.loads(bytes.fromhex(data[-1]))
        hash_num = 0

        # взять каждый хеш строки и сверить с img_hash_1
        for img_hash_2 in img_data_2:
            def_i = get_difference_hash(img_hash_1, img_hash_2)

            hash_num += 1
            if def_i > differ:
                if not find:
                    # Если найденных нет, то создается элемент
                    # в словаре.
                    done[data[0]] = (def_i,
                                     data[0],
                                     data[1],
                                     data[2],
                                     len(img_data_2),
                                     hash_num)
                    find = True
                    continue

                if def_i > done[data[0]][0]:
                    # Если вычесленная разница больше то, которая
                    # находится в БД, то заменить ее
                    done[data[0]] = (def_i,
                                     data[0],
                                     data[1],
                                     data[2],
                                     len(img_data_2),
                                     hash_num)

    if len(done.items()) < 1:
        print('Нет совпадений'.center(80), sep='')
        result = 'Найдено совпадений: 0'
    else:
        # breakpoint()
        for i in sorted(done.values(), key=lambda x: x[0], reverse=True):
            print('%.2f %% - %s - %s - %s - Хешей: (%s/%s)' % i)
        result = 'Найдено совпадений: %s' % len(done)
    print()
    print('-'.center(80, '-'),
          result.rjust(80),
          '-'.center(80, '-'), sep='\n')

    return file_img_hash, img_hash_1, c_title, done


def get_hash_from_url(url):
    """
    Функция получения hash изображения по скриншоту сайта
    Функциональность
    """
    if not urlparse(url).scheme:
        url = 'http://%s' % url
    # Если ставить , options='--headless' то скриншоты получаются маленькими
    browser = get_browser_chrome(url, options="--headless")
    # browser = get_browser_chrome(url)
    time.sleep(1)
    img_base64 = browser.get_screenshot_as_base64()
    b_current_url = browser.current_url
    img_hash = get_img_hash(img_base64=img_base64)
    b_title = browser.title
    browser.close()
    browser.quit()

    return img_hash, img_base64, b_title, b_current_url


def get_hash_from_file(file_path=False, img_base64=False):
    """
    Функция получения hash изображения по файлу изображения
    Функциональность
    """
    if file_path:
        if os.path.exists(file_path):
            # TODO: Сделать влзврат не имя файла, а его base64
            file_name = os.path.basename(file_path)
            img_hash = get_img_hash(img_path=file_path)

            return img_hash, file_name, None, None
        else:
            print('Данного файла, нет')
            return None, None, None, None
    else:
        img_hash = get_img_hash(img_base64=img_base64)

        return img_hash, None, None, None


def get_hashes_from_db(node_id, get_data=True, data=None):
    """
    Функция получения list из значений hash_img для указанного node_id
    Функциональность
    """
    if get_data:
        node_data = dict(db_utils.get_db_data(node_id))
    else:
        node_data = data

    db_node_hashes = pickle.loads(
        bytes.fromhex(dict(node_data)['hash_img']))
    return db_node_hashes


def get_img_hash(img_path=False, img_base64=False):
    """
    Получение hash изображения.

    Method (доступные виды хеширования):
        ahash:          Average hash
        phash:          Perceptual hash
        dhash:          Difference hash
        whash-haar:     Haar wavelet hash
        whash-db4:      Daubechies wavelet hash
        colorhash:      HSV color hash
        crop-resistant: Crop-resistant hash

    Функциональность
    """
    HASH_SIZE = 12
    hashes = {}
    # TODO: Если в img будет передаваться путь, нужно обработать такой вариант
    if img_path:
        img_ = Image.open(img_path)
    elif base64:
        img_ = Image.open(BytesIO(base64.b64decode(img_base64)))

    hashes['ahash'] = imagehash.average_hash(img_, hash_size=HASH_SIZE)
    hashes['phash'] = imagehash.phash(img_, hash_size=HASH_SIZE)
    hashes['dhash'] = imagehash.dhash(img_, hash_size=HASH_SIZE)
    hashes['whash'] = imagehash.whash(img_, hash_size=8)
    hashes['whash_db4'] = imagehash.whash(img_, hash_size=8, mode='db4')
    hashes['colorhash'] = imagehash.colorhash(img_, binbits=3)
    hashes['crop_resistant'] = imagehash.crop_resistant_hash(img_)

    return hashes


def get_difference_hash(hash_1, hash_2, info=False):
    """
    Функция возвращает усредненное значение разницы двух хешей
    Функциональность
    """
    hash_data = []
    for key in hash_1.keys():
        dif_data = 100 - abs(hash_1[key] - hash_2[key])
        print('%s -> %s%%' % (key, dif_data)) if info else None
        hash_data.append(dif_data)
    mean = sum(hash_data) / len(hash_data)

    return mean


def add_hash_to_node_db(node_id, img_hash):
    """
    Функция добавления нового hash в данные о node_id в БД.
    Функция проверяет добавляемый хеш на 100% соответсвие, если такое соответсвие
    находится, хеш не добавляется в БД.
    Функциональность
    """
    # Максимальная схожесть для добавления
    max_difference = 97

    print('Обновление материала %s' % node_id)
    if img_hash:
        node_data = dict(db_utils.get_db_data(node_id))

        new_hash = img_hash
        hash_img = pickle.loads(bytes.fromhex(node_data['hash_img']))

        add_do_hashes = True

        for _hash in hash_img:
            if get_difference_hash(_hash, new_hash, info=False) > max_difference:
                add_do_hashes = False
                break

        if add_do_hashes:
            hash_img.append(new_hash)
            node_data['hash_img'] = pickle.dumps(hash_img).hex()
            db_utils.update_to_db(node_data['node_id'], node_data['hash_img'])
        else:
            print('Найдено %s%% соответствие, которое уже есть в таблице.' %
                  max_difference)
    else:
        print('Нет картинки на добавление.')


def remove_hash_img_index_from_node_id(node_id, hash_index=-1):
    """
    Функция удаляет указанный hash_index из списка hash в строке noode в db.
    По умолчанию, удаляется крайний справа элемент списка.
    Функциональность
    """
    breakpoint()
    db_node_hashes = get_hashes_from_db(node_id)
    db_node_hashes.pop(hash_index - 1)
    hash_img = pickle.dumps(db_node_hashes).hex()
    db_utils.update_to_db(node_id, hash_img)


def autorization():
    """
    Функция, которая возвращает авторизированный сеанс браузера, для
    сбора и добавления нового материала.
    Функциональность
    """
    # TODO: Проверить на закрытие браузера, что бы исключить клонирование
    # процессов браузера

    URL = 'https://www.%s/user' % os.getenv('site')
    browser = get_browser_chrome(URL, options='--headless', waite=False)
    # Для отладки раскомментировать
    # browser = get_browser_chrome(URL, waite=False)

    if not os.path.exists(os.path.join('cookie', COOKIE_NAME)):
        print('Нет куки')
    else:
        with open(os.path.join('cookie', COOKIE_NAME), 'r', newline='') as file:
            cookies = json.load(file)

        browser.add_cookie(cookies[0])

    browser.get(URL)

    login_form = browser.find_elements_by_xpath(
        '//form[@class="user-login-form"]')

    if login_form:
        if not TRUST_NAME:
            os.environ['USER_CHECK'] = input('Enter LOGIN: ')
            os.environ['USER_CHECK_PSW'] = input('Enter PSWD: ')
            login_form = login_form[0]
            print('Нужно авторизоваться')
            login = browser.find_element_by_xpath('//input[@id="edit-name"]')
            assert login
            login.send_keys(os.getenv('USER_CHECK'))

            passwd = browser.find_element_by_xpath('//input[@id="edit-pass"]')
            assert passwd
            passwd.send_keys(os.getenv('USER_CHECK_PSW'))

            login_form.submit()

        cookies = browser.get_cookies()

        with open(os.path.join('cookie', COOKIE_NAME), 'w', newline='') as file:
            json.dump(cookies, file)

        if os.getenv('USER_CHECK') in browser.title:
            print('\t-> Авторизован')
            return browser
        else:
            print('\t->Не авторизировано')
            return False
    else:
        print('\t-> Авторизован')
        return browser


def hash_menu(action=None, source=None):
    """
    Функция компоновки отдельных функция для работы в хешами в БД
    """
    while True:
        node_id = input('Введите ID материала в БД: ')
        if node_id.isnumeric():
            node_id = int(node_id)
            node_data = dict(db_utils.get_db_data(node_id))
            if node_data:
                hashes = get_hashes_from_db(node_id, get_data=False,
                                            data=node_data)
                print('\n\t[%s] - %s - Хешей: %s\n' % (node_data['node_id'],
                                                       node_data['title'],
                                                       len(hashes)))
                break
            else:
                print('Такой ID не найден.')
        else:
            print('Не верно указан ID')

    if source == 'url':
        img_hash, *_ = get_hash_from_url(input('Введите URL: '))
    elif source == 'file':
        img_hash, *_ = get_hash_from_file(file_path=input('Введите PATH: '))

    if action == 'add':
        add_hash_to_node_db(node_id,
                            img_hash)
    elif action == 'delete':
        remove_hash_img_index_from_node_id(node_id,
                                           hash_index=int(input('Введите index хэша: ')))


def add_new_to_db(url):
    """
    Функция добавления новых записей в БД по URL.
    """

    hash_img, *_ = get_hash_from_url(url)
    hash_img = pickle.dumps([hash_img]).hex()
    node_id = input('Введите id: ')
    title = input('Введите название: ').replace('"', '""')
    db_utils.save_to_db((node_id, title, 'https://www.%s' % os.getenv('site'),
                         'none', hash_img))


def get_done_urls(column, url):
    """
    Функция возвращает True если url найдены, в противном случае, вернет False.
    """
    pattern = re.compile(r'http(s)?:\/\/|www.|\/$|\/\.$')
    url = re.sub(pattern, '', url)
    result = db_utils.get_checks(column, url)
    return True if result else False


def get_need_done_urls(url):
    """
    Функция возвращает True если url уже находится в ожидании выполнения, в
    противном случае вернет False
    """
    pattern = re.compile(r'http(s)?:\/\/|www.|\/$|\/\.$')
    url = re.sub(pattern, '', url)
    result = db_utils.get_need_done(url)
    return True if result else False


def get_all_need_done():
    """
    Функция возвращает полный список данных из БД need_done
    """
    return db_utils.get_all_need_done()


def find_urls(text, black_list=False):
    """
    Функция поиска ссылок в тексте.
    TODO: Разобраться как работает модуль urlextract. Реализовать самостоятельно
    """
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': True,
    })
    extractor = URLExtract()

    _urls = extractor.find_urls(text)
    urls = []

    if black_list:
        for _url in _urls:
            # Поиск не желательных цифр в начале домена.
            # Например 6.example.com, 13.example.com
            _url = re.sub(r'^((\d){1,2}\.)', '', _url)
            find = False
            for black in black_list:
                if black.lower() in _url.lower():
                    find = True
                    break

            if not find:
                urls.append(_url.lower())
    else:
        urls = _urls

    return urls


def get_site_load(img_base64, url):
    """
    Функция открытия сайта в браузере и вывода меню работы с контентом сайта
    """
    pages = ['https://www.%s/search/content?keys=%s' %
             (os.getenv('site'), re.sub(r'\/.*', '', url))]

    if img_base64:
        img = Image.open(BytesIO(base64.b64decode(img_base64)))
        img.show()
        pages.append(url)
    try:
        if len(pages) > 1:
            br_show = get_browser_chrome(pages[1], options='--incognito')
            br_show.execute_script("window.open('');")
            br_show.switch_to.window(br_show.window_handles[1])
            br_show.get(pages[0])
        else:
            br_show = get_browser_chrome(pages[0], options='--incognito')
        br_show.switch_to.window(br_show.window_handles[0])
    except Exception as err:
        """Какие то ошибки при загрузки демо вкладок"""
        print('Возникла ошибка: %s' % err)
        br_show = get_browser_chrome(pages[0], options='--incognito')

    return br_show


def save_to_need_done(domain, url, project, url_title,
                      simular_search, simular_db, img_hash, webform):
    """
    Функция сохраняет данные об URL, которые необходимо будет добавить после
    сбора.
    """
    simular_search = json.dumps(simular_search, ensure_ascii=False)
    simular_db = json.dumps(simular_db, ensure_ascii=False)
    pattern = re.compile(r'http(s)?:\/\/|www.|\/$|\/\.$')
    url = re.sub(pattern, '', url)
    domain = re.sub(pattern, '', domain)
    db_utils.add_need_done(domain, url, project, url_title,
                           simular_search, simular_db, img_hash, webform)


def save_to_checks(url, status, note):
    """
    Функция добавления домена, url и статуса в БД
    """
    # FIXME: Для чего 2 раза обрабатывать domain?
    domain = utils.get_domain(url)
    pattern = re.compile(r'http(s)?:\/\/|www.|\/$|\/\.$')
    url = re.sub(pattern, '', url)
    domain = re.sub(pattern, '', domain)
    db_utils.add_checks(domain, url, status, note)


def try_find_it(urls_list, debugger=False, recheck=False):
    """
    Функция поиска данных об url. Принимает список urls_list
    в ходе проверки сохраняет сайты в соответсвующие файлы.

    Возвращает -> список списков с данными проверенных URL
    :domain: -> str - домен, который ищет на сайте
    :find_projects_site: -> список словарей найденных на сайте
                            [название проекта, ID проекта]
    :file_img_base64: -> str - строка base64 скриншота
    :img_hashes: -> список словарей хешей
    :title: -> str - строка заголовка проверяемого URL
    :find_projects_db: -> - словарь словарей найденных похожих проектов в БД
    """
    # TODO: Сделать обработку поссылочно, а не списком
    need_done = []
    for number, url_s in enumerate(urls_list, 1):
        (domain, url_s, find_projects_site,
         file_img_base64, img_hashes,
         title, find_projects_db, error) = (utils.get_domain(url_s),
                                            url_s, [], None, [],
                                            None, {}, None)
        print('\n', '[%s/%s] %s' % (number, len(urls_list), url_s))
        if (not get_done_urls('url', url_s) and not
                get_need_done_urls(url_s)) or recheck:
            if not get_need_done_urls(url_s):
                try:
                    # Поиск на ресурсах
                    domain, find_projects_site = find_on_search_site(url_s)
                    try:
                        (file_img_base64,
                            img_hashes,
                            title,
                            find_projects_db) = find_simular_db_from_url(url_s)
                    except common.exceptions.TimeoutException as err:
                        print('\n', '=' * 80, sep='')
                        print('Долгая загрузка: %s' % (err))
                        print('=' * 80, sep='')
                        error = err
                except common.exceptions.WebDriverException as err:
                    print('\n', '=' * 80, sep='')
                    print('Ошибка загрузки %s: %s' % (url_s, err))
                    print('=' * 80, sep='')
                    error = err
                if get_done_urls('url', url_s):
                    error = 'in done'
            else:
                error = 'need done'
            # Если страница не найдена с схожестью больше 98%, значит сайт не
            # добавлять в дальнейшую обработку.
            if not (1 in find_projects_db.keys() and find_projects_db[1][0] > 98):
                need_done.append([domain, url_s, find_projects_site,
                                  file_img_base64, img_hashes,
                                  title, find_projects_db, error])

        else:
            if debugger:
                print('\n', '[%s] %s' % (number, url_s))
                line_ = '-'.center(80, '-')
                head_ = ' Уже проверял! '.center(80)
                print('-'.center(80, '-'))
                print('%s\n\n%s\n\n%s' % (line_, head_, line_))
    return need_done


def send_webform(link, data):
    """
    Функция, которая отправляет данные результата обработки вебформы
    на сайт.

    link - ссылка на вебформу
    data - данные для заполнения вебформы
    """
    title = get_response(url='https://www.%s/user' %
                         os.getenv('site'),
                         cookies=True).html.find('title',
                                                 first=True).text
    if 'Пользователь' in title:
        webform_data = get_response(url=link, cookies=True)

        check_name = webform_data.html.xpath(
            '//input[@id="edit-check-name"]', first=True).attrs['value']
        check_email = webform_data.html.xpath(
            '//input[@id="edit-check-email"]', first=True).attrs['value']
        url_sites = webform_data.html.xpath(
            '//input[@id="edit-url-sites"]', first=True).attrs['value']

        status = webform_data.html.xpath(
            '//div[contains(@class,"js-form-type-radio")]/input[@checked="checked"]',
            first=True)
        project_review = webform_data.html.xpath(
            '//input[@name="project_review"]', first=True)

        # Если статус не установлен и не установлен проект, создаем словарь запроса
        if not (status and project_review):
            status = data['status']
            project_review = data['title']
        elif not status:
            status = data['status']
            project_review = project_review.attrs['value']
        elif not project_review:
            status = status.attrs['value']
            project_review = data['title']

        form_build_id = webform_data.html.xpath(
            '//input[@name="form_build_id"]', first=True).attrs['value']
        form_token = webform_data.html.xpath(
            '//input[@name="form_token"]', first=True).attrs['value']
        form_id = webform_data.html.xpath(
            '//input[@name="form_id"]', first=True).attrs['value']
        _triggering_element_name = 'op'
        _triggering_element_value = 'Сохранить'
        _drupal_ajax = 1

        post_data = {
            'check_name': check_name,
            'check_email': check_email,
            'url_sites': url_sites,
            'status': status,
            'project_review': project_review,
            'form_build_id': form_build_id,
            'form_token': form_token,
            'form_id': form_id,
            '_triggering_element_name': _triggering_element_name,
            '_triggering_element_value': _triggering_element_value,
            '_drupal_ajax': _drupal_ajax
        }
        send_webform_data = get_response(method='POST', url=link + '?ajax_form=1&_wrapper_format=drupal_ajax',
                                         cookies=True, data=post_data)
        if 'Form validation errors' not in send_webform_data.text:
            return True
        else:
            return False
    else:
        print('Не авторизован')
        return False
