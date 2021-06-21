# from src.sys.system import *
# from src.utils.utils import *
# from src.utils.funcs import *
# from src.utils.deco import *
# from src.menus.menus import *
# from src.const import *
# from src.sys.system import *
import pickle

from ..sys.system import (site_data_need_check,
                          cli_need_done,
                          check_db_data, save_to_db,
                          work_with_url,
                          remove_hash_img_index_from_node_id,
                          find_simular_in_db, collect_all,
                          new_project, update_project, check_sites)
from ..utils import (add_hash_to_node_db,
                     hash_menu, get_hashes_from_db,
                     remove_from_bd, add_new_to_db)


main_actions = {'1': 'Добавить новый проект (site & db)',
                '2': 'Добавить в существующий проект (site & db)',
                '3': 'Добавить только img_hash (only db)',
                '4': 'Добавить проект (only db)',
                '5': 'Добавить проект (only site)',
                '6': 'Удалить хеш из проекта (only db)'}

_actions = {'1': 'Сбор данных [Все]',
            '2': 'Сбор данных [Проекты]',
            '3': 'Сбор данных [На сайте]',
            '4': 'Работа с БД',
            '5': 'Работа с сайтом',
            '6': 'Работа с URL',
            '7': 'Нужно проверить'}

_check_from_projects = {'1': 'Все проекты',
                        '2': 'Указать проект'}

_db_actions = {'1': 'Добавить хеш в проект',
               '2': 'Удалить хеш из проекта',
               '3': 'Проверка проектов',
               '9': 'Поиска дубликатов в БД'}

_actions_two = {'1': 'Взять hash из URL',
                '2': 'Взять hash из файла'}

_site_actions = {'9': 'Получить все данные с сайта'}

_project_check = {'1': 'Объединить проект',
                  '2': 'Удалить проект'}

EXIT_VALUE = ['', '0', 'q', 'n', 'e', 'quit', 'exit']


def construct_menu(dict_action=main_actions, headline='Что необходимо сделать?',
                   has_image=True):
    """
    Функция создания меню по указанным аргументам.
        dict_action : словарь с пунктами меню, в качестве значений словаря ключи
            по которым будет проводиттся проверка ввода.
        headline : Заголовок меню
    Функциональность
    """
    # dict_action[''] = 'Ничего не делать. Выйти.'
    if not has_image:
        main_actions.pop('1')
    if headline:
        print('-' * 80)
        print(headline.center(80))

    print('-' * 80)
    for i in sorted(dict_action.keys()):
        raw = '\t-> [%s] - %s' % (i, dict_action[i])
        print(raw.ljust(80))
    print(('\n\t-> [0 / Quit / Exit] - Ничего не делать. Выйти.').ljust(80))
    print('-' * 80)
    choice = False
    while not choice:
        choice = input('Введите: ')

        if choice in dict_action.keys():
            print('Делаем - [%s] - %s' % (choice, dict_action[choice]))
            return choice
        elif choice.lower() in EXIT_VALUE:
            return False
        else:
            print('Ответ не распознан!')
            choice = False


def draw_actions(url, img_name, img, img_hash, empty=False):
    """
    Конструктор интерактивного меню
    Функциональность
        url
        img
        img_hash
        webform
        empty
    """
    done = {}
    # Добавить в уже существующий материал
    if not img:
        has_image = False
    else:
        has_image = True

    if not empty:
        step_1 = construct_menu(has_image=has_image)
        if step_1 == '1':
            new_ = new_project(img_name, img, url)
            if new_:  # -> (node_id, title_n, url, img)
                hash_img = pickle.dumps([img_hash]).hex()
                save_to_db(new_ + (hash_img,))
                done['title'] = new_[1]
                done['title_id'] = new_[0]
            else:
                done['status'] = False
                raise ValueError('Материал не добавлен, нужно разобраться')
            done['status'] = 'new'
        elif step_1 == '2':
            step_2 = construct_menu(
                {'1': 'Указать доп. инфо',
                 '2': 'Не указывать доп. инфо'}, headline=False)
            while True:

                node_id = input('Укажите id материала: ')
                if node_id.isnumeric():
                    break
                else:
                    print('Не верно указанный ID')
            if step_2 == '1':  # Необходимо добавить доп информацию
                more_data = True
            elif step_2 in ['2', False]:
                more_data = False

            if not step_2 == '':
                new_ = update_project(node_id, url, more_data=more_data)
                if new_:  # -> (node_id, title_n, url, img)
                    add_hash_to_node_db(node_id, img_hash)
                    done['title'] = new_[1]
                    done['title_id'] = new_[0]
                else:
                    done['status'] = False
                    raise ValueError('Материал не обновлен, нужно разобраться')
                done['status'] = 'update'
        elif step_1 == '3':
            node_id = input('Укажите id материала: ')
            add_hash_to_node_db(node_id, img_hash)
            done['status'] = False
        # TODO:  Сделать рабочими остальные пункты меню
        # elif step_1 == '4':
        #     add_new_to_db(url)
        # elif step_1 == '6':
        #     node_id = int(input('Введите ID проекта: '))
        #     hash_index = int(input('Введите номер хеша в проекте: '))
        #     remove_hash_img_index_from_node_id(node_id, hash_index)
        else:
            done['status'] = False
        return done


def draw_form_webform(node_result):
    """
    Функция добавляет интерактивное меню для работы с заявками
    на сайте
    """
    choice = {'1': 'Лохотрон', '2': 'Доверенный', '3': 'Сомнительный'}
    print(
        '\n', '[1] Лохотрон | [2] Доверенный | [3] Сомнительный'.center(80), '\n')
    checked = False
    while not checked:
        p_status = input('Выбирите статус: ')
        if p_status in ['1', '2', '3']:
            checked = True
            p_status = choice[p_status]

    choice = construct_menu(dict_action={'1': 'Указать название'},
                            headline='Установить "Проверка сайта (156)" ?')
    if choice == '1':
        checked = False
        while not checked:
            p_id = input('Введите id: ')
            if p_id.isnumeric():
                checked = True
                p_id = int(p_id)
        p_title = input('Введите название: ')
        p_title = '%s (%s)' % (p_title, p_id)
    else:
        if 'title' in node_result.keys() and 'title_id' in node_result.keys():
            p_title = '%s (%s)' % (node_result['title'],
                                   node_result['title_id'])
        else:
            p_title = 'Проверка сайта (156)'
    return {"status": p_status, "title": p_title}

def main_menu_loop():

    while True:
        choice = construct_menu(dict_action=_actions)
        if not choice:
            print('Завершаем. До свидания!')
            break
        else:
            if choice == "1":
                # TODO: Разделить на сбор заявок и проверка сайтов.
                # Обдумать как лучше сделать.
                site_data_need_check()
                check_sites()
            elif choice == "2":
                _choice = construct_menu(dict_action=_check_from_projects)
                if _choice == "1":
                    check_sites()
                elif _choice == "2":
                    check_sites(need_site=input('Введите название проекта: '))
            elif choice == "3":
                site_data_need_check()
            elif choice == "4":
                _choice = construct_menu(dict_action=_db_actions)
                if _choice == "1":
                    # Добавить хеш в проект
                    _choice = construct_menu(dict_action=_actions_two)
                    if _choice == "1":
                        # Взять hash из URL
                        hash_menu(action='add', source='url')
                    if _choice == "2":
                        # Взять hash из файла
                        hash_menu(action='add', source='file')
                elif _choice == "2":
                    # Удалить хеш из проекта
                    _choice = construct_menu(dict_action=_actions_two)
                    if _choice == "1":
                        # Взять hash из URL
                        hash_menu(action='delete', source='url')
                    if _choice == "2":
                        # Взять hash из файла
                        hash_menu(action='delete', source='file')
                elif _choice == "3":
                    # Проверка акутальности данных проектов в БД
                    check_db_data(input('Введите id материала: '))
                elif _choice == "9":
                    find_simular_in_db(int(input('Укажите точность поиска: ')))
            elif choice == "5":
                _choice = construct_menu(dict_action=_site_actions)
                if _choice == "9":
                    collect_all(int(input('Количество страниц для обхода: ')),
                                int(input('Начальную страницу: ')))
                else:
                    print('Команда не найдена.')
            elif choice == "6":
                work_with_url(url=input('Введите URL адрес сайта: '))
            elif choice == "7":
                cli_need_done()
            else:
                print('Команда не найдена.')


def project_check_menu(headline='Что необходимо сделать?',
                       node_id_old=None, node_id_new=None):
    # Функция отрисовки меню для раздела управления проектами при проверке
    if not node_id_old:
        node_id_old = int(input('Введите ID материала, откуда копируем: '))

    choice = construct_menu(dict_action=_project_check, headline=headline)
    if choice == '1':
        if not node_id_new:
            node_id_new = int(input('Введите ID материала, куда копируем: '))
        # Необходимо получить список хешей с старого матриала.
        old_hashes = get_hashes_from_db(node_id_old)
        print('\tНайдено %s хешей' % len(old_hashes))
        for img_hash in old_hashes:
            add_hash_to_node_db(node_id_new, img_hash)

        remove_from_bd(node_id_old)
    elif choice == '2':
        remove_from_bd(node_id_old)
