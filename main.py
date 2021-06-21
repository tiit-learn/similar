"""
Автоматическая система сбора данных с сайтов и публикатор на
указанном сайте данных о проектах.

Система может получать скриншоты главных страниц проекта
и сравнивать хеши, данного скриншота, с разных формами
вычисления этих хешей.

TODO: Рефакторинг. Оптимизация и инкапсуляция кода.

DONE: Перенести сохранение результатов в БД
DONE: Перенос в system.py функционала поиска данных на проектах get_from_other_site
DONE: Переделать web_form на прием img в base64
DONE: Установить куки глобально в настройках проекта
      (Пока установил в константы) 
"""
import logging

from src.menus.menus import main_menu_loop

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logging.disable(logging.DEBUG)

if __name__ == '__main__':
    choice = input()
    if choice == '1':
        print(__doc__)
        main_menu_loop()
    elif choice == 'gen':
        print('node_utils'.upper())
        from src.utils import node_utils
        node_utils.node_data_generator(True)
    elif choice == 'dev':
        from src.sys import system
        print('development'.upper())
        system.check_sites('telltrue')
    elif choice == '2':
        from src.utils.funcs import get_browser_chrome
        get_browser_chrome('chrome://settings/languages')
