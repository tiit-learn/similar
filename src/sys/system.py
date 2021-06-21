import base64
import datetime
import json
import os
import re
import requests_html
import time
from urllib import parse

from concurrent import futures
from io import BytesIO
from requests.exceptions import SSLError

from src.utils.deco import timer
from src.const import *
from src.utils import *
from src.menus import menus

from ..const.constants import TOTAL_PAGES


def update_project(node_id, add_url, more_data=False):
    """
    Функция добавляющая информацию в проекте. Если установлен флаг на more_data
    будет вызвана функция генерации данных для проекта и добавлены к уже
    существующим.
    Меняет только данные в проекте на сайте, не трогает БД!
    Возвращает данные для добавления в БД

    Бизнес логика.
    """

    # TODO: Заменить импортирование модуля на импорт модуля src.utils.funcs
    #       оттуда взять функцию на получение сессии.

    url = 'https://www.%s/node/%s/edit' % (os.getenv('site'), node_id)
    headers = {'accept': 'text/html,application/xhtml+xml,application/xml;'
               'q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-'
               'exchange;v=b3;q=0.9',
               'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
               ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192'
               ' Safari/537.36 OPR/74.0.3911.218'}

    session = requests_html.HTMLSession()
    session.headers.update(headers)
    # Доступ к редактированию получает по cookie
    with open(os.path.join('cookie', COOKIE_NAME)) as file:
        for cookie in json.loads(file.read()):
            session.cookies.set(cookie['name'], cookie['value'])

    resp = session.get(url)

    _form_build = resp.html.xpath(
        '//input[@name="form_build_id"]', first=True).attrs['value']
    _form_token = resp.html.xpath(
        '//input[@name="form_token"]', first=True).attrs['value']
    _title = resp.html.xpath(
        '//input[@id="edit-title-0-value"]', first=True).attrs['value']
    _field_category = resp.html.xpath(
        '//input[@id="edit-field-category-target-id-value-field"]', first=True).attrs['value']
    _field_image_alt = resp.html.xpath(
        '//input[@id="edit-field-image-0-alt"]', first=True).attrs['value']
    _field_image_fids = int(resp.html.xpath(
        '//input[@name="field_image[0][fids]"]', first=True).attrs['value'])
    _body_value = resp.html.xpath(
        '//textarea[@name="body[0][value]"]', first=True).text
    _field_other_title = resp.html.xpath(
        '//input[@name="field_other_title[target_id][value_field]"]', first=True).attrs['value']
    _field_project_links = resp.html.xpath(
        '//input[@name="field_project_links[target_id][value_field]"]',
        first=True).attrs['value']
    _field_project_emails = resp.html.xpath(
        '//input[@name="field_project_emails[target_id][value_field]"]',
        first=True).attrs['value']
    _field_project_addresses = resp.html.xpath(
        '//input[@name="field_project_addresses[target_id][value_field]"]',
        first=True).attrs['value']
    _field_project_telephones = resp.html.xpath(
        '//input[@name="field_project_telephones[target_id][value_field]"]',
        first=True).attrs['value']

    data = {
        'changed': int(time.time()),
        'title[0][value]': _title,
        'form_build_id': '%s' % _form_build,
        'form_token': '%s' % _form_token,
        'form_id': 'node_project_edit_form',
        'field_category[target_id][value_field]': _field_category,
        'field_image[0][alt]': _field_image_alt,
        'field_image[0][fids]': _field_image_fids,
        'field_image[0][display]': 1,
        'field_rating_post[0][value]': 3,
        '%s' % os.getenv('PRIVATE_FIELD'): 'basic_html',
        'body[0][value]': _body_value,
        'body[0][format]': 'basic_html',
        'field_other_title[target_id][value_field]': _field_other_title,
        'field_project_links[target_id][value_field]': _field_project_links,
        'field_project_emails[target_id][value_field]': _field_project_emails,
        'field_project_addresses[target_id][value_field]':
        _field_project_addresses,
        'field_project_telephones[target_id][value_field]':
        _field_project_telephones,
        'field_project_people[0][_weight]': 0,
        'field_for_author[0][format]': 'basic_html',
        'advanced__active_tab': 'edit-path-0',
        'op': 'Сохранить',

    }

    # Если more_data, значит нужно указывать дополнительные данные
    if more_data:
        node_data = node_data_generator(add_url)
        data['field_other_title[target_id][value_field]'] = \
            data['field_other_title[target_id][value_field]'] + \
            data_list(node_data['names'])
        data['field_project_links[target_id][value_field]'] = \
            data['field_project_links[target_id][value_field]'] + \
            data_list(node_data['links'])
        data['field_project_emails[target_id][value_field]'] = \
            data['field_project_emails[target_id][value_field]'] + \
            data_list(node_data['email'])
        data['field_project_addresses[target_id][value_field]'] = \
            data['field_project_addresses[target_id][value_field]'] + \
            data_list(node_data['addresses'])
        data['field_project_telephones[target_id][value_field]'] = \
            data['field_project_telephones[target_id][value_field]'] + \
            data_list(node_data['phones'])

    add_url = re.sub(r'https|http|://|www.|/.*', '', add_url)

    # если нет add_url в существующем списке url -> data['field_project_links']
    # тогда добавляем новый.
    if add_url not in data['field_project_links[target_id][value_field]']:
        data['field_project_links[target_id][value_field]'] = \
            data['field_project_links[target_id][value_field]'] + \
            ' ""%s""' % add_url
    resp = session.post(url, data=data)

    if 'edit' not in resp.url:
        node_id = resp.url.split('/')[-1]
        url = resp.url

        repl = re.compile(r'.webp.*|styles/max_325x325/public/')
        img = resp.html.find('.field--name-field-image',
                             first=True).find('img', first=True).attrs['src']
        img = ('https://www.%s' % os.getenv('site')) + re.sub(repl, '', img)
        return (node_id, _title, url, img)
    else:
        print(resp.html.find('.alert-dismissible', first=True).text)
        os.makedirs('errors', exist_ok=True)
        with open(os.path.join('errors', '%s_error.html' % add_url), 'w') as file:
            file.write(resp.text)
        return False


def new_project(img_name, img, url_site):
    """
    Функция добавления нового проекта. Добавляет только на сайт и возвращает
    данные для добавления в БД!
    Бизнес логика.

    TODO: Добавление переданного URL автоматически, если не установлено другое
    значение в поле ссылок.
    """
    node_data = node_data_generator(url_site)

    url = 'https://www.%s/add-project' % os.getenv('site')
    headers = {'accept': 'text/html,application/xhtml+xml,application/xml'
               ';q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-'
               'exchange;v=b3;q=0.9',
               'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
               ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192'
               ' Safari/537.36 OPR/74.0.3911.218'}

    session = requests_html.HTMLSession()
    session.headers.update(headers)
    with open(os.path.join('cookie', COOKIE_NAME)) as file:
        for cookie in json.loads(file.read()):
            session.cookies.set(cookie['name'], cookie['value'])

    resp = session.get(url)
    _form_build = resp.html.xpath(
        '//input[@name="form_build_id"]', first=True).attrs['value']
    _form_token = resp.html.xpath(
        '//input[@name="form_token"]', first=True).attrs['value']

    post_url = 'https://www.%s/add-project?element_parents=field_image/'\
        'widget/0&ajax_form=1&_wrapper_format=drupal_ajax' % os.getenv('site')
    session.headers.update(
        {'accept': 'application/json, text/javascript, */*; q=0.01'})

    data = {
        'changed': int(time.time()),
        'form_build_id': '%s' % _form_build,
        'form_token': '%s' % _form_token,
        'form_id': 'node_project_form',
        '_triggering_element_name': 'field_image_0_upload_button',
        '_triggering_element_value': 'Закачать',
        '_drupal_ajax': 1}

    # TODO: РАЗОБРАТЬСЯ С ПЕРЕДАЧЕЙ ФАЙЛА ИЗ base64
    resp_img = session.post(post_url, data=data, files={
                            "files[field_image_0]": (img_name,
                                                     BytesIO(base64.b64decode(img)), 'image/png')})

    img_html = requests_html.HTML(html=json.loads(resp_img.text)[3]['data'])
    img_id = img_html.xpath(
        '//input[@name="field_image[0][fids]"]', first=True).attrs['value']

    if len(node_data['names']) < 1:
        raise TypeError('Не достаточно названий')

    title_n = node_data['names'][0]

    data = {
        'changed': int(time.time()),
        'title[0][value]': title_n,
        'form_build_id': '%s' % _form_build,
        'form_token': '%s' % _form_token,
        'field_image[0][alt]': '%s отзывы и обзор. Развод, лохотрон или'
        ' правда. Только честные и правдивые отзывы на %s' % (title_n,
                                                              os.getenv('site').title()),
        'field_image[0][fids]': img_id,
        'field_image[0][display]': 1,
        'form_id': 'node_project_form',
        'body[0][value]': '%s' % node_data['description'],
        'field_category[target_id][value_field]': '%s' %
        data_list(node_data['categories']),
        'field_other_title[target_id][value_field]': '%s' %
        data_list(node_data['names']),
        'field_project_links[target_id][value_field]': '%s' %
        data_list(node_data['links']),
        'field_project_emails[target_id][value_field]': '%s' %
        data_list(node_data['email']),
        'field_project_addresses[target_id][value_field]': '%s' %
        data_list(node_data['addresses']),
        'field_project_telephones[target_id][value_field]': '%s' %
        data_list(node_data['phones']),
        'status[value]': 1,
        'op': 'Сохранить'
    }
    resp = session.post(url, data=data)

    if title_n in resp.html.find('title', first=True).text:
        node_id = resp.url.split('/')[-1]
        url = resp.url
        # Проверка возможности обработки с r''
        repl = re.compile(r'.webp.*|styles/max_325x325/public/')
        img = resp.html.find('.field--name-field-image',
                             first=True).find('img', first=True).attrs['src']
        img = ('https://www.%s' % os.getenv('site')) + re.sub(repl, '', img)

        return (node_id, title_n, url, img)
    else:
        print(resp.html.find('.alert-dismissible', first=True).text)
        os.makedirs('errors', exist_ok=True)
        with open(os.path.join('errors', 'html-error.html'), 'w') as file:
            file.write(resp.text)
        return False


def adding_to_db(results, webforms=[[]], project='system'):
    """
    Функция обработки результатов и отправка на добавление в БД.
    """
    # TODO: Добавить проверку на доступность страницы, что бы исключить не
    #       работающие.
    # TODO: Не добавлять результаты поиска на сайте, и поиска в БД. Производить
    #       эту проверку по факту проверки. Сохранять только base64 картинку
    if results:
        for result in results:
            if result[-1] and result[-1] != 'in done' and result[-1] != 'need done':
                save_to_checks(result[1], False, result[-1])
            elif result[-1] == 'in done':
                print(result[1], 'In Done DB')
            elif result[-1] == 'need done':
                print(result[1], 'In Need Done DB')
            else:
                save_to_checks(result[1], True, '')
            # Если есть картинка или webforma и ошибка не равна 'need done'
            if ((result[3] or webforms[0]) and result[-1] != 'need done'):
                for webform in webforms:
                    if (webform and webform[0] == result[1]) or not webform:
                        save_to_need_done(result[0], result[1],
                                          project, result[5],
                                          result[2], result[6],
                                          result[3], '' if not webform else webform[-1])
                        break
    else:
        print('Нет доступных результатов проверки.')


@timer
def site_data_need_check():
    """
    Функция проверки отправленных заявок.
    Бизнес логика
    """
    resp = get_response(url='https://www.%s/checkit/sites' % os.getenv('site'))
    raw_list = resp.html.xpath('//td[3][text()="- "]')
    print(' Отправленные заявки '.center(80, '='))
    links_in_webforms = []
    webforms_link = []
    if raw_list:
        # Создание вкладок для работы
        print(' Авторизация '.center(80, '='))
        browser = autorization()
        if not browser:
            return False
        # TODO: Заменить selenium на requests
        browser.get('https://www.%s/checkit/sites' % os.getenv('site'))
        raw_list = browser.find_elements_by_xpath('//tr[td="- "]')
        # Вкладки для работы. Возможно стоит уменьшить
        for i in range(3):
            browser.execute_script("window.open('');")
        for n, raw in enumerate(raw_list[::-1], 1):
            # Вкладка с главной страницы
            browser.switch_to.window(browser.window_handles[0])
            edit = raw.find_elements_by_xpath(
                'td')[3].find_element_by_tag_name('a').get_attribute('href')
            # Вкладка с страницей редактирования отправленной формы
            browser.switch_to.window(browser.window_handles[1])
            browser.get(edit)
            need_done = browser.find_element_by_xpath(
                '//form[contains(@class, "webform-submission-form")]')
            author = need_done.find_element_by_xpath(
                '//input[@data-drupal-selector="edit-check-name"]').get_attribute('value')
            author_email = need_done.find_element_by_xpath(
                '//input[@data-drupal-selector="edit-check-email"]').get_attribute('value')
            need_check = need_done.find_element_by_xpath(
                '//input[@data-drupal-selector="edit-url-sites"]').get_attribute('value')
            desription = need_done.find_element_by_xpath(
                '//textarea[@data-drupal-selector="edit-datails-info"]').get_attribute('value')
            print('Номер заявки:', n)
            print(' Данные отправителя '.center(80, '-'))
            print('\tАвтор: %s\n\tПочта: %s\n\tОписание: %s\n\n\tСайт: %s\n' % (
                author,
                author_email,
                desription if len(
                    desription) > 1 else '-',
                need_check))
            pattern = re.compile(r'http(s)?:\/\/|www.|\/$')
            need_check = re.sub(pattern, '', need_check)
            links_in_webforms.append(need_check)
            webforms_link.append((need_check, edit))
            browser.switch_to.window(browser.window_handles[3])
            browser.switch_to.window(browser.window_handles[1])
        try:
            results = try_find_it(links_in_webforms, recheck=True)
        except Exception as err:
            # TODO: Обдумать как выводить форму заявки, если сайт
            # не загрузился
            print('Ошибка в results')

        # Что бы успело сохраниться.
        time.sleep(1)
        browser.quit()

        adding_to_db(results, webforms_link)
    else:
        print('\n', 'Нет заявок!'.center(80), '\n')


@timer
def check_sites(need_site='all'):
    """
    Функция обработки проектов. Функция указывает какие проекты необходимо
    проверить.

    Если в :need_site: указать определенное название, функция выполнит только
    указанный проект.
    """
    from ..sys import (mmgp_forex)

    SITES_PROJECT = {'mmgp_forex': mmgp_forex,
                     }

    sites = SITES_PROJECT
    need_site = need_site.lower()
    # TODO: Сделать многопоточную обработку каждого проекта
    if need_site == 'all':
        for site in sites:
            # Вывод заголовка сайта
            title = ' Получение сайтов с [%s] ' % site
            print(title.center(80, '='))
            # Вызов модуля сайта
            results = sites[site].start()
            if results:
                adding_to_db(results, project=site)
    else:
        if need_site in sites:
            title = ' Получение сайтов с [%s] ' % sites[need_site]
            print(title.center(80, '='))
            results = sites[need_site].start()
            if results:
                adding_to_db(results, project=need_site)
        else:
            print('Проект для обработки не найден.')


def collect_all(pages_done=TOTAL_PAGES, first_page=0):
    """
    Функция сбора данных со всех страниц указанных в pages_done
    Бизнес логика
    """
    if not os.path.exists(DB_NAME):
        logging.info('Создаю БД [%s]' % DB_NAME)
        new_db(DB_NAME, 'nodes', '''node_id INTEGER PRIMARY KEY,
                            title    TEXT NOT NULL,
                            url      TEXT,
                            img      TEXT,
                            hash_img BLOB''')
        new_db(DB_NAME, 'checks', '''id INTEGER PRIMARY KEY AUTOINCREMENT,
                                     domain TEXT,
                                     url    TEXT UNIQUE,
                                     status BOOLEAN,
                                     note   TEXT''')
        new_db(DB_NAME, 'need_done', '''id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        domain         TEXT,
                                        url            TEXT UNIQUE,
                                        project        TEXT,
                                        url_title      TEXT,
                                        simular_search TEXT,
                                        simular_db     TEXT,
                                        img_hash       BLOB,
                                        webform        TEXT''')
    if not os.path.exists(TEMP_DIR):
        logging.info('Создаю временную папку [%s]' % TEMP_DIR)
        os.makedirs(TEMP_DIR, exist_ok=True)

    link = 'https://www.%s/project?page=' % os.getenv('site')
    pages = (link + str(page) for page in range(first_page,
                                                first_page + pages_done))
    ex = futures.ThreadPoolExecutor(max_workers=20)

    to_do = [ex.submit(get_data, i) for i in pages]

    page_count = 0
    node_count = 0
    for f in futures.as_completed(to_do):

        page_count += 1
        for data_tuple in f.result():
            if data_tuple:
                node_count += 1

    print('=' * 80)
    print('Пройдено страниц %s' % page_count)
    print('Загружено материалов %s' % node_count)


def work_with_url(url, action=False):
    """
    Функция обрабатываем переданный ей URL
    Собирает данные и вызывает меню обработки.
    Бизнес логика
    """
    # TODO: Разобраться с функцией
    find_on_search_site(url)

    file_img_hash, img_hash = find_simular_db_from_url(url)

    menus.draw_actions(url=url,
                       img=file_img_hash,
                       img_hash=img_hash)


@ timer
def find_simular_in_db(differ=80):
    """
    Функция поиска дубликатов в БД.

    for data_2 in all_data[node_count + 1:]: - определяет логику поиска,
    стоит ли искать в уже пройденных.
    Бизнес логика
    """
    header = ' Идентичность: %s ' % differ
    print(header.center(80, '='))
    all_data = all_db_data()
    number_node = 0

    # Берем каждую строку в БД
    for number, data_1 in enumerate(all_data):
        # Список найденных соответсвий по устновленному параметру differ
        find_data = []
        # Берем каждую последующую строку в БД
        for data_2 in all_data[number_node + 1:]:
            # for data_2 in all_data:
            # Получение словарей хешей для первичной и вторичной строки.
            img_hashes_1 = pickle.loads(bytes.fromhex(data_1[-1]))
            img_hashes_2 = pickle.loads(bytes.fromhex(data_2[-1]))
            # Для каждой первичной строки, извлекаем список хешей
            for img_hash_1 in img_hashes_1:
                # Устанавливаем счетчик для подсчета сравниваемых строк.
                # Т. е. для каждой новой итерации хешей первичной строки,
                # будет сбрасываться счетчик, что бы понимать, какой хеш
                # совпадает с каким. Для выявления дублей.
                hash_num = 0
                # Для каждой вторичной строки, извлекаем список хешей
                for img_hash_2 in img_hashes_2:
                    def_i = get_difference_hash(img_hash_1, img_hash_2)
                    hash_num += 1
                    if def_i > differ:
                        if data_1[0] != data_2[0]:
                            find_data.append((def_i,
                                              data_2[0],
                                              data_2[1],
                                              data_2[2],
                                              len(img_hashes_2),
                                              hash_num))
        if find_data:
            print('[#%s] %s - %s - %s (%s)' % (number,
                                               data_1[0],
                                               data_1[1],
                                               data_1[2],
                                               len(img_hashes_1)))
            find_data.sort(key=lambda x: x[0], reverse=True)
            for data_2 in find_data:
                print('\t(%.2f %%) %s - %s - %s (%s/%s)' % (data_2[0],
                                                            data_2[1],
                                                            data_2[2],
                                                            data_2[3],
                                                            data_2[-2],
                                                            data_2[-1]))
        number_node += 1


def get_hash_list(hash_list):
    return pickle.loads(bytes.fromhex(hash_list))


def check_title(data):

    data_id, data_title, data_url = data[:3]
    if data_id not in [0, 1, 2]:
        resp = get_response(url=data_url)
        _title = resp.html.find('title', first=True).text[:-54].strip()

        if resp.status_code != 200:
            if resp.status_code == 404:
                return('delete', data_url, None, data_title, None)
        if resp.url != data_url:
            return('redirect', data_url, resp.url, data_title, None)
        if _title != data_title:
            return('change title', data_url, resp.url, data_title, _title)
    return('unknown', data_url, None, data_title, None)


@ timer
def check_db_data(node_id=''):
    # Функция проеврки данных в БД
    if not node_id.isdigit():
        print("Проверка всех материалов в БД.")
        all_data = all_db_data()
    else:
        print("Проверка id матриала %s" % node_id)
        if get_db_data(node_id):
            all_data = dict(get_db_data(node_id))
            all_data = [(all_data['node_id'],
                         all_data['title'],
                         all_data['url'],
                         all_data['img'],
                         all_data['hash_img'])]
        else:
            print('Такого проекта нет.')
            return False

    ex = futures.ThreadPoolExecutor(max_workers=20)
    to_do = [ex.submit(check_title, data) for data in all_data[:]]

    for data_done in futures.as_completed(to_do):
        data = data_done.result()

        if data[1]:
            old_node_id = data[1].split('/')[-1]
        else:
            old_node_id = None

        if data[2]:
            new_node_id = data[2].split('/')[-1]
        else:
            new_node_id = None

        old_title = data[-2]
        new_title = data[-1]

        if data[0] == 'change title':
            print('[%s] - %s -> %s' % (old_node_id, old_title, new_title))
            update_to_db_cell(old_node_id, 'title', new_title)
        elif data[0] in ['redirect', 'delete']:
            print('\n\t[%s] Действие для %s\n' % (old_node_id,
                                                  data[0]))

            headline = '%s %s %s' % (old_node_id,
                                     data[0],
                                     new_node_id)
            menus.project_check_menu(headline, old_node_id, new_node_id)


def get_from_other_site(nodes_data_xpath,
                        node_data_xpath,
                        SITES, PAGINATOR,
                        BLACK_URLS,
                        page_count=1,
                        verify=True,
                        debugger=False):
    """
    Функция инициализации обработки сайта для сбора необходимой информации.
    """
    session = requests_html.HTMLSession()
    header = {
        'accept': 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4507.0 Safari/537.36'}
    """
    Получение ранее пройденных URL
    """
    find_url = []
    n = 0

    BLACK_URLS = BLACK_URLS + \
        list((map(lambda x: x.strip(), os.getenv('GLOBAL_BLACK_URLS').split(','))))
    for SITE in SITES:
        for page in reversed(range(1, page_count + 1)):

            # Обход каждой страницы, по указанному кол-ву страниц.
            url_ = '%s%s' % (SITE, PAGINATOR % page)

            # FIXME: Разобраться, почему отваливается сертификат.
            resp = session.get(url_, verify=verify, timeout=20, headers=header)
            print(resp.html.find('title', first=True).text.center(80))
            print(''.center(80, "-"))
            nodes_data = resp.html.xpath(nodes_data_xpath)
            # TODO: Сделать асинхронность или конкурентность. Для быстрого
            # обхода страниц сайтов.

            for n, data in enumerate(nodes_data[::-1], n + 1):
                # Обход каждого тизера материала. Проверка каждого тизера
                # на наличие URL

                _temp = []
                urls = set(find_urls(data.text, BLACK_URLS))
                if not urls:
                    # Если ссылки не найдены в тизере, попробовать поиск
                    # в основном теле документа.

                    node_url = data.xpath('//a', first=True)
                    if node_url:
                        node_url = node_url.attrs['href']
                    else:
                        continue

                    # Если нет домена в найденом URL на материал
                    if not parse.urlparse(node_url).netloc:
                        node_url = parse.urljoin('%s://%s' % (
                            parse.urlparse(SITE).scheme or 'http',
                            parse.urlparse(SITE).netloc),
                            node_url)

                    try:
                        try:
                            node_resp = session.get(
                                node_url, verify=True, timeout=20)
                        except SSLError:
                            print('Нужен сертификат %s' % (node_url))
                            node_resp = session.get(
                                node_url, verify=False, timeout=20)
                    except Exception as e:
                        print('Ошибка с %s (%s)' % (node_url, e))
                        continue

                    # Получить фактический домен загруженной страницы
                    scheme = parse.urlparse(node_resp.url.lower()).scheme
                    domain = (parse.urlparse(node_resp.url.lower()).netloc if
                              scheme else parse.urlparse(
                        ('http://' + node_resp.url).lower()).netloc)

                    # Если домен не в найденных, не в сделанных и не в
                    # первой загруженной странице. То добавить его как
                    # найденный
                    done_urls = get_done_urls("domain", domain)
                    need_done_url = get_need_done_urls(domain)
                    if (domain not in find_url and not done_urls and domain not in
                            BLACK_URLS and not need_done_url):
                        find_url.append(domain.lower())
                        _temp.append(domain.lower())

                    # Получить весь текст с страницы.
                    try:
                        node_data = node_resp.html.xpath(node_data_xpath,
                                                         first=True)

                        node_text = ('%s %s %s') % (node_url,
                                                    node_resp.url,
                                                    node_data.text if node_data else '')
                        # TODO: Возможно стоит удалить эту реализацию проверки черного
                        #       списка, так как реализовано в find_urls. Проверить остальные
                        #       WP проекты.
                        for black in BLACK_URLS:
                            node_text = node_text.replace(black, '')

                        urls = set(find_urls(node_text, BLACK_URLS))
                        # urls.append(node_resp.url)
                        # breakpoint()
                        if urls:
                            for url in urls:
                                url = url.replace(',', '')
                                scheme = parse.urlparse(url.lower()).scheme
                                url_domain = (parse.urlparse(url.lower()).netloc if
                                              scheme else parse.urlparse(
                                    ('http://' + url).lower()).netloc)
                                _url_temp = re.sub(
                                    r'http(s)?:\/\/|www\.', '', url)
                                done_urls = get_done_urls("url", _url_temp)
                                need_done_url = get_need_done_urls(_url_temp)
                                if (url_domain not in find_url and not
                                        done_urls and domain not in url and not
                                        need_done_url):
                                    find_url.append(url.lower())
                                    _temp.append(url.lower())
                            # print('#%s' % n, 'Необходимо добавить URL %s из %s' %
                            #       (_temp, urls))
                    except Exception as err:
                        print('Ошибка с %s: %s' % (domain, err))
                else:
                    _temp = []
                    for url in urls:
                        url = url.replace(',', '')
                        scheme = parse.urlparse(url.lower()).scheme
                        url_domain = (parse.urlparse(url.lower()).netloc if
                                      scheme else parse.urlparse(
                            ('http://' + url).lower()).netloc)
                        done_urls = get_done_urls("url", url)
                        done_domain = get_done_urls("domain", url_domain)
                        need_done_url = get_need_done_urls(url)
                        if ((url_domain not in find_url or len(url) > len(find_url[find_url.index(url_domain)])) and not
                                done_urls and not done_domain and not need_done_url):
                            find_url.append(url.lower())
                            _temp.append(url.lower())
                    # print('#%s' % n, 'Необходимо добавить URL %s из %s' %
                    #       (_temp, urls))
    if find_url:
        print("Найдено URL - %s" % len(find_url[:]))
        return try_find_it(list(set(find_url[:])))
    else:
        print('\n', 'Нет сайтов!'.center(80), '\n')
        return False


def cli_need_done():
    """
    Функция для обработки информации в БД через CLI.
    Поочередно обрабатывает каждую строку БД в таблице need_done.

    В первую очередь обрабатывает строки, содержащие Webform, которые
    осортированы по ID в порядке возрастания.
    """
    need_done_datas = get_all_need_done()
    for num, data in enumerate(need_done_datas, 1):
        (data_id, domain, url, project, url_title,
         simular_search, simular_db, img_base64, webform) = data
        simular_search = json.loads(simular_search)
        simular_db = json.loads(simular_db)
        if img_base64 == 'None':
            img_base64 = ''
        print(('=== [%s/%s] === ID [%s] - %s ' %
               (num, len(need_done_datas),
                data_id, url)).center(80, '='))
        if webform:
            # Получение данных фебформы
            print('\t\t-', '%s' % webform)
            print(''.center(80, '-'))
        print('')
        print('\t\t-', 'Источник:'.ljust(20), '%s' % project)
        print('\t\t-', 'Заголовок:'.ljust(20), '%s' % url_title)
        print('\t\t-', 'Домен:'.ljust(20), '%s' % domain)
        print('\t\t-', 'URL:'.ljust(20), '%s' % url)
        print('\t\t-', 'Размер скриншота:'.ljust(20),
              '%.2f kb' % (len(img_base64) / 1024))

        # TODO: Сделать поиск актуальных на момент выгрузки
        if simular_search:
            print('\t\t-', 'Поиск на сайте:\n')
            for find in simular_search:
                print('\t\t\t-', '[%s] - %s' % (find[1], find[0]))
            print('')
        if simular_db:
            print('\t\t-', 'Поиск в БД:\n')
            simular_db = {x: y for x, y in sorted(
                simular_db.items(), key=lambda i: i[1][0], reverse=True)}
            for find in simular_db.keys():
                print('\t\t\t-',
                      '[%s] - [%.2f%%] - %s (%s/%s)' % (
                          simular_db[find][1],
                          float(simular_db[find][0]),
                          simular_db[find][2],
                          simular_db[find][-2],
                          simular_db[find][-1]))
        # TODO: Сделать возврат base64 в переменную img_hash
        find_on_search_site(domain)
        find_simular_db_from_file(img_base64=img_base64)
        print('')

        date_now = datetime.datetime.now().strftime('%d_%m_%Y_%H_%m')
        if img_base64:
            img_name = 'project_review_%s_%s.png' % (domain.lower(), date_now)
        else:
            img_name = False

        img_hash = get_img_hash(img_base64=img_base64)
        browser_data = get_site_load(img_base64, url)
        # Отрисовка основного меню, для обработки строки
        # БД need_done
        result = menus.draw_actions(url, img_name, img_base64, img_hash,
                                    empty=False)
        if webform:
            # Если строка содержит ссылку на вебформу, значит
            # необходимо обработать ее.
            webform_data = menus.draw_form_webform(result)
            webform_result = send_webform(webform, webform_data)
            if webform_result:
                result['webform'] = True
            else:
                result['webform'] = False

        if 'status' in result.keys():
            if result['status'] == 'new':
                print('Добавлен новый проект')
            elif result['status'] == 'update':
                print('Обновлен проект')
            print('Удалить из need_done')
            db_utils.remove_need_done(data_id)
            if not get_done_urls('url', url):
                save_to_checks(url, True, '')
        else:
            print('Ошибка добавления')
        print('')
        browser_data.quit()
