import sys
import logging
import pandas as pd
import alphapept.io
import os
import psutil


def check_file(file):
    if not os.path.isfile(file):
        raise FileNotFoundError(file)


def check_dir(dir):
    if not os.path.isdir(dir):
        raise FileNotFoundError(dir)


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

    logging.info(
        'Currently {:.2f} GB of memory available.'.format(memory_available)
    )

    MIN_MEMORY = 8
    if memory_available < MIN_MEMORY:
        raise MemoryError(f'Only {memory_available:.2f} GB memory available. Make sure that at least {MIN_MEMORY} GB are available.')
    import platform
    sysinfo = platform.uname()

    logging.info('System information: {}'.format(sysinfo))


def check_python_env():
    import numba
    logging.info('Python version {}'.format(sys.version))
    logging.info('Numba version {}'.format(numba.__version__))
    if float('.'.join(numba.__version__.split('.')[0:2])) < 0.46:
        raise RuntimeError(
            'Numba version {} not sufficient'.format(numba.__version__)
        )


def check_settings(settings):
    # _this_file = os.path.abspath(__file__)
    # _this_directory = os.path.dirname(_this_file)
    import multiprocessing
    logging.info('Check for settings not completely implemented yet.')

    n_set = settings['general']['n_processes']
    n_actual = psutil.cpu_count()

    logging.info('Checking CPU settings.')
    if n_set > n_actual:
        settings['general']['n_processes'] = n_actual
        logging.info('Setting number of processes to {}.'.format(n_actual))

    logging.info('Checking if files exist.')
    for file in settings['experiment']['file_paths']:
        if file.endswith('.d'):
            check_dir(file)
        else:
            check_file(file)

    for file in settings['fasta']['fasta_paths']:
        check_file(file)

    if not settings['experiment']['results_path']:
        file_dir = os.path.dirname(settings['experiment']['file_paths'][0])
        settings['experiment']['results_path'] = os.path.normpath(
            os.path.join(file_dir, 'results.hdf')
        )
        logging.info(
            'Results path was not set. Setting to {}'.format(
                settings['experiment']['results_path']
            )
        )

    if settings['experiment']['shortnames'] == []:
        logging.info('Shortnames not set. Setting to filename.')
        shortnames = [
            os.path.splitext(
                os.path.split(file_name)[1]
            )[0] for file_name in settings['experiment']['file_paths']
        ]
        settings['experiment']['shortnames'] = shortnames

    if settings['fasta']['save_db']:
        if not settings['fasta']['database_path']:
            file_dir = os.path.dirname(settings['experiment']['file_paths'][0])
            settings['fasta']['database_path'] = os.path.normpath(
                os.path.join(file_dir, 'database.hdf')
            )
            logging.info(
                'No database path set and save_db option checked. Using default path {}'.format(settings['fasta']['database_path'])
            )

    return settings


def assemble_df(settings, field = 'protein_fdr', callback=None):
    """
    Todo we could save this to disk
    include callback
    """
    paths = [
        os.path.splitext(
            file_name
        )[0]+'.ms_data.hdf' for file_name in settings['experiment']['file_paths']
    ]
    shortnames = settings['experiment']['shortnames']
    all_dfs = []
    for idx, file_name in enumerate(paths):

        df = alphapept.io.MS_Data_File(
            file_name
        ).read(dataset_name=field)
        df['filename'] = file_name
        df['shortname'] = shortnames[idx]

        if 'fraction' in settings['experiment'].keys():
            if settings['experiment']['fraction'] != []:
                df['fraction'] = settings['experiment']['fraction'][idx]
        all_dfs.append(df)

        if callback:
            callback((idx+1)/len(paths))

    xx = pd.concat(all_dfs)

    # Here we could save things

    xx.to_hdf(settings['experiment']['results_path'], 'combined_'+field)

    return xx
