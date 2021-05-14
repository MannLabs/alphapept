import os
import datetime
import yaml
import streamlit as st
from multiprocessing import Process
import psutil
import time
import pandas as pd

def escape_markdown(text):
    """
    Escape markdown
    """
    MD_SPECIAL_CHARS = "\`*_{}[]()#+-.!"
    for char in MD_SPECIAL_CHARS:
        text = text.replace(char, "\\"+char)
    return text

def files_in_folder(folder, ending, sort='name'):
    """
    Reads a folder and returns all files that have this ending. Sorts the files by name or creation date.
    """
    files = [_ for _ in os.listdir(folder) if _.endswith(ending)]

    if sort == 'name':
        files.sort()
    elif sort == 'date':
        files.sort(key=lambda x: os.path.getctime(os.path.join(folder, x)))
    else:
        raise NotImplementedError

    files = files[::-1]

    return files

def files_in_folder_pandas(folder):
    """
    Reads a folder and returns pandas dataframe
    """
    files = os.listdir(folder)
    created = [time.ctime(os.path.getctime(os.path.join(folder, _))) for _ in files]
    sizes = [os.path.getsize(os.path.join(folder, _))/1024**2 for _ in files]
    df = pd.DataFrame(files, columns = ['File'])
    df['Created'] = created
    df['Filesize (Mb)'] = sizes

    return df

def read_log(log_path):
    """
    Reads logfile cleanly (i.e. removing lines with __ which are used for progress)
    """
    if os.path.isfile(log_path):
        with st.beta_expander("Run log"):
            with st.spinner('Parsing file'):
                with open(log_path, "r") as logfile:
                    lines = logfile.readlines()
                    lines = [_ for _ in lines if '__' not in _]
                    st.code(''.join(lines))


def start_process(target, process_file, args = None, verbose = True):
    process = {}
    now = datetime.datetime.now()
    process['created'] = now
    if args:
        p = Process(target=target, args = args)
    else:
        p = Process(target=target)
    p.start()
    process['pid'] = p.pid

    if verbose:
        st.success(f'Started process PID {p.pid} at {now}')

    with open(process_file, "w") as file:
        yaml.dump(process, file, sort_keys=False)

def check_process(process_path):
    if os.path.isfile(process_path):
        with open(process_path, "r") as process_file:
            process = yaml.load(process_file, Loader=yaml.FullLoader)
        last_pid = process['pid']

        if 'init' in process:
            p_init = process['init']
        else:
            p_init = False

        if psutil.pid_exists(last_pid):
            p_ = psutil.Process(last_pid)
            with p_.oneshot():
                p_name = p_.name()
                status = p_.status()
            return True, last_pid, p_name, status, p_init

    return False, None, None, None, False

def init_process(process_path, **kwargs):
    """
    Waits until a process file is created and then writes an init flag to the file
    """
    while True:
        if os.path.isfile(process_path):
            with open(process_path, "r") as process_file:
                p = yaml.load(process_file, Loader=yaml.FullLoader)
            p['init'] = True
            for _ in kwargs:
                p[_] = kwargs[_]
            with open(process_path, "w") as file:
                yaml.dump(p, file, sort_keys=False)
            break
        else:
            time.sleep(1)
