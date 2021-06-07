import streamlit as st
import os
import pandas as pd
import datetime
from alphapept.paths import SETTINGS_TEMPLATE_PATH, QUEUE_PATH, DEFAULT_SETTINGS_PATH, FASTA_PATH
from alphapept.settings import load_settings_as_template, save_settings, load_settings
from alphapept.gui.utils import escape_markdown, files_in_folder

# Dict to match workflow
WORKFLOW_DICT = {}
WORKFLOW_DICT['create_database'] = ['fasta']
WORKFLOW_DICT['import_raw_data'] = ['raw']
WORKFLOW_DICT['find_features'] = ['features']
WORKFLOW_DICT['search_data'] = ['search', 'score']
WORKFLOW_DICT['recalibrate_data'] = ['calibration']
WORKFLOW_DICT['align'] = []
WORKFLOW_DICT['match'] = ['matching']
WORKFLOW_DICT['lfq_quantification'] = ['quantification']


SETTINGS_TEMPLATE = load_settings(SETTINGS_TEMPLATE_PATH)

def parse_folder(file_folder):
    """
    Checks a folder for raw, fasta and db_data.hdf files
    """
    raw_files = [_ for _ in os.listdir(file_folder) if _.lower().endswith('.raw') or _.lower().endswith('.d')] # or _.lower().endswith('.ms_data.hdf')]
    fasta_files = [_ for _ in os.listdir(file_folder) if _.lower().endswith('.fasta')]
    db_files = [_ for _ in os.listdir(file_folder) if _.lower().endswith('.db_data.hdf')]
    #ms_files = [_ for _ in os.listdir(file_folder) if _.lower().endswith('.ms_data.hdf')]

    return raw_files, fasta_files, db_files


def widget_from_setting(recorder, key, group, element, override=None, indent=False):
    """
    Creates streamlit widgets from settigns
    Returns a recorder to extract set values
    """
    _ = group[element]

    if key not in recorder:
        recorder[key] = {}

    if 'description' in _:
        help = _['description']
    else:
        help = ''

    value = _['default']

    if override:
        value = override

    if indent:
        c1, c2 = st.beta_columns((1,8))
    else:
        c2 = st

    if _['type'] == 'doublespinbox':
        recorder[key][element] = c2.slider(element, min_value = float(_['min']), max_value = float(_['max']), value = float(value), help = help)
    elif _['type'] == 'spinbox':
        recorder[key][element] = c2.slider(element, min_value = _['min'], max_value = _['max'], value = value, help = help)
    elif _['type'] == 'checkbox':
        recorder[key][element] = c2.checkbox(element, value = value, help = help)
    elif _['type'] == 'checkgroup':
        opts = list(_['value'].keys())
        recorder[key][element] = c2.multiselect(label = element, options = opts, default = value, help = help)
    elif _['type'] == 'combobox':
        recorder[key][element] = c2.selectbox(label = element, options = _['value'], index = _['value'].index(value),  help = help)
    else:
        st.write(f"Not understood {_}")

    return recorder

def submit_experiment(recorder):
    """
    Asks for an experiment name and creates a button to submit.
    """
    name = st.text_input('Enter experiment name and press enter.', datetime.datetime.today().strftime('%Y_%m_%d_'))

    long_name = name + '.yaml'
    long_name_path = os.path.join(QUEUE_PATH, long_name)

    if os.path.exists(long_name_path):
        st.error(f'Name {escape_markdown(long_name)} already exists. Please rename.')
    else:
        st.info(f'Filename will be: {escape_markdown(long_name)}. Click submit button to add to queue.')
        if st.button('Submit'):
            settings = load_settings_as_template(DEFAULT_SETTINGS_PATH)
            for group in recorder:
                for key in recorder[group]:
                    settings[group][key] = recorder[group][key]

            save_settings(settings, long_name_path)
            #Change things from experiment
            st.success(f'Experiment {escape_markdown(long_name)} submitted. Switch to Status tab to track progress.')


def customize_settings(recorder, uploaded_settings, loaded):

    with st.beta_expander("Settings", loaded):

        checked = [_ for _ in recorder['workflow'] if not recorder['workflow'][_]]
        checked_ = []
        [checked_.extend(WORKFLOW_DICT[_]) for _ in checked if _ in WORKFLOW_DICT]

        exclude = ['experiment', 'workflow'] + checked_

        for key in SETTINGS_TEMPLATE.keys():
            if key not in exclude:

                group = SETTINGS_TEMPLATE[key]
                #Check if different than default
                if loaded:
                    changed = sum([uploaded_settings[key][element] != group[element]['default'] for element in group]) > 0
                else:
                    changed = False

                if st.checkbox(key, changed):
                    for element in group:
                        override = None
                        if changed:
                            if uploaded_settings[key][element] != group[element]['default']:
                                override = uploaded_settings[key][element]

                        recorder = widget_from_setting(recorder, key, group, element, override, indent=True)

    return recorder

def experiment():
    st.write("# New experiment")
    st.write('## Files')

    recorder = {}
    recorder['experiment'] = {}

    cwd = os.getcwd()
    file_folder = st.text_input("Enter path to folder that contains all experimental files. AlphaPept will parse for raw (.d / .raw), FASTA and AlphaPept database (.db_files.hdf) files and add them to the experiment.", cwd)

    if not os.path.isdir(file_folder):
        st.warning('Not a valid folder.')
    else:
        with st.spinner('Parsing folder'):

            raw_files, fasta_files, db_files = parse_folder(file_folder)

            if st.button('Reload folder'):
                raw_files, fasta_files, db_files = parse_folder(file_folder)

            fasta_files = [os.path.join(file_folder, _) for _ in fasta_files]

            recorder['experiment']['file_paths'] = [os.path.join(file_folder, _) for _ in raw_files]

            if len(raw_files) == 0:
                st.warning('No raw files in folder.')

            else:
                with st.beta_expander(f"Raw files ({len(raw_files)})"):
                    st.table(pd.DataFrame(raw_files, columns=['File']))

                fasta_files_home_dir = files_in_folder(FASTA_PATH, '.fasta')
                fasta_files_home_dir = [os.path.join(FASTA_PATH, _) for _ in fasta_files_home_dir]

                fasta_files_home_dir += fasta_files

                selection = st.multiselect(f'Select FASTA files', options=fasta_files_home_dir, default = fasta_files)
                recorder['experiment']['fasta_paths'] = selection

                #TODO: Include databse files
                #if len(fasta_files) > 0:
                #    with st.beta_expander(f"FASTA files ({len(fasta_files)})"):
                #        st.table(pd.DataFrame(fasta_files, columns=['File']))

                with st.beta_expander("Fractions"):
                    st.write('Fractions are currently not supported.')
                    if False:
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

                st.write("## Modify settings")

                prev_settings = st.checkbox('Use previous settings as template')

                loaded = False
                uploaded_settings = None
                if prev_settings:
                    uploaded_file = st.file_uploader("Choose a file")
                    if uploaded_file is not None:
                        uploaded_settings =  yaml.load(uploaded_file, Loader=yaml.FullLoader)
                        loaded=True


                recorder = customize_settings(recorder, uploaded_settings, loaded)

                st.write("## Submit experiment")
                submit_experiment(recorder)
