import streamlit as st
from alphapept.gui.utils import files_in_folder, read_log, check_process, init_process, start_process, escape_markdown
from alphapept.paths import PROCESSED_PATH, PROCESS_FILE, QUEUE_PATH, FAILED_PATH
from alphapept.settings import load_settings, load_settings_as_template, save_settings
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
    #This is in pool and should be reporting.
    print(f'{datetime.datetime.now()} Started queue_watcher')

    init_process(PROCESS_FILE)


    while True:
        queue_files = [_ for _ in os.listdir(QUEUE_PATH) if _.endswith('.yaml')]
        #print(f'{datetime.datetime.now()} queue_watcher running. {len(queue_files)} experiments to process.')

        if len(queue_files) > 0:
            file_path = os.path.join(QUEUE_PATH, queue_files[0])
            settings = load_settings_as_template(file_path)

            current_file = {}
            current_file['started'] = datetime.datetime.now()
            current_file['file'] = queue_files[0]

            current_file_path = os.path.join(QUEUE_PATH, 'current_file')

            with open(current_file_path, "w") as file:
                yaml.dump(current_file, file, sort_keys=False)

            logfile = os.path.join(PROCESSED_PATH, os.path.splitext(queue_files[0])[0]+'.log')
            try:
                settings_ = alphapept.interface.run_complete_workflow(settings, progress=True, logfile = logfile)
                save_settings(settings_, os.path.join(PROCESSED_PATH, queue_files[0]))

            except Exception as e:
                print(f'Run {file_path} failed with {e}')
                settings_ = settings.copy()
                settings_['error'] = f"{e}"
                save_settings(settings_, os.path.join(FAILED_PATH, queue_files[0]))

            os.remove(file_path)
            if os.path.isfile(current_file_path):
                os.remove(current_file_path)
        else:
            time.sleep(15)

def status():

    st.write("# Status")
    st.text(f'This page shows the status of the current analysis.\nSwitch to `New experiment` to define a new experiment')
    status_msg = st.empty()
    failed_msg = st.empty()

    current_log = ''
    log_txt = []

    st.write("## Progress")

    overall_txt = st.empty()

    overall_txt.text('Overall: 0%')
    overall = st.progress(0)

    task = st.empty()
    task.text('Current task: None')

    current_p = st.empty()
    current_p.text('Current progess: 0%')

    current = st.progress(0)

    last_log = st.empty()

    st.write("## Hardware utilization")

    st.text('Ram')
    ram = st.progress(0)
    st.text('CPU')
    cpu = st.progress(0)

    running, last_pid, p_name, status, queue_watcher_state = check_process(PROCESS_FILE)

    if not running:
        start_process(target = queue_watcher, process_file= PROCESS_FILE, verbose=False)
        st.warning('Initializing Alphapept and waiting for process to start. Please refresh page in a couple of seconds.')
    elif not queue_watcher_state:
        st.warning('Initializing Alphapept and waiting for process to start. Please refresh page in a couple of seconds.')
    else:
        current_file = os.path.join(QUEUE_PATH, 'current_file')

        with st.beta_expander(f"Full log "):
            log_ = st.empty()

        with st.beta_expander(f"Queue"):
            queue_table = st.empty()

        with st.beta_expander(f"Failed"):
            failed_table = st.empty()

        refresh = st.checkbox('Auto-Update Page')

        while True:
            if os.path.isfile(current_file):
                with open(current_file, "r") as file:
                    cf_ = yaml.load(file, Loader=yaml.FullLoader)

                cf = cf_['file']
                cf_start = cf_['started']
                status_msg.success(f'Processing {escape_markdown(cf)}. Started at {cf_start}')

                logfile = os.path.join(PROCESSED_PATH, os.path.splitext(cf)[0]+'.log')
                if current_log != logfile:
                    current_log = logfile
                    log_txt = []
                    f = open(logfile, "r")

                lines = f.readlines()[:200] # Limit to 200 lines 

                for line in lines:
                    if '__progress_current' in line:
                        current_p_ = float(line.split('__progress_current ')[1][:5])
                        current.progress(current_p_)

                        current_p.text(f'Current progress: {current_p_*100:.2f}%')
                    elif '__progress_overall' in line:

                        overall_p = float(line.split('__progress_overall ')[1][:5])
                        overall.progress(overall_p)

                        overall_txt.text(f'Overall: {overall_p*100:.2f}%')
                    elif '__current_task' in line:
                        task_ = line.strip('\n').split('__current_task ')[1]
                        task.text(f'Current task: {task_}')
                    else:
                        log_txt.append(line)

                    last_log.code(''.join(log_txt[-3:]))
                    log_.code(''.join(log_txt))

            ram.progress(1-psutil.virtual_memory().available/psutil.virtual_memory().total)
            cpu.progress(psutil.cpu_percent()/100)

            queue_files = [_ for _ in os.listdir(QUEUE_PATH) if _.endswith('.yaml')]
            failed_files = [_ for _ in os.listdir(FAILED_PATH) if _.endswith('.yaml')]
            n_failed = len(failed_files)
            n_queue = len(queue_files)

            if n_queue == 0:
                status_msg.success(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")} No files to process. Please add new experiments.')
                current.progress(0)
                overall.progress(0)
                overall_txt.text('Overall: 0%')
                task.text('None')

                queue_table.table(pd.DataFrame())

            else:
                created = [time.ctime(os.path.getctime(os.path.join(QUEUE_PATH, _))) for _ in queue_files]
                queue_df = pd.DataFrame(queue_files, columns = ['File'])
                queue_df['Created'] = created

                queue_table.table(queue_df)

            if n_failed == 1:
                failed_msg.error(f'{n_failed} run failed. Please check {FAILED_PATH}.')
            elif n_failed > 1:
                failed_msg.error(f'{n_failed} runs failed. Please check {FAILED_PATH}.')

            failed_table.table(pd.DataFrame(failed_files))
            time.sleep(0.2)

            if not refresh:
                break
