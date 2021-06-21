import time


def timer(func):
    """
    Функция таймер для измерения скорости обработки. Утилита
    """

    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        def_t = time.perf_counter() - t0
        print('=' * 80)
        print('Затрачено времени: %.2f c' % def_t)
        print('=' * 80)
        print()
        return result

    return wrapper
