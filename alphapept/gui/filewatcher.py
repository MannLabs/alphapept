import streamlit as st
from alphapept.paths import FILE_WATCHER_FILE, DEFAULT_SETTINGS_PATH, QUEUE_PATH
from alphapept.gui.utils import check_process, init_process, start_process
from alphapept.settings import load_settings_as_template, save_settings
import os
import time
import datetime
import yaml
import psutil

def check_file_completion(file, minimum_file_size):

    to_analyze = []

    if file.endswith('.d'):
        #Bruker
        to_check = os.path.join(file, 'analysis.tdf_bin')
        while not os.path.isfile(to_check):
            time.sleep(1)
    else:
        to_check = file

    filesize = os.path.getsize(to_check)

    writing = True
    while writing:
        time.sleep(1)
        new_filesize = os.path.getsize(to_check)
        if filesize == new_filesize:
            writing  = False
        else:
            filesize = new_filesize

    if filesize/1024/1024 > minimum_file_size: #bytes, kbytes, mbytes
        to_analyze.append(file)

    return to_analyze



def file_watcher_process(folder, settings_template, minimum_file_size, tag):
    """
    Start the filewatcher process
    """

    from watchdog.observers import Observer
    from watchdog.events import PatternMatchingEventHandler

    patterns = "*"
    ignore_patterns = ""
    ignore_directories = False
    case_sensitive = False
    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)

    def on_created(event):
        print(f"{event.src_path} has been created!")

        file = event.src_path

        if tag != 'None':
            if tag not in file:
                return

        if file.lower().endswith('.raw') or file.lower().endswith('.d'):

            files = check_file_completion(file, minimum_file_size)

            if len(files) > 0:
                settings = settings_template.copy()
                settings['experiment']['file_paths'] = files
                new_file = os.path.splitext(os.path.split(file)[1])[0] + '.yaml'
                settings['experiment']['results_path'] = os.path.splitext(file)[0] + '.yaml'
                save_settings(settings, os.path.join(QUEUE_PATH, new_file))
                print(f'{datetime.datetime.now()} Added {file}')

    print(f'{datetime.datetime.now()} file watcher started.')

    my_event_handler.on_created = on_created

    go_recursively = True
    my_observer = Observer()
    my_observer.schedule(my_event_handler, folder, recursive=go_recursively)

    init_process(FILE_WATCHER_FILE, folder=folder)

    my_observer.start()
    while True:
        time.sleep(1)

def filewatcher():
    st.write('# FileWatcher')

    # FIleWatcher
    running, last_pid, p_name, status, p_init  = check_process(FILE_WATCHER_FILE)

    if running:
        if p_init:
            with open(FILE_WATCHER_FILE, "r") as process_file:
                process = yaml.load(process_file, Loader=yaml.FullLoader)
                path = process['folder']
        else:
            path = None
        st.success(f'PID {last_pid} - {p_name} - {status} - {path}')

        if st.button('Stop file watcher'):
            p_ = psutil.Process(last_pid)
            p_.terminate()
            st.success(f'Terminated {last_pid}')
            raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))
    else:
        st.warning('FileWatcher is currently not running.')

    valid = True
    st.write('AlphaPept can watch folders for new files and automatically add them to the processing queue.')

    folder = st.text_input("Enter folder to watch.", os.getcwd())

    if not os.path.isdir(folder):
        st.error('Not a valid path.')
        valid = False

    minimum_size = st.slider("Minimum file size in MB. Files that are smaller will be ignored.", min_value=1, max_value = 10000, value=200)

    tag = st.text_input("Enter tag to only select files with tag. Keep None for all files. ",'None')

    settings_template = st.text_input("Enter path to a settings template:", DEFAULT_SETTINGS_PATH)
    if not os.path.isfile(settings_template):
        st.error('Not a valid path.')
        valid = False
    else:
        settings_ = load_settings_as_template(settings_template)
        st.success('Valid settings file.')
        if st.checkbox('Show'):
            st.write(settings_)

    if valid:
        start_watcher = st.button('Start file watcher ')
        valid = False

        if start_watcher:
            start_process(target = file_watcher_process, process_file = FILE_WATCHER_FILE, args = (folder, settings_, minimum_size, tag), verbose = True)
            raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))
