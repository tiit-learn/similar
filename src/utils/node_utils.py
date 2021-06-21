import logging
import os
import re
import pickle
import threading

from .funcs import get_response, get_img_hash, get_difference_hash
from .db_utils import get_db_data, save_to_db

# from src.utils.funcs import *


def node_data_generator(url, debug=False):
    """
    Функция генерации данных при добавлении нового проекта.
    Утилита - проекта
    """
    node_data = {}
    replace_ = re.compile(r'https|http|://|www.|/.*')
    phone_format_ = re.compile(r'[\(\)\+\-]?|tel\:| |')
    addresses_format_ = re.compile(r'[\(\)\n]?')

    node_data['names'] = input(
        'Укажите названия (через запятую): ').strip().title().split(',')
    node_data['links'] = re.sub(replace_, '', input(
        'Укажите ссылки (через запятую): ').strip().lower()).split(',')
    node_data['email'] = input(
        'Укажите email (через запятую): ').strip().lower().split(',')
    node_data['phones'] = re.sub(phone_format_, '', input(
        'Укажите телефонные номера (через запятую): ').strip()).split(',')
    node_data['addresses'] = re.sub(addresses_format_, '', input(
        'Укажите известные адреса (через ,,): ').strip().title()).split(',,')
    node_data['categories'] = input(
        'Укажите названия категорий (через запятую): ').strip().split(',')
    node_data['description'] = """%s""" % re.sub(r'\n', '<p></p>', re.sub(
        r'$', '</p>', re.sub(r'^', '<p>', input('Укажите описание: ').strip())))
    if url and 'links' in node_data.keys():
        node_data['links'].append(re.sub(replace_, '', url))
    if debug:
        breakpoint()

    return node_data


def data_list(list_data):
    """
    Функция форматирования строк, при добавлении в поля на сайте.
    Утилита - проекта
    """
    if len(list_data):
        return ' ' + ' '.join(map(lambda x: '"""' + x.strip().replace('"', '""') + '"""',
                                  filter(lambda x: len(x) > 1, list_data)))
    else:
        return ''


def get_data(page):
    """
    Функция получения всех элементов материала на странице
    Функциональность
    """

    resp = get_response(url=page)
    base_url = 'https://www.%s' % os.getenv('site')
    data_list = []
    for node_element in resp.html.find('.node--type-project'):
        title_thread = ' %s ' % threading.current_thread().name
        print(title_thread.center(80, '='))

        title = node_element.find(
            '.field--name-node-title', first=True).text.replace('"', '""')
        url = base_url + node_element.find('a', first=True).attrs['href']
        node_id = int(node_element.find(
            'div', first=True).attrs['data-history-node-id'])

        db_node_data = get_db_data(node_id)

        repl = re.compile(r'.webp.*|styles/max_325x325/public/')
        img = node_element.find('img', first=True).attrs['src']
        img = base_url + re.sub(repl, '', img)
        node_hash_img = get_img_hash(get_response(url=img, stream=True).raw)

        if not db_node_data:
            # print('%s - %s - %s - %s' % (title, url, img, hash_img))
            hash_img = pickle.dumps([node_hash_img]).hex()
            data_list.append((node_id, title, url, img, hash_img))
            save_to_db((node_id, title, url, img, hash_img))
        else:
            db_node_datas = pickle.loads(
                bytes.fromhex(dict(db_node_data)['hash_img']))
            for db_img_hash in db_node_datas:

                def_hash = get_difference_hash(node_hash_img, db_img_hash)

                # Если схожесть не 100% необходимо обновить сигнатуру хеша ноды
                # написать функцию добавления нового хеша в БД
                logging.info('[%s] Схожесть c БД: %.2f%%' %
                             (node_id, def_hash))

    return data_list
