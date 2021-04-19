import streamlit as st
import os
import psutil
import pandas as pd
import yaml
import time
import matplotlib.pyplot as plt
import alphapept.io
from multiprocessing import Process
from datetime import datetime
from alphapept.settings import load_settings, save_settings
import alphapept.interface
import base64


_this_file = os.path.abspath(__file__)
_this_directory = os.path.dirname(_this_file)

DEFAULT_SETTINGS_PATH = os.path.join(_this_directory, 'default_settings.yaml')
SETTINGS_TEMPLATE_PATH = os.path.join(_this_directory, 'settings_template.yaml')

SETTINGS_TEMPLATE = load_settings(SETTINGS_TEMPLATE_PATH)

HOME = os.path.expanduser("~")

QUEUE_PATH = os.path.join(HOME, "alphapept", "queue")
PROCESSED_PATH = os.path.join(HOME, "alphapept", "finished")
PROCESS_FILE = os.path.join(QUEUE_PATH, 'process')
FILE_WATCHER_FILE = os.path.join(QUEUE_PATH, 'file_watcher')

for folder in [QUEUE_PATH, PROCESSED_PATH]:
    if not os.path.isdir(folder):
        os.mkdir(folder)

def check_new_files(path):
    """
    Check for new files in folder
    """
    new_files = []

    for dirpath, dirnames, filenames in os.walk(path):

        for dirname in [d for d in dirnames if d.endswith('.d')]: #Bruker
            new_file = os.path.join(dirpath, dirname)
            base, ext = os.path.splitext(dirname)
            hdf_path = os.path.join(dirpath, base+'.ms_data.hdf')

            if not os.path.exists(hdf_path):
                new_files.append(new_file)

        for filename in [f for f in filenames if f.lower().endswith('.raw')]: #Thermo
            new_file = os.path.join(dirpath, filename)
            base, ext = os.path.splitext(filename)
            hdf_path = os.path.join(dirpath, base+'.ms_data.hdf')

            if not os.path.exists(hdf_path):
                new_files.append(new_file)

    return new_files


def check_file_completion(list_of_files, minimum_file_size):
    to_analyze = []
    for file in list_of_files:

        if file.endswith('.d'):
            #Bruker
            to_check = os.path.join(file, 'analysis.tdf_bin')
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

def history():
    """
    Plot history of previous experiments
    """
    st.write("# History")
    st.text(f'History allows to visualize summary information from multiple previous analysis.'
    f'\nIt checks {PROCESSED_PATH} for *.yaml files.'
    '\nFiles can be filtered to only include a subset.')

    processed_files = [_ for _ in os.listdir(PROCESSED_PATH) if _.endswith('.yaml')]
    with st.beta_expander(f"Processed files ({len(processed_files)})"):
        st.table(processed_files)

    filter = st.text_input('Filter')

    if filter:
        filtered = [_ for _ in processed_files if filter in _]
    else:
        filtered = processed_files

    st.write(f"Remaining {len(filtered)} of {len(processed_files)} files.")
    bar = st.progress(0)

    all_results = {}

    for idx, _ in enumerate(filtered):
        with open(os.path.join(PROCESSED_PATH, _), "r") as settings_file:
            results = yaml.load(settings_file, Loader=yaml.FullLoader)

            all_results[_] = results

        bar.progress((idx+1)/len(filtered))

    if len(all_results) > 0:
        options = ['timing', 'feature_table','protein_fdr']

        plots = st.multiselect('Plots', options = options, default=options)

        with st.spinner('Creating plots..'):
            for plot in plots:
                plot_dict = {} # summary_time
                if plot == 'timing':
                    for _ in all_results.keys():
                        plot_dict[_] = all_results[_]["summary"]["timing"]["total"]
                else:
                    for _ in all_results.keys():
                        file = os.path.splitext(all_results[_]['summary']['processed_files'][0])[0]
                        try:
                            plot_dict[_] = all_results[_]["summary"][file][plot]
                        except KeyError:
                            plot_dict[_] = 0

                fig = plt.figure(figsize=(10,3))
                plt.bar(range(len(plot_dict)), list(plot_dict.values()), align='center')
                plt.xticks(range(len(plot_dict)), list(plot_dict.keys()), rotation='vertical')
                plt.title(plot)
                st.write(fig)


        if False:
            plot_dict[_] = results['summary']['timing'][field]

            fig = plt.figure(figsize=(10,3))
            plt.bar(range(len(plot_dict)), list(plot_dict.values()), align='center')
            plt.xticks(range(len(plot_dict)), list(plot_dict.keys()))
            plt.title(field)
            st.write(fig)

def queue_watcher():
    """
    Start the queue_watcher.
    """
    #This is in pool and should be reporting.
    print(f'{datetime.now()} Started queue_watcher')

    while True:
        if os.path.isfile(PROCESS_FILE):
            with open(PROCESS_FILE, "r") as process_file:
                p = yaml.load(process_file, Loader=yaml.FullLoader)
            p['init'] = True
            with open(PROCESS_FILE, "w") as file:
                yaml.dump(p, file, sort_keys=False)
            break
        else:
            time.sleep(1)

    while True:
        queue_files = [_ for _ in os.listdir(QUEUE_PATH) if _.endswith('.yaml')]
        print(f'{datetime.now()} queue_watcher running. {len(queue_files)} experiments to process.')

        if len(queue_files) > 0:
            file_path = os.path.join(QUEUE_PATH, queue_files[0])
            settings = load_settings(file_path)

            current_file = {}
            current_file['started'] = datetime.now()
            current_file['file'] = queue_files[0]

            current_file_path = os.path.join(QUEUE_PATH, 'current_file')

            with open(current_file_path, "w") as file:
                yaml.dump(current_file, file, sort_keys=False)

            logfile = os.path.join(PROCESSED_PATH, os.path.splitext(queue_files[0])[0]+'.log')
            settings_ = alphapept.interface.run_complete_workflow(settings, progress=True, logfile = logfile)
            save_settings(settings_, os.path.join(PROCESSED_PATH, queue_files[0]))
            os.remove(file_path)

            if os.path.isfile(current_file_path):
                os.remove(current_file_path)

        else:
            time.sleep(15)


def file_watcher(folder, settings_template, minimum_file_size, tag):
    """
    Start the file Watcher

    """

    already_added = []

    print(f'{datetime.now()} file watcher started.')

    while True:
        if os.path.isfile(FILE_WATCHER_FILE):
            with open(FILE_WATCHER_FILE, "r") as process_file:
                p = yaml.load(process_file, Loader=yaml.FullLoader)
            p['init'] = True
            p['folder'] = folder
            with open(FILE_WATCHER_FILE, "w") as file:
                yaml.dump(p, file, sort_keys=False)
            break
        else:
            time.sleep(1)

    while True:
        new_files = check_file_completion(check_new_files(folder), minimum_file_size)

        if tag != 'None':
            new_files = [_ for _ in new_files if tag in _]

        new_files = [_ for _ in new_files if _ not in already_added]

        already_added = new_files

        print(f'{datetime.now()} file watcher running. {len(new_files)} new files.')

        if len(new_files) > 0:

            for file in new_files:
                settings = settings_template.copy()

                settings['experiment']['file_paths'] = [file]
                settings['experiment']['results_path'] = ''

                new_file = os.path.splitext(os.path.split(file)[1])[0] + '.yaml'

                save_settings(settings, os.path.join(QUEUE_PATH, new_file))

                print(f'{datetime.now()} Added {file}')

        else:
            time.sleep(60*5)


def start_process(target, process_file, args = None, verbose = True):
    process = {}
    now = datetime.now()
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


def system():

    st.write("# System")
    st.text(f'This page shows system status and settings and allows to launch a file watcher.')
    st.write('## General')

    # Main Process
    running, last_pid, p_name, status, p_init  = check_process(PROCESS_FILE)

    if running:
        st.success(f'PID {last_pid} - {p_name} - {status}')

        if st.button('Stop'):
            p_ = psutil.Process(last_pid)
            p_.terminate()
            st.success(f'Terminated {last_pid}')
            raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))
    else:
        st.warning('No running AlphaPept process found. Please start.')
        if st.button('Start'):
            start_process(target = queue_watcher, process_file= PROCESS_FILE)
            raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))


    with st.beta_expander(f"System paths "):
        st.code(f"queue \t\t {QUEUE_PATH}")
        st.code(f"processed \t {PROCESSED_PATH}")

    with st.beta_expander(f"File watcher "):
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
            st.warning('No running FileWatcher process found. Please start.')

        valid = True
        st.write('AlphaPept can watch folders for new files and automatically add them to the processing queue.')

        folder = st.text_input("Enter path to folder to watch.", os.getcwd())

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
            settings_ = load_settings(settings_template)
            st.success('Valid settings file.')
            if st.checkbox('Show'):
                st.write(settings_)

        if valid:
            start_watcher = st.button('Start file watcher ')
            valid = False

            if start_watcher:
                start_process(target = file_watcher, process_file = FILE_WATCHER_FILE, args = (folder, settings_, minimum_size, tag), verbose = True)
                raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))




def status():

    st.write("# Status")
    st.text(f'This page shows the status of the current analysis.\nSwitch to `New experiment` to define a new experiment')
    status_msg = st.empty()

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

        refresh = st.checkbox('Auto-Update Page')

        while True:
            if os.path.isfile(current_file):
                with open(current_file, "r") as file:
                    cf_ = yaml.load(file, Loader=yaml.FullLoader)

                cf = cf_['file']
                cf_start = cf_['started']
                status_msg.success(f'Processing {cf}. Started at {cf_start}')

                logfile = os.path.join(PROCESSED_PATH, os.path.splitext(cf)[0]+'.log')
                if current_log != logfile:
                    current_log = logfile
                    log_txt = []
                    f = open(logfile, "r")

                for line in f.readlines():
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
            n_queue = len(queue_files)

            if n_queue == 0:
                status_msg.success(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")} No files to process. Please add new experiments.')
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

            time.sleep(0.2)

            if not refresh:
                break

def get_table_download_link(df, name):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(
        csv.encode()
    ).decode()  # some strings <-> bytes conversions necessary here

    href = f'<a href="data:file/csv;base64,{b64}" download="%{name}" >Download as *.csv</a>'
    st.markdown('')
    st.markdown(href, unsafe_allow_html=True)


def result():
    st.write("# Results")

    st.text("This page allows to explore the analysis results.\nAlphaPept uses the HDF container format which can be accessed here.")

    #TOdo: include previously processed output files..

    selection = st.selectbox('File selection', ('Previous results', 'Enter file'))

    file = ''

    if selection == 'Previous results':
        results_files = [_ for _ in os.listdir(PROCESSED_PATH) if _.endswith('.yaml')]

        results_files.sort()

        results_files = results_files[::-1]


        with st.beta_expander(f"Total {len(results_files)} Files"):
            st.table(results_files)

        st.write('### Select results file')

        selection = st.selectbox('Run', results_files)

        if selection:

            with open(os.path.join(PROCESSED_PATH, selection), "r") as settings_file:
                results = yaml.load(settings_file, Loader=yaml.FullLoader)

            with st.beta_expander(f"Run summary"):
                st.write(results['summary'])

            log_path = os.path.join(PROCESSED_PATH, os.path.splitext(selection)[0]+'.log')

            if os.path.isfile(log_path):
                with st.beta_expander(f"Run log"):
                    with open(log_path, "r") as logfile:
                        lines = logfile.readlines()
                        st.code(''.join(lines))


            raw_files = [os.path.splitext(_)[0]+'.ms_data.hdf' for _ in results['experiment']['file_paths']]

            #TODO: add results.hdf file
            raw_files = raw_files + [results['experiment']['results_path']]

            raw_files = [_ for _ in raw_files if os.path.exists(_)]

            st.write('### Select file from Experiment')
            file = st.selectbox('Select file from experiment', raw_files)

    elif selection == 'Enter file':
        file = st.text_input("Enter path to hdf file.", os.getcwd())
    else:
        file = ''

    if file is None:
        file = ''

    if not os.path.isfile(file):
        st.warning('Not a valid file.')
    else:
        with st.spinner('Parsing file'):

            pandas_hdf = False

            try:
                ms_file = alphapept.io.MS_Data_File(file)
                options = [_ for _ in ms_file.read() if _ != "Raw"]
            except KeyError:
                pandas_hdf = True

                with pd.HDFStore(file) as hdf:
                    options = list(hdf.keys())

            opt = st.selectbox('Select group', [None] + options)
            if opt is not None:
                if pandas_hdf:
                    df = pd.read_hdf(file, opt)
                else:
                    df = ms_file.read(dataset_name = opt)
                st.write(df)
                if st.checkbox('Create download link'):
                    if not isinstance(df, pd.DataFrame):
                        df = pd.DataFrame(df)

                    file_name = os.path.splitext(os.path.split(file)[-1])[0] + '.csv'
                    get_table_download_link(df, file_name)

def parse_folder(file_folder):
    """

    """
    raw_files = [_ for _ in os.listdir(file_folder) if _.lower().endswith('.raw') or _.lower().endswith('.d')]
    fasta_files = [_ for _ in os.listdir(file_folder) if _.lower().endswith('.fasta')]
    db_files = [_ for _ in os.listdir(file_folder) if _.lower().endswith('.db_data.hdf')]

    return raw_files, fasta_files, db_files


def widget_from_setting(recorder, key, group, element):
    """
    e.g. key = General

    """

    _ = group[element]

    if key not in recorder:
        recorder[key] = {}

    if 'description' in _:
        help = _['description']
    else:
        help = ''

    if _['type'] == 'doublespinbox':
        recorder[key][element] = st.slider(element, min_value = float(_['min']), max_value = float(_['max']), value = float(_['default']), help = help)
    elif _['type'] == 'spinbox':
        recorder[key][element] = st.slider(element, min_value = _['min'], max_value = _['max'], value = _['default'], help = help)
    elif _['type'] == 'checkbox':
        recorder[key][element] = st.checkbox(element, value = _['default'], help = help)
    elif _['type'] == 'checkgroup':
        opts = list(_['value'].keys())
        recorder[key][element] = st.multiselect(label = element, options = opts, default = _['default'], help = help)
    elif _['type'] == 'combobox':
        recorder[key][element] = st.selectbox(label = element, options = _['value'], index = _['value'].index(_['default']),  help = help)
    else:
        st.write(f"Not understood {_}")

    return recorder


def experiment():
    st.write(f"# New experiment")
    st.write(f'## Files')

    recorder = {}
    recorder['experiment'] = {}

    #files = file_selector()
    cwd = os.getcwd()
    file_folder = st.text_input("Enter path to folder that contains all experimental files. AlphaPept will parse for raw (.d / .raw), FASTA and AlphaPept database (.db_files.hdf) files and add them to the experiment.", cwd)

    if not os.path.isdir(file_folder):
        st.warning('Not a valid folder.')
    else:
        with st.spinner('Parsing folder'):
            raw_files, fasta_files, db_files = parse_folder(file_folder)


            recorder['experiment']['fasta_paths'] = [os.path.join(file_folder, _) for _ in fasta_files]
            recorder['experiment']['file_paths'] = [os.path.join(file_folder, _) for _ in raw_files]


            if (len(raw_files) == 0) or (len(fasta_files) == 0):
                if (len(raw_files) == 0) and (len(fasta_files) == 0):
                    st.warning('No raw and FASTA files in folder.')
                elif len(raw_files) == 0:
                    st.warning('No raw files in folder.')
                elif len(fasta_files) == 0:
                    st.warning('No fasta files in folder.')

            else:
                with st.beta_expander(f"Raw files ({len(raw_files)})"):
                    st.table(pd.DataFrame(raw_files, columns=['File']))

                if len(fasta_files) > 0:
                    with st.beta_expander(f"FASTA files ({len(fasta_files)})"):
                        st.table(pd.DataFrame(fasta_files, columns=['File']))

                #TODO: Include databse files
                #if len(fasta_files) > 0:
                #    with st.beta_expander(f"FASTA files ({len(fasta_files)})"):
                #        st.table(pd.DataFrame(fasta_files, columns=['File']))

                with st.beta_expander("Fractions"):
                    st.write('Fractions can be automatically assigned based on the filename.',
                            'Enter the string that preceds the fraction identifier and the string that comes after.')
                    prec = st.text_input('Preceding')
                    after = st.text_input('After')

                    if st.button('Apply'):
                        with st.spinner('Parsing folder'):
                            files = pd.DataFrame(raw_files, columns=['File'])
                            files['Fraction'] = files['File'].apply(lambda x: x.split(prec)[1].split(after)[0])
                            st.table(files)

                st.write(f"## Workflow")

                with st.beta_expander("Steps"):
                    group = SETTINGS_TEMPLATE['workflow']
                    for element in group:
                        recorder = widget_from_setting(recorder, 'workflow', group, element)

                st.write(f"## Additional settings")

                with st.beta_expander("Settings"):
                    for key in SETTINGS_TEMPLATE.keys():
                        if key not in ['experiment', 'workflow']:
                            group = SETTINGS_TEMPLATE[key]
                            if st.checkbox(key):
                                for element in group:
                                    recorder = widget_from_setting(recorder, key, group, element)

                name = st.text_input('Enter experiment name and press enter.')

                if name:
                    long_name = datetime.today().strftime('%Y_%m_%d_') + name + '.yaml'
                    long_name_path = os.path.join(QUEUE_PATH, long_name)

                    if os.path.exists(long_name_path):
                        st.error(f'Name {long_name} already exists. Please rename.')
                    else:
                        st.info(f'Filename will be: {long_name}. Click submit button to add to queue.')
                        if st.button('Submit'):
                            settings = load_settings(DEFAULT_SETTINGS_PATH)
                            for group in recorder:
                                for key in recorder[group]:
                                    settings[group][key] = recorder[group][key]

                            save_settings(settings, long_name_path)
                            #Change things from experiment
                            st.success(f'Experiment {long_name} submitted. Switch to Status tab to track progress.')
