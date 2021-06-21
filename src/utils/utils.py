import re


def is_url(string):
    """
    Функция проверки строки на соответствие URL. Утилита
    """
    is_url = re.compile(
        r'[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)', re.IGNORECASE)
    return re.match(is_url, string)


def get_domain(url):
    """
    Функция получения домена из URL. Утилита
    """
    return re.sub(r'http(s)?:\/\/|www.|/.*|[.,]$', '', url)
