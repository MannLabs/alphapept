import streamlit as st
from alphapept.gui.utils import (
    check_process,
    init_process,
    start_process,
    escape_markdown,
)
from alphapept.paths import PROCESSED_PATH, PROCESS_FILE, QUEUE_PATH, FAILED_PATH
from alphapept.settings import load_settings_as_template, save_settings
import os
import psutil
import datetime
import pandas as pd
import time
import yaml
import alphapept.interface


def queue_watcher():
    """
    Start the queue_watcher.
    """
    # This is in pool and should be reporting.
    print(f"{datetime.datetime.now()} Started queue_watcher")

    init_process(PROCESS_FILE)

    while True:
        queue_files = [_ for _ in os.listdir(QUEUE_PATH) if _.endswith(".yaml")]
        # print(f'{datetime.datetime.now()} queue_watcher running. {len(queue_files)} experiments to process.')

        if len(queue_files) > 0:

            try:
                created = [
                    time.ctime(os.path.getctime(os.path.join(QUEUE_PATH, _)))
                    for _ in queue_files
                ]
            except FileNotFoundError: #File moved / deleted.
                break
            queue_df = pd.DataFrame(queue_files, columns=["File"])
            queue_df["Created"] = created

            file_to_process = queue_df.sort_values("Created")["File"].iloc[0]

            file_path = os.path.join(QUEUE_PATH, file_to_process)
            settings = load_settings_as_template(file_path)

            current_file = {}
            current_file["started"] = datetime.datetime.now()
            current_file["file"] = file_to_process

            current_file_path = os.path.join(QUEUE_PATH, "current_file")

            with open(current_file_path, "w") as file:
                yaml.dump(current_file, file, sort_keys=False)

            logfile = os.path.join(
                PROCESSED_PATH, os.path.splitext(file_to_process)[0] + ".log"
            )
            try:
                settings_ = alphapept.interface.run_complete_workflow(
                    settings, progress=True, logfile=logfile
                )
                save_settings(settings_, os.path.join(PROCESSED_PATH, file_to_process))

            except Exception as e:
                print(f"Run {file_path} failed with {e}")
                settings_ = settings.copy()
                settings_["error"] = f"{e}"
                save_settings(settings_, os.path.join(FAILED_PATH, file_to_process))


            if os.path.isfile(current_file_path):
                os.remove(current_file_path)
            os.remove(file_path)

        else:
            time.sleep(15)


def terminate_process():

    with st.spinner("Terminating processes.."):

        running, last_pid, p_name, status, queue_watcher_state = check_process(
            PROCESS_FILE
        )

        parent = psutil.Process(last_pid)
        procs = parent.children(recursive=True)
        for p in procs:
            p.terminate()
        gone, alive = psutil.wait_procs(procs, timeout=3)
        for p in alive:
            p.kill()

        parent.terminate()
        parent.kill()

        st.success(f"Terminated {last_pid}")

        current_file = os.path.join(QUEUE_PATH, "current_file")

        if os.path.isfile(current_file):

            with open(current_file, "r") as file:
                cf_ = yaml.load(file, Loader=yaml.FullLoader)

            cf = cf_["file"]
            file_in_process = os.path.join(QUEUE_PATH, cf)
            target_file = os.path.join(FAILED_PATH, cf)

            os.rename(file_in_process, target_file)
            st.success(
                f"Moved {escape_markdown(file_in_process)} to {escape_markdown(target_file)}"
            )

            os.remove(current_file)
            st.success(f"Cleaned up {escape_markdown(current_file)}")

        time.sleep(3)
        st.success('Please refresh page')
        st.stop()


def status():

    st.write("# Status")
    st.text(
        f"This page shows the status of the current analysis.\nSwitch to `New experiment` to define a new experiment.\nSwitch to `Results` to see previous results."
    )
    status_msg = st.empty()
    failed_msg = st.empty()

    current_log = ""
    log_txt = []

    st.write("## Progress")

    overall_txt = st.empty()

    overall_txt.text("Overall: 0%")
    overall = st.progress(0)

    task = st.empty()
    task.text("Current task: None")

    current_p = st.empty()
    current_p.text("Current progess: 0%")

    current = st.progress(0)

    last_log = st.empty()

    st.write("## Hardware utilization")

    c1,c2 = st.columns(2)
    c1.text("Ram")
    ram = c1.progress(0)
    c2.text("CPU")
    cpu = c2.progress(0)

    running, last_pid, p_name, status, queue_watcher_state = check_process(PROCESS_FILE)



    if not running:
        start_process(target=queue_watcher, process_file=PROCESS_FILE, verbose=False)
        st.warning(
            "Initializing Alphapept and waiting for process to start. Please refresh page in a couple of seconds."
        )

    if not queue_watcher_state:
        with st.spinner('Waiting for AlphaPept process to start.'):
            while not queue_watcher_state:
                running, last_pid, p_name, status, queue_watcher_state = check_process(PROCESS_FILE)

        time.sleep(1)
        st.success('Please refresh this page.')
        st.stop()


    current_file = os.path.join(QUEUE_PATH, "current_file")

    with st.expander(f"Full log "):
        log_ = st.empty()

    with st.expander(f"Queue"):
        queue_table = st.empty()

    with st.expander(f"Failed"):
        failed_table = st.empty()

    if st.checkbox("Terminate process"):
        st.error(
            f"This will abort the current run and move it to failed. Please confirm."
        )
        if st.button("Confirm"):
            terminate_process()

    while True:
        ram.progress(
            1 - psutil.virtual_memory().available / psutil.virtual_memory().total
        )
        cpu.progress(psutil.cpu_percent() / 100)

        queue_files = [_ for _ in os.listdir(QUEUE_PATH) if _.endswith(".yaml")]
        failed_files = [_ for _ in os.listdir(FAILED_PATH) if _.endswith(".yaml")]
        n_failed = len(failed_files)
        n_queue = len(queue_files)

        if n_queue == 0:
            status_msg.success(
                f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")} No files to process. Please add new experiments.'
            )
            current.progress(0)
            overall.progress(0)
            overall_txt.text("Overall: 0%")
            task.text("None")
            last_log.code("")

            queue_table.table(pd.DataFrame())

        else:
            if os.path.isfile(current_file):
                with open(current_file, "r") as file:
                    cf_ = yaml.load(file, Loader=yaml.FullLoader)

                cf = cf_["file"]
                cf_start = cf_["started"]
                now = datetime.datetime.now()
                delta = f"{now-cf_start}".split('.')[0]
                status_msg.success(
                    f'{now.strftime("%d.%m.%Y %H:%M:%S")} Processing {escape_markdown(cf)}. Time elapsed {delta}'
                )

                logfile = os.path.join(PROCESSED_PATH, os.path.splitext(cf)[0] + ".log")
                if current_log != logfile:
                    current_log = logfile
                    log_txt = []
                    f = open(logfile, "r")

                lines = f.readlines()[-200:]  # Limit to 200 lines

                for line in lines:
                    if "__progress_current" in line:
                        current_p_ = float(line.split("__progress_current ")[1][:5])
                        current.progress(current_p_)

                        current_p.text(f"Current progress: {current_p_*100:.2f}%")
                    elif "__progress_overall" in line:

                        overall_p = float(line.split("__progress_overall ")[1][:5])
                        overall.progress(overall_p)

                        overall_txt.text(f"Overall: {overall_p*100:.2f}%")
                    elif "__current_task" in line:
                        task_ = line.strip("\n").split("__current_task ")[1]
                        task.text(f"Current task: {task_}")
                    else:
                        log_txt.append(line)

                    last_log.code("".join(log_txt[-3:]))
                    log_.code("".join(log_txt))

            created = [
                time.ctime(os.path.getctime(os.path.join(QUEUE_PATH, _)))
                for _ in queue_files
            ]
            queue_df = pd.DataFrame(queue_files, columns=["File"])
            queue_df["Created"] = created

            queue_table.table(queue_df)

        if n_failed == 1:
            failed_msg.error(f"{n_failed} run failed. Please check {FAILED_PATH}.")
        elif n_failed > 1:
            failed_msg.error(f"{n_failed} runs failed. Please check {FAILED_PATH}.")

        failed_table.table(pd.DataFrame(failed_files))
        time.sleep(0.4)
