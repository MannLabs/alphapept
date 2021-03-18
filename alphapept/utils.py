import sys
import logging
import pandas as pd
import alphapept.io
import os
import psutil
import logging
from alphapept.__version__ import VERSION_NO

BASE_PATH = os.path.dirname(__file__)
HOME = os.path.expanduser("~")
LOG_PATH = os.path.join(HOME, "alphapept", "logs")


def set_logger(
    *,
    log_file_name: str = "",
    stream: bool = True,
    log_level: int = logging.INFO,
    overwrite: bool = False
) -> str:
    """Set the log stream and file.
    All previously set handlers will be disabled with this command.
    Parameters
    ----------
    log_file_name : str
        The file name to where the log is written.
        Folders are automatically created if needed.
        This is relative to the current path. When an empty string is provided,
        a log is written to the AlphaTims "logs" folder with the name
        "log_yymmddhhmmss" (reversed timestamp year to seconds).
        Default is "".
    stream : bool
        If False, no log data is also sent to stream.
        If True, all logging can be tracked with stdout stream.
        Default is True
    log_level : int
        The logging level. Usable values are defined in Python's "logging"
        module.
        Default is logging.INFO.
    overwrite : bool
        If True, overwrite the log_file if one exists.
        If False, append to this log file.
        Default is False.
    Returns
    -------
    : str
        The file name to where the log is written.
    """
    import time
    root = logging.getLogger()
    formatter = logging.Formatter(
        '%(asctime)s> %(message)s', "%Y-%m-%d %H:%M:%S"
    )
    root.setLevel(log_level)
    while root.hasHandlers():
        root.removeHandler(root.handlers[0])
    if stream:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(log_level)
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)
    if log_file_name is not None:
        if log_file_name == "":
            if not os.path.exists(LOG_PATH):
                os.makedirs(LOG_PATH)
            log_file_name = LOG_PATH
        log_file_name = os.path.abspath(log_file_name)
        if os.path.isdir(log_file_name):
            current_time = time.localtime()
            current_time = "".join(
                [
                    f'{current_time.tm_year:04}',
                    f'{current_time.tm_mon:02}',
                    f'{current_time.tm_mday:02}',
                    f'{current_time.tm_hour:02}',
                    f'{current_time.tm_min:02}',
                    f'{current_time.tm_sec:02}',
                ]
            )
            log_file_name = os.path.join(
                log_file_name,
                f"log_{current_time}.txt"
            )
        directory = os.path.dirname(log_file_name)
        if not os.path.exists(directory):
            os.makedirs(directory)
        if overwrite:
            file_handler = logging.FileHandler(log_file_name, mode="w")
        else:
            file_handler = logging.FileHandler(log_file_name, mode="a")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    logging.info(f"Logging to {log_file_name}.")
    return log_file_name


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


def show_platform_info() -> None:
    """Log all platform information.
    This is done in the following format:
        - [timestamp]> Platform information:
        - [timestamp]> system     - [...]
        - [timestamp]> release    - [...]
        - [timestamp]> version    - [...]
        - [timestamp]> machine    - [...]
        - [timestamp]> processor  - [...]
        - [timestamp]> cpu count  - [...]
        - [timestamp]> ram memory - [...]/[...] Gb (available/total)
    """
    import platform
    import psutil
    logging.info("Platform information:")
    logging.info(f"system     - {platform.system()}")
    logging.info(f"release    - {platform.release()}")
    if platform.system() == "Darwin":
        logging.info(f"version    - {platform.mac_ver()[0]}")
    else:
        logging.info(f"version    - {platform.version()}")
    logging.info(f"machine    - {platform.machine()}")
    logging.info(f"processor  - {platform.processor()}")
    logging.info(
        f"cpu count  - {psutil.cpu_count()}"
        # f" ({100 - psutil.cpu_percent()}% unused)"
    )
    logging.info(
        f"ram memory - "
        f"{psutil.virtual_memory().available/1024**3:.1f}/"
        f"{psutil.virtual_memory().total/1024**3:.1f} Gb "
        f"(available/total)"
    )
    logging.info("")

def show_python_info() -> None:
    """Log all Python information.
    This is done in the following format:
        - [timestamp]> Python information:
        - [timestamp]> alphapept          - [current_version]
        - [timestamp]> [required package] - [current_version]
        - ...
        - [timestamp]> [required package] - [current_version]
    """
    import importlib.metadata
    import platform
    module_versions = {
        "python": platform.python_version(),
        "alphapept": VERSION_NO
    }
    requirements = importlib.metadata.requires("alphapept")
    for requirement in requirements:
        module_name = requirement.split()[0].split(";")[0].split("=")[0]
        try:
            module_version = importlib.metadata.version(module_name)
        except importlib.metadata.PackageNotFoundError:
            module_version = ""
        module_versions[module_name] = module_version
    max_len = max(len(key) for key in module_versions)
    logging.info("Python information:")
    for key, value in sorted(module_versions.items()):
        logging.info(f"{key:<{max_len}} - {value}")
    logging.info("")



def check_python_env():
    import numba
    logging.info(f'AlphaPept version {VERSION_NO}')
    logging.info(f'Python version {sys.version}')
    logging.info(f'Numba version {numba.__version__}')
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

    if settings['general']['n_processes'] > 60:
        settings['general']['n_processes'] = 60
        logging.info('Capping number of processes to {}.'.format(settings['general']['n_processes']))

    if settings['experiment']['file_paths'] == []:
        raise FileNotFoundError('No files selected')

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

    if settings['fasta']['save_db']:
        var_id = ['mods_variable_terminal', 'mods_variable', 'mods_variable_terminal_prot']
        n_var_mods = sum([len(settings['fasta'][_]) for _ in var_id])
        if n_var_mods > 2:
            logging.info(f'Number of variable modifications {n_var_mods} is larger than 2, possibly causing a very large search space. Only small DB w/o modifications will be created, the full database will be generated on the fly for the second search.')
            settings['fasta']['save_db'] = False

        protease = settings['fasta']['protease']
        if protease == 'non-specific':
            logging.info(f'Protease is {protease}, possibly causing a very large search space. Only small DB w/o modifications will be created, the full database will be generated on the fly for the second search.')
            settings['fasta']['save_db'] = False

    if settings['fasta']['fasta_block'] > settings['fasta']['db_size']:
        logging.info('FASTA block size is larger than db size. Decreasing fasta block size.')
        settings['fasta']['fasta_block'] = settings['fasta']['db_size']

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

        try:
            df = alphapept.io.MS_Data_File(
                file_name
            ).read(dataset_name=field)

            df['filename'] = file_name
            df['shortname'] = shortnames[idx]

            if 'fraction' in settings['experiment'].keys():
                if settings['experiment']['fraction'] != []:
                    df['fraction'] = settings['experiment']['fraction'][idx]

            all_dfs.append(df)
        except KeyError: # e.g. field does not exist
            pass

        if callback:
            callback((idx+1)/len(paths))

    if len(all_dfs) > 0:
        xx = pd.concat(all_dfs)
        xx.to_hdf(settings['experiment']['results_path'], 'combined_'+field)
    else:
        xx = pd.DataFrame()

    return xx
