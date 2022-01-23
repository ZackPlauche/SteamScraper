import time

def timeit(func):
    def wrapper():
        start = time.time()
        val = func()
        end = time.time()
        print(f'Time: {end - start}s')
        return val
    return wrapper
