"""
mmgp_forex: модуль, который реализирует сбор и обработку данных с сайта
            https://mmgp.com/ ветки Forex брокера. Функциональность модуля
            позволяет указать кол-во страниц для сбора
            произвести анализ данных и выделить URL, сопоставить URL с
            существующим набором в БД и по необходимости предложить джобавление
            на проект.
"""
from .system import get_from_other_site
from ..utils.deco import timer


SITES = ['https://mmgp.com/forums/spisok-brokerov-forex.99/']
PAGINATOR = 'page-%s/'
BLACK_URLS = ['mmgp.com']
NODES_XPATH = '//div[@class="structItem-title"]'
NODE_XPATH = '//article[contains(@class, "message--post")]'


@timer
def start(page_count=1, debugger=False):
    return get_from_other_site(NODES_XPATH, NODE_XPATH,
                               SITES, PAGINATOR,
                               BLACK_URLS, page_count=1,
                               debugger=False)
