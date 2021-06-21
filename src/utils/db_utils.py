import logging
import random
import sqlite3
import time

from ..const.constants import DB_NAME


def do_query(db_name, query):
    """
    Подключение к БД и отправка созданного запроса. DB UTIL
    """
    # logging.debug('Запрос в БД:\n\n%s\n' % query)
    retry = 0
    while True:
        if retry > 5:
            logging.critical('Запрос не добавлен в БД')
            response_data = False
            break
        try:
            with sqlite3.connect(db_name) as conn:
                curs = conn.cursor()
                curs.execute(query)
                response_data = curs.fetchall()
                conn.commit()
                curs.close()
        except Exception as err:
            sleep_time = random.randint(1, 10)
            logging.error('Ошибка БД: %s\n\n' % (err))
            logging.info('Засыпаю на %s' % str(sleep_time))
            time.sleep(sleep_time)
            retry += 1
        else:
            # logging.debug('Ответ из БД:\n\n%s\n' % response_data)
            break

    return response_data


def all_db_data(db_path=DB_NAME):
    """
    Конструктор запроса на получение всех данных из БД. DB UTIL
    """
    query = "SELECT * FROM nodes"
    data = do_query(db_path, query)
    return data


def get_db_data(node_id, db_path=DB_NAME):
    """
    Конструктор запроса на получение данных о ноде, хранящиеся в локальной БД. DB UTIL
    """
    query = "SELECT * FROM nodes WHERE node_id IN (%s)" % node_id

    data = do_query(db_path, query)

    if len(data) > 0:
        data_node = zip(('node_id', 'title', 'url', 'img',
                         'hash_img'), data[0])
        return data_node
    else:
        return None


def new_db(db_path, table_name, columns):
    """
    Конструктор запроса на создание новой БД.
    Запрос на создание новой БД если ее еще не существует. DB UTIL
    """
    queries = """CREATE TABLE IF NOT EXISTS %s (%s);""" % (table_name, columns)
    do_query(db_path, queries)


def save_to_db(data_tuple, db_name=DB_NAME):
    """
    Конструктор запроса на добавление информации о материале. DB UTIL
    """
    # print(data_tuple)
    print()
    logging.info('[%s] Добавляю в БД' % data_tuple[0])
    query = """INSERT INTO nodes (node_id, title, url, img, hash_img) VALUES (%s, "%s", '%s', '%s', '%s')""" % data_tuple

    do_query(db_name, query)


def update_to_db(node_id, hash_img, db_name=DB_NAME):
    """
    Конструктор запроса на изменение hash_img материала. DB UTIL
    """
    logging.info('[%s] Обновляю [hash_img] в БД' % node_id)
    query = 'UPDATE nodes SET hash_img = "%s" WHERE node_id = %s' % (hash_img,
                                                                     node_id)
    do_query(db_name, query)


def update_to_db_cell(node_id, cell, data, db_name=DB_NAME):
    """
    Конструктор запроса на изменение определенной ячейки материала. DB UTIL
    """
    logging.info('[%s] Обновляю [%s] в БД' % (node_id, cell))
    query = 'UPDATE nodes SET %s = "%s" WHERE node_id = %s' % (cell,
                                                               data.replace(
                                                                   '"', '""'),
                                                               node_id)
    do_query(db_name, query)


def remove_from_bd(node_id, db_name=DB_NAME):
    """
    Конструктор запроса на удаление материала из БД. DB UTIL
    """
    logging.info('[%s] Удаляю из БД' % node_id)
    query = 'DELETE FROM nodes WHERE node_id = %s;' % (node_id)
    do_query(db_name, query)


def add_checks(domain: str, url: str, status: bool, note: str,
               db_path: str = DB_NAME):
    """
    Функция добавления проверенного URL в ДБ с статусом проверки.
    Если Url не удалось загрузить, статус будет False, иначе True.
    """
    query = '''INSERT INTO checks(domain,url,status,note)
              VALUES("%s","%s",%s, "%s");''' % (domain, url, status, note)
    do_query(db_path, query)


def get_checks(column: str, url: str, db_path: str = DB_NAME):
    """
    Функция возвращает id url из БД. Сравнить вывыод можно по разным столбцам
    выборки.
    """
    query = '''SELECT id FROM checks WHERE %s = "%s";''' % (column, url)
    return do_query(db_path, query)


def add_need_done(domain, url, project, url_title, simular_search,
                  simular_db, img_hash, webform, db_path=DB_NAME):
    """
    Фнукция добавляет информацию о новом URL в БД, который необходимо
    добавить.
    """
    query = '''INSERT INTO need_done(domain,url,project,url_title,
                                     simular_search,simular_db,img_hash,
                                     webform)
              VALUES("%s","%s","%s","%s",
                     '%s','%s',"%s", "%s");''' % (domain, url, project,
                                                  url_title,
                                                  simular_search,
                                                  simular_db, img_hash,
                                                  webform)
    do_query(db_path, query)


def get_need_done(url, db_path=DB_NAME):
    """
    Функция получет информацию из БД об URL, которые находится в таблице URL,
    которые необходимо сделать.
    """
    query = '''SELECT * FROM need_done WHERE url = "%s";''' % (url)
    return do_query(db_path, query)


def remove_need_done(raw_id, db_path=DB_NAME):
    """
    Функция удаляет из таблицы need_done строку raw_id.
    """
    query = '''DELETE FROM need_done WHERE id = %s;''' % (raw_id)
    return do_query(db_path, query)


def get_all_need_done(db_path=DB_NAME):
    """
    Функция возвращет полный список данных которые необходимо обработать
    """
    query = '''SELECT * FROM need_done ORDER BY webform IS NULL OR webform='', webform;'''
    return do_query(db_path, query)
