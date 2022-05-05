import os
import datetime
from multiprocessing import Process
import time
import yaml
import streamlit as st
import psutil
import pandas as pd
from typing import Callable, Union, Tuple

from alphapept.paths import PROCESSED_PATH
from alphapept.utils import get_size


@st.cache(allow_output_mutation=True)
def load_file(file:str) -> dict:
    """Cached streamlit function to read summary stats from a file.

    Args:
        file (str): List of file paths.

    Returns:
        dict: A dictionary containing the summary of a results.yaml file.
    """
    with open(os.path.join(PROCESSED_PATH, file), "r") as settings_file:
        results = yaml.load(settings_file, Loader=yaml.FullLoader)
    return results

def load_files(file_list: list, callback: Union[Callable, None] = None) -> dict:
    """Read multiple results.yaml files and combine them into a dict.

    Args:
        file_list (list): List of file paths.
        callback (Union[Callable, None], optional): Callback function to report progress. Defaults to None.

    Returns:
        dict: A dictionary containing the summary of all results.yaml files.
    """
    all_results = []

    for idx, _ in enumerate(file_list):
        base, ext = os.path.splitext(_)
        results = load_file(_)

        f = results['summary']['processed_files']

        for f_ in f:
            f__ = os.path.splitext(f_)[0]
            res_ = results['summary'][f__]
            res_['file_in_experiment'] = f__
            res_['experiment'] = base
            all_results.append(res_)

        if callback:
            callback.progress((idx + 1) / len(file_list))

    return pd.DataFrame(all_results)


def filter_by_tag(files: list) -> list:
    """Streamlit widget to filter a list based on a user input.

    Args:
        files (list): List of files to be filtered.
    Returns:
        list: Reduced file list with files containing the tag.
    """
    filter = st.text_input("Filter by name (use & for multiple names)")
    if filter:
        multi = filter.split('&')
        multi = [_.replace(' ', '') for _ in multi]
        st.write(f"Searching for files containing {multi}")
        #files['keep'] = False
        #for tag in multi:
        #    files['keep'].apply.lambda(x)

        #filtered = files[files['file_in_experiment'].str.contains(multi)]
        filtered = files
    else:
        filtered = files

    st.write(f"Remaining {len(filtered)} of {len(files)} files.")

    return filtered


def check_group(filename: str, groups: list) -> Union[str, None]:
    """Helper function to check if a group exists for a given filename.

    Args:
        filename (str): Name of file to be checked.
        groups (list): List of groups.

    Returns:
        Union[str, None]: Returns None if group is not present, else the group name.
    """
    for group in groups:
        if group in filename:
            return group
    return "None"


def escape_markdown(text: str) -> str:
    """Helper function to escape markdown in text.

    Args:
        text (str): Input text.

    Returns:
        str: Converted text to be used in markdown.
    """
    MD_SPECIAL_CHARS = "\`*_{}[]()#+-.!"
    for char in MD_SPECIAL_CHARS:
        text = text.replace(char, "\\" + char)
    return text


def markdown_link(description: str, link: str):
    """Creates a markdown compatible link.

    Args:
        description (str): Description.
        link (str): Target URL.
    """
    _ = f"[{description}]({link})"
    st.markdown(_, unsafe_allow_html=True)


def files_in_folder(folder: str, ending: str, sort: str = "name") -> list:
    """Reads a folder and returns all files that have this ending. Sorts the files by name or creation date.

    Args:
        folder (str): Path to folder.
        ending (str): Ending.
        sort (str, optional): How files should be sorted. Defaults to 'name'.

    Raises:
        NotImplementedError: If a sorting mode is called that is not implemented.

    Returns:
        list: List of files.
    """
    files = [_ for _ in os.listdir(folder) if _.endswith(ending)]

    if sort == "name":
        files.sort()
    elif sort == "date":
        files.sort(key=lambda x: os.path.getctime(os.path.join(folder, x)))
    else:
        raise NotImplementedError

    files = files[::-1]

    return files


def files_in_folder_pandas(folder: str) -> pd.DataFrame:
    """Reads a folder and returns a pandas dataframe containing the files and additional information.
    Args:
        folder (str): Path to folder.

    Returns:
        pd.DataFrame: PandasDataFrame.
    """
    files = os.listdir(folder)
    created = [time.ctime(os.path.getctime(os.path.join(folder, _))) for _ in files]
    sizes = [get_size(os.path.join(folder, _)) / 1024 ** 2 for _ in files]
    df = pd.DataFrame(files, columns=["File"])
    df["Created"] = created
    df["Filesize (Mb)"] = sizes

    return df


def read_log(log_path: str):
    """Reads logfile and removes lines with __.
    Lines with __ are used to indicate progress for the AlphaPept GUI.
    Args:
        log_path (str): Path to the logile.
    """
    if os.path.isfile(log_path):
        with st.expander("Run log"):
            with st.spinner("Parsing file"):
                with open(log_path, "r") as logfile:
                    lines = logfile.readlines()
                    lines = [_ for _ in lines if "__" not in _]
                    st.code("".join(lines))


def start_process(
    target: Callable,
    process_file: str,
    args: Union[list, None] = None,
    verbose: bool = True,
):
    """Function to initiate a process. It will launch the process and save the process id to a yaml file.

    Args:
        target (Callable): Target function for the process.
        process_file (str): Path to the yaml file where the process information will be stored.
        args (Union[list, None], optional): Additional arguments for the process. Defaults to None.
        verbose (bool, optional): Flag to show a stramlit message. Defaults to True.
    """
    process = {}
    now = datetime.datetime.now()
    process["created"] = now
    if args:
        p = Process(target=target, args=args)
    else:
        p = Process(target=target)
    p.start()
    process["pid"] = p.pid

    if verbose:
        st.success(f"Started process PID {p.pid} at {now}")

    with open(process_file, "w") as file:
        yaml.dump(process, file, sort_keys=False)


def check_process(
    process_path: str,
) ->Tuple[bool, Union[str, None], Union[str, None], Union[str, None], bool]:
    """Function to check the status of a process.
    Reads the process file from the yaml and checks the process id.

    Args:
        process_path (str): Path to the process file.

    Returns:
        bool: Flag if process exists.
        Union ([str, None]): Process id if process exists, else None.
        Union ([str, None]): Process name if process exists, else None.
        Union ([str, None]): Process status if process exists, else None.
        bool ([type]): Flag if process was initialized.
    """
    if os.path.isfile(process_path):
        with open(process_path, "r") as process_file:
            process = yaml.load(process_file, Loader=yaml.FullLoader)

        if process:
            last_pid = process["pid"]

            if "init" in process:
                p_init = process["init"]
            else:
                p_init = False

            if psutil.pid_exists(last_pid):
                p_ = psutil.Process(last_pid)
                with p_.oneshot():
                    p_name = p_.name()
                    status = p_.status()
                return True, last_pid, p_name, status, p_init

    return False, None, None, None, False


def init_process(process_path: str, **kwargs: dict):
    """Waits until a process file is created and then writes an init flag to the file

    Args:
        process_path (str): Path to process yaml.
    """
    while True:
        if os.path.isfile(process_path):
            with open(process_path, "r") as process_file:
                process = yaml.load(process_file, Loader=yaml.FullLoader)
            process["init"] = True
            for _ in kwargs:
                process[_] = kwargs[_]
            with open(process_path, "w") as file:
                yaml.dump(process, file, sort_keys=False)
            break
        else:
            time.sleep(1)


def check_file(path: str) -> bool:
    """Function to check if a file exists.
    This function will also return if the file is None.

    Args:
        path (str): Path to the file to be checked.

    Returns:
        bool: Flag if file or path exists..
    """

    if path:
        if os.path.isfile(path):
            return True
        else:
            return False
    else:
        return False

def compare_date(date: str, minimum_date: datetime) -> bool:
    """Utility function to convert the acquisition date time to a datetime format.
    Checks if it was before the minimum_date.

    Args:
        date (str): Datetime as string.
        minimum_date (dateime): Comparison

    Returns:
        bool: Flag if file was acquired after the minimum date.
    """

    if not date:
        return False

    if date.endswith('Z'):
        rem = date.split('.')[1]

        if len(rem) == 8:
            date = date[:-2]+'Z'

        dt = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')

    else:
        dt = datetime.datetime.fromisoformat(date).replace(tzinfo=None)

    if dt > minimum_date:
        return True
    else:
        return False
