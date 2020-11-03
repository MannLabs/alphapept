"""
Dummy script to test gpu access

"""

import multiprocessing
import threading
import functools
import math
import numba as numba_
numba = numba_
import numpy as np
from numba import cuda as cuda_
cuda = cuda_

import cupy


@numba.njit
def grid_1d(x): return -1
@numba.njit
def grid_2d(x): return -1, -1


def set_cuda_grid(dimensions=0):
    global cuda
    if dimensions == 0:
        cuda = cuda_
        cuda.grid = cuda_.grid
    if dimensions == 1:
        cuda = numba_
        cuda.grid = grid_1d
    if dimensions == 2:
        cuda = numba_
        cuda.grid = grid_2d


def parallel_compiled_func(
    _func=None,
    *,
    cpu_threads=None,
    dimensions=1,
):
    set_cuda_grid()
    if dimensions not in (1, 2):
        raise ValueError("Only 1D and 2D are supported")
    if cpu_threads is not None:
        use_gpu = False
    else:
        try:
            cuda.get_current_device()
        except cuda.CudaSupportError:
            use_gpu = False
            cpu_threads = 0
        else:
            use_gpu = True
    if use_gpu:
        set_cuda_grid()
        def parallel_compiled_func_inner(func):
            cuda_func = cuda.jit(func)
            if dimensions == 1:
                def wrapper(iterable_1d, *args):
                    cuda_func.forall(iterable_1d.shape[0], 1)(
                        -1,
                        iterable_1d,
                        *args
                    )
            elif dimensions == 2:
                def wrapper(iterable_2d, *args):
                    threadsperblock = (
                        min(iterable_2d.shape[0], 16),
                        min(iterable_2d.shape[0], 16)
                    )
                    blockspergrid_x = math.ceil(
                        iterable_2d.shape[0] / threadsperblock[0]
                    )
                    blockspergrid_y = math.ceil(
                        iterable_2d.shape[1] / threadsperblock[1]
                    )
                    blockspergrid = (blockspergrid_x, blockspergrid_y)
                    cuda_func[blockspergrid, threadsperblock](
                        -1,
                        -1,
                        iterable_2d,
                        *args
                    )
            return functools.wraps(func)(wrapper)
    else:
        set_cuda_grid(dimensions)
        if cpu_threads <= 0:
            cpu_threads = multiprocessing.cpu_count()
        def parallel_compiled_func_inner(func):
            numba_func = numba.njit(nogil=True)(func)
            if dimensions == 1:
                def numba_func_parallel(
                    thread,
                    iterable_1d,
                    *args
                ):
                    for i in range(
                        thread,
                        len(iterable_1d),
                        cpu_threads
                    ):
                        numba_func(i, iterable_1d, *args)
            elif dimensions == 2:
                def numba_func_parallel(
                    thread,
                    iterable_2d,
                    *args
                ):
                    for i in range(
                        thread,
                        iterable_2d.shape[0],
                        cpu_threads
                    ):
                        for j in range(iterable_2d.shape[1]):
                            numba_func(i, j, iterable_2d, *args)
            numba_func_parallel = numba.njit(nogil=True)(numba_func_parallel)
            def wrapper(iterable, *args):
                threads = []
                for thread_id in range(cpu_threads):
                    t = threading.Thread(
                        target=numba_func_parallel,
                        args=(thread_id, iterable, *args)
                    )
                    t.start()
                    threads.append(t)
                for t in threads:
                    t.join()
                    del t
            return functools.wraps(func)(wrapper)
    if _func is None:
        return parallel_compiled_func_inner
    else:
        return parallel_compiled_func_inner(_func)


def test_func_1d(query_idx, in_array_1d, out_array_1d, complexity):
    "query_idx should be an int satisfying 0<=query_idx<=len(in_array_1d)."
    "In case query_idx == -1, a gpu pointer is assumed."
    "Each different query_idx should write to a unique out_array_1d section"
    if query_idx == -1:
        query_idx = cuda.grid(1)
    # simulate compute intensive function
    x = 0
    for i in range(complexity):
        x += 1 + in_array_1d[query_idx]
    # quick test to test if function generates correct output
    out_array_1d[query_idx] = x


@parallel_compiled_func(dimensions=2)
def test_func_2d(
    query_idx,
    query_idy,
    in_array_2d,
    out_array_2d,
    complexity
):
    if query_idx == -1:
        query_idx, query_idy = cuda.grid(2)
    # simulate compute intensive function
    x = 0
    for i in range(complexity):
        x += 1 + in_array_2d[query_idx, query_idy]
    # quick test to test if function generates correct output
    out_array_2d[query_idx, query_idy] = x

if __name__ == '__main__':
    import time
    size = 10**6
    complexity = 10**4

    # def test_func_1d_not_compiled(queries, *args):
    #     for i in range(len(queries)):
    #         test_func_1d(i, queries, *args)

    # print("\nNot compiled:")
    # %time test_func_not_compiled(in_array_1d, out_array_1d, complexity)

    print("\n1 CPU thread:")
    test_func_1d_cpu_1 = parallel_compiled_func(cpu_threads=1)(test_func_1d)
    in_array_1d = np.around(100 * np.random.random(size) + 1)
    out_array_1d = np.empty_like(in_array_1d)
    s = time.time()
    test_func_1d_cpu_1(in_array_1d, out_array_1d, complexity)
    print(time.time() - s)
    assert np.all(
        (complexity * (1 + in_array_1d)) == out_array_1d
    ), "1D function CPU not working"
    assert (
        test_func_1d_cpu_1.__doc__ == test_func_1d.__doc__
    ), "Docstring not passed properly"

    print(f"\n{multiprocessing.cpu_count()} (max) CPU threads:")
    test_func_1d_cpu_max = parallel_compiled_func(cpu_threads=-1)(test_func_1d)
    in_array_1d = np.around(100 * np.random.random(size) + 1)
    out_array_1d = np.empty_like(in_array_1d)
    s = time.time()
    test_func_1d_cpu_max(in_array_1d, out_array_1d, complexity)
    print(time.time() - s)
    assert np.all(
        (complexity * (1 + in_array_1d)) == out_array_1d
    ), "1D function CPU not working"
    assert (
        test_func_1d_cpu_max.__doc__ == test_func_1d.__doc__
    ), "Docstring not passed properly"

    print(f"\nGPU:")
    test_func_1d_gpu = parallel_compiled_func(test_func_1d)
    in_array_1d_gpu = cupy.around(100 * np.random.random(size) + 1)
    out_array_1d_gpu = cupy.empty_like(in_array_1d_gpu)
    s = time.time()
    test_func_1d_gpu(in_array_1d_gpu, out_array_1d_gpu, complexity)
    print(time.time() - s)
    assert np.all(
        (complexity * (1 + in_array_1d_gpu)) == out_array_1d_gpu
    ), "1D function GPU not working"
    assert (
        test_func_1d_gpu.__doc__ == test_func_1d.__doc__
    ), "Docstring not passed properly"

    print(f"\n2D GPU:")
    in_array_2d_gpu = cupy.around(100 * np.random.random((size//10, 10)) + 1)
    out_array_2d_gpu = cupy.empty_like(in_array_2d_gpu)
    s = time.time()
    test_func_2d(in_array_2d_gpu, out_array_2d_gpu, complexity)
    print(time.time() - s)
    assert np.all(
        (complexity * (1 + in_array_2d_gpu)) == out_array_2d_gpu
    ), "2D function not working"
    assert (
        test_func_2d.__doc__ == test_func_2d.__doc__
    ), "Docstring not passed properly"
