import sys
import logging
import pandas as pd
import os

def log_me(given_function):
    """
    Decorator to track function execution
    """
    def wrapper(*args, **kwargs):
        logging.debug("FUNCTION `{}` EXECUTED".format(given_function.__name__))
        result = given_function(*args, **kwargs)
        logging.debug("FUNCTION `{}` FINISHED".format(given_function.__name__))
        return result
    return wrapper


def check_hardware():
    import psutil
    memory_available = psutil.virtual_memory().available/1024**3

    logging.info('Currently {:.2f} GB of memory available.'.format(memory_available))

    if memory_available < 16:
        raise MemoryError('Only {:.2f} GB memory available. Make sure that at least 16 GB are available.'.format(memory_available))
    import platform
    sysinfo = platform.uname()

    logging.info('System information: {}'.format(sysinfo))

def check_python_env():
    import numba
    logging.info('Python version {}'.format(sys.version))
    logging.info('Numba version {}'.format(numba.__version__))
    if float('.'.join(numba.__version__.split('.')[0:2])) < 0.46:
        raise RuntimeError('Numba version {} not sufficient'.format(numba.__version__))

def check_settings(settings):
    import multiprocessing
    logging.info('Check for settings not completely implemented yet.')

    n_set = settings['general']['n_processes']
    n_actual = multiprocessing.cpu_count()

    if n_set > n_actual:
        settings['general']['n_processes'] = n_actual
        logging.info('Setting number of processes to {}.'.format(n_actual))

    for file in settings['experiment']['files']:
        if file.endswith('.d'):
            if not os.path.isdir(file):
                raise FileNotFoundError(file)
        else:
            if not os.path.isfile(file):
                raise FileNotFoundError(file)


    return settings

def assemble_df(settings, callback = None):
    """
    Todo we could save this to disk
    include callback
    """
    files_npz = settings['experiment']['files_npz']

    paths = [os.path.splitext(_)[0]+'.hdf' for _ in files_npz]

    all_dfs = []
    for idx, _ in enumerate(paths):

        df = pd.read_hdf(_,'protein_fdr')
        df['filename'] = _

        if 'fraction' in settings['experiment'].keys():
            if settings['experiment']['fraction'] != []:
                df['fraction'] = settings['experiment']['fraction'][idx]
        if 'experiment' in settings['experiment'].keys():
            if settings['experiment']['experiment'] != []:
                df['experiment'] = settings['experiment']['experiment'][idx]

        all_dfs.append(df)

        if callback:
            callback((idx+1)/len(paths))

    xx = pd.concat(all_dfs)

    # Here we could save things

    xx.to_hdf(settings['experiment']['evidence'], 'combined_protein_fdr')

    return xx

def reset_hdf(hdf_path):
    """
    Removes previous search results from hdf file.
    """
    logging.info('Removing previous search results from hdf.')
    for x in ['features_calib', 'first_search' ,'peptide_fdr' ,'protein_fdr','second_search']:
        with pd.HDFStore(hdf_path) as hdf:
            hdf.remove(x)

def resave_hdf(hdf_path):
    """
    When overwriting hdf files HDF does not adjust size after removal
    This function reads the hdf and overwrites it.
    """
    logging.info('Re-saving hdf file.')
    new_hdf = {}
    with pd.HDFStore(hdf_path) as hdf:
        keys = hdf.keys()

    for key in keys:
        new_hdf[key] = pd.read_hdf(hdf_path, key)

    first = True
    for key in new_hdf.keys():
        if first:
            new_hdf[key].to_hdf(hdf_path, key, mode='w')
            first = False
        else:
            new_hdf[key].to_hdf(hdf_path, key, mode='r+')
