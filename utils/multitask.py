# https://gist.githubusercontent.com/yasufumy/087c8c80ea761c1ec0f3b30fea358212/raw/34136a50e1fdce2b6b0f41572ea78db94a3b8a30/multiprocessing_with_lambda_2.py
from multiprocessing import Pool


_func = None


def worker_init(func):
  global _func
  _func = func
  

def worker(x):
  return _func(x)


def xmap(func, iterable, processes=None):
  with Pool(processes, initializer=worker_init, initargs=(func,)) as p:
    return p.map(worker, iterable)