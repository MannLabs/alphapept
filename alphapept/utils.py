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

LATEST_GITHUB_INIT_FILE = (
    "https://raw.githubusercontent.com/MannLabs/alphapept/"
    "master/alphapept/__init__.py"
)


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
        a log is written to the AlphaPept "logs" folder with the name
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

    try:
        import importlib.metadata
        skip = False
    except ModuleNotFoundError:
        skip = True

    if not skip:
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

    if settings['experiment']['file_paths'] == []:
        raise FileNotFoundError('No files selected')

    logging.info('Checking if files exist.')
    for file in settings['experiment']['file_paths']:
        if file.endswith('.d'):
            check_dir(file)
        else:
            check_file(file)

    fasta_size = 0
    for file in settings['experiment']['fasta_paths']:
        check_file(file)
        fasta_size += get_size_mb(file)

    logging.info(f'FASTA Files have a total size of {fasta_size:.3f} Mb')

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
        if not settings['experiment']['database_path']:
            file_dir = os.path.dirname(settings['experiment']['file_paths'][0])
            settings['experiment']['database_path'] = os.path.normpath(
                os.path.join(file_dir, 'database.hdf')
            )
            logging.info(
                'No database path set and save_db option checked. Using default path {}'.format(settings['experiment']['database_path'])
            )

    if fasta_size > 1: #Only for larger fasta files
        if settings['fasta']['save_db']:
            var_id = ['mods_variable_terminal', 'mods_variable', 'mods_variable_terminal_prot']
            n_var_mods = sum([len(settings['fasta'][_]) for _ in var_id])
            if n_var_mods > 2:
                logging.info(f'Number of variable modifications {n_var_mods} is larger than 2, possibly causing a very large search space. Database will be generated on the fly for the second search.')
                settings['fasta']['save_db'] = False

            protease = settings['fasta']['protease']
            if protease == 'non-specific':
                logging.info(f'Protease is {protease}, possibly causing a very large search space. Adjusting settings.')
                logging.info('Setting save_db to False, Database will be generated on the fly.')
                settings['fasta']['save_db'] = False
                logging.info(f'Ssetting n_missed_cleavages to pep_length_max and fasta_block to 100.')
                settings['fasta']['n_missed_cleavages'] = settings['fasta']['pep_length_max']
                settings['fasta']['fasta_block'] = 100

    if getattr(sys, 'frozen', False):
        logging.info('You are are using the frozen one-click installation.')

        if len(settings['experiment']['file_paths']) > 100:
            logging.info('Processing more than 100 files and using frozen one-click installation version. It is recommended to install the Python version for improved performance.')

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


def check_file(file):
    if not os.path.isfile(file):
        base, ext = os.path.splitext(file)
        if not os.path.isfile(base+'.ms_data.hdf'):
            raise FileNotFoundError(f"{file}")

def get_size_mb(file):
    return os.path.getsize(file)/(1024**2)

def check_dir(dir):
    if not os.path.isdir(dir):
        base, ext = os.path.splitext(dir)
        if not os.path.isfile(base+'.ms_data.hdf'):
            raise FileNotFoundError(f"{dir}")

def delete_file(filename):
    if os.path.isfile(filename):
        os.remove(filename)
        logging.info(f'Deleted {filename}')


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

def check_github_version() -> str:
    """Checks and returns the current version of AlphaPept.
    Parameters
    ----------

    Returns
    -------
    : str
        The version on the AlphaPept GitHub master branch.
        None if no version can be found on GitHub
    """
    import urllib.request
    import urllib.error
    try:
        with urllib.request.urlopen(LATEST_GITHUB_INIT_FILE, timeout=10) as version_file:
            for line in version_file.read().decode('utf-8').split("\n"):
                if line.startswith("__version__"):
                    github_version = line.split()[2][1:-1]
                    return github_version
    except IndexError:
        return None
    except urllib.error.URLError:
        return None
