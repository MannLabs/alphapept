import os
import time
import datetime
import yaml
import psutil

import streamlit as st
from alphapept.paths import FILE_WATCHER_FILE, DEFAULT_SETTINGS_PATH, QUEUE_PATH
from alphapept.gui.utils import check_process, init_process, start_process
from alphapept.utils import get_size
from alphapept.settings import load_settings_as_template, save_settings


def check_file_completion(file: str, minimum_file_size: float) -> list:
    """Checks if a file is being written or complete.

    Args:
        file (str): Path to the file that should be checked.
        minimum_file_size (float): Minimum file size in Mb.

    Returns:
        list: A list of files that are considered complete.
    """

    to_analyze = []

    filesize = get_size(file)

    writing = True
    while writing:
        time.sleep(5)
        new_filesize = get_size(file)
        if filesize == new_filesize:
            writing = False
        else:
            filesize = new_filesize

    if filesize / 1024 / 1024 > minimum_file_size:  # bytes, kbytes, mbytes
        if file.endswith(".d"):  # Check if required subfiles exist for bruker
            for subfile in ["analysis.tdf_bin", "analysis.tdf"]:
                if not os.path.isfile(os.path.join(file, subfile)):
                    print(f"No {subfile} found. Skipping {file}.")
                    return to_analyze
        to_analyze.append(file)

    return to_analyze


def file_watcher_process(
    folder: str, settings_template: dict, minimum_file_size: float, tag: str
):
    """Function to start a filewatcher process.
    It uses the PatternMatchEventHandler to look for new files.

    Args:
        folder (str): Path to the folder to be checked.
        settings_template (dict): Dictionary containing settings.
        minimum_file_size (fliat): Minimum file size.
        tag (str): Dedicated tag to only watch for files with the tag.
    """
    from watchdog.observers import Observer
    from watchdog.events import PatternMatchingEventHandler

    patterns = "*"
    ignore_patterns = ""
    ignore_directories = False
    case_sensitive = False
    my_event_handler = PatternMatchingEventHandler(
        patterns, ignore_patterns, ignore_directories, case_sensitive
    )

    def on_created(event):
        print(f"New file {event.src_path} in folder.")
        file = event.src_path

        if tag != "None":
            if tag not in file:
                return

        if os.path.split(file)[0].endswith(".d"):
            file = os.path.split(file)[0]
            print(f"File could belong to bruker file. Checking main folder {file}")
            new_file = os.path.splitext(os.path.split(file)[1])[0] + ".yaml"
            queue_file = os.path.join(QUEUE_PATH, new_file)
            if os.path.isfile(queue_file):
                print("File exists in queue already. Skipping.")
                return

        if file.lower().endswith(".raw") or file.lower().endswith(".d"):

            print(f"Checking if {file} is complete")
            files = check_file_completion(file, minimum_file_size)

            if len(files) > 0:
                settings = settings_template.copy()
                settings["experiment"]["file_paths"] = files
                new_file = os.path.splitext(os.path.split(file)[1])[0] + ".yaml"
                settings["experiment"]["results_path"] = (
                    os.path.splitext(file)[0] + ".yaml"
                )

                queue_file = os.path.join(QUEUE_PATH, new_file)

                if os.path.isfile(queue_file):
                    print("File exists in queue already. Skipping.")
                else:
                    save_settings(settings, queue_file)
                    print(f"{datetime.datetime.now()} Added {file} as {queue_file}")

    print(f"{datetime.datetime.now()} file watcher started.")

    my_event_handler.on_created = on_created

    go_recursively = True
    my_observer = Observer()
    my_observer.schedule(my_event_handler, folder, recursive=go_recursively)

    init_process(FILE_WATCHER_FILE, folder=folder)

    my_observer.start()
    while True:
        time.sleep(1)


def filewatcher():
    """Streamlit page to launch the file watcher."""
    st.write("# FileWatcher")

    # FileWatcher
    running, last_pid, p_name, status, p_init = check_process(FILE_WATCHER_FILE)

    if running:
        if p_init:
            with open(FILE_WATCHER_FILE, "r") as process_file:
                process = yaml.load(process_file, Loader=yaml.FullLoader)
                path = process["folder"]
        else:
            path = None
        st.success(f"PID {last_pid} - {p_name} - {status} - {path}")

        if st.button("Stop file watcher"):
            process = psutil.Process(last_pid)
            process.terminate()
            st.success(f"Terminated {last_pid}. Please refresh page.")
            st.stop()
    else:
        st.warning("FileWatcher is currently not running.")

    valid = True
    st.write(
        "AlphaPept can watch folders for new files and automatically add them to the processing queue."
    )

    folder = st.text_input("Enter folder to watch.", os.getcwd())

    if not os.path.isdir(folder):
        st.error("Not a valid path.")
        valid = False

    minimum_size = st.slider(
        "Minimum file size in MB. Files that are smaller will be ignored.",
        min_value=1,
        max_value=10000,
        value=200,
    )

    tag = st.text_input(
        "Enter tag to only select files with tag. Keep None for all files. ", "None"
    )

    settings_template = st.text_input(
        "Enter path to a settings template:", DEFAULT_SETTINGS_PATH
    )
    if not os.path.isfile(settings_template):
        st.error("Not a valid path.")
        valid = False
    else:
        settings_ = load_settings_as_template(settings_template)
        st.success("Valid settings file.")
        with st.expander("Show settings"):
            st.write(settings_)

    st.write("## Start watcher")

    if valid:
        process_existing = st.checkbox("Process already existing files.")

        if st.button("Start"):

            if process_existing:
                raw_files = [
                    _
                    for _ in os.listdir(folder)
                    if _.lower().endswith(".raw") or _.lower().endswith(".d")
                ]
                st.success(f"Found {len(raw_files)} existing raw files.")

                current = st.progress(0)

                for idx, file in enumerate(raw_files):
                    file = os.path.join(folder, file)
                    settings = settings_.copy()
                    settings["experiment"]["file_paths"] = [file]
                    new_file = os.path.splitext(os.path.split(file)[1])[0] + ".yaml"
                    settings["experiment"]["results_path"] = (
                        os.path.splitext(file)[0] + ".yaml"
                    )
                    save_settings(settings, os.path.join(QUEUE_PATH, new_file))
                    print(f"{datetime.datetime.now()} Added {file}")

                    current.progress((idx + 1) / len(raw_files))

            start_process(
                target=file_watcher_process,
                process_file=FILE_WATCHER_FILE,
                args=(folder, settings_, minimum_size, tag),
                verbose=True,
            )
            valid = False
            st.success('Please refresh page.')
            st.stop()
