import streamlit as st
import os
import pandas as pd
import datetime
from alphapept.paths import SETTINGS_TEMPLATE, QUEUE_PATH, DEFAULT_SETTINGS_PATH
from alphapept.settings import load_settings_as_template, save_settings


def parse_folder(file_folder):
    """
    Checks a folder for raw, fasta and db_data.hdf files
    """
    raw_files = [_ for _ in os.listdir(file_folder) if _.lower().endswith('.raw') or _.lower().endswith('.d')]
    fasta_files = [_ for _ in os.listdir(file_folder) if _.lower().endswith('.fasta')]
    db_files = [_ for _ in os.listdir(file_folder) if _.lower().endswith('.db_data.hdf')]

    return raw_files, fasta_files, db_files


def widget_from_setting(recorder, key, group, element, override=None):
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

    if _['type'] == 'doublespinbox':
        recorder[key][element] = st.slider(element, min_value = float(_['min']), max_value = float(_['max']), value = float(value), help = help)
    elif _['type'] == 'spinbox':
        recorder[key][element] = st.slider(element, min_value = _['min'], max_value = _['max'], value = value, help = help)
    elif _['type'] == 'checkbox':
        recorder[key][element] = st.checkbox(element, value = value, help = help)
    elif _['type'] == 'checkgroup':
        opts = list(_['value'].keys())
        recorder[key][element] = st.multiselect(label = element, options = opts, default = value, help = help)
    elif _['type'] == 'combobox':
        recorder[key][element] = st.selectbox(label = element, options = _['value'], index = _['value'].index(value),  help = help)
    else:
        st.write(f"Not understood {_}")

    return recorder

def submit_experiment(recorder):
    """
    Asks for an experiment name and creates a button to submit.
    """
    name = st.text_input('Enter experiment name and press enter.')

    if name:
        long_name = datetime.datetime.today().strftime('%Y_%m_%d_') + name + '.yaml'
        long_name_path = os.path.join(QUEUE_PATH, long_name)

        if os.path.exists(long_name_path):
            st.error(f'Name {long_name} already exists. Please rename.')
        else:
            st.info(f'Filename will be: {long_name}. Click submit button to add to queue.')
            if st.button('Submit'):
                settings = load_settings_as_template(DEFAULT_SETTINGS_PATH)
                for group in recorder:
                    for key in recorder[group]:
                        settings[group][key] = recorder[group][key]

                save_settings(settings, long_name_path)
                #Change things from experiment
                st.success(f'Experiment {long_name} submitted. Switch to Status tab to track progress.')


def customize_settings(recorder, uploaded_settings, loaded):

    with st.beta_expander("Settings", loaded):
        for key in SETTINGS_TEMPLATE.keys():
            if key not in ['experiment', 'workflow']:
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

                        recorder = widget_from_setting(recorder, key, group, element, override)

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

                st.write("## Additional settings")

                prev_settings = st.checkbox('Use previous settings as template')

                loaded = False
                if prev_settings:
                    uploaded_file = st.file_uploader("Choose a file")
                    if uploaded_file is not None:
                        uploaded_settings =  yaml.load(uploaded_file, Loader=yaml.FullLoader)
                        loaded=True


                recorder = customize_settings(recorder, uploaded_settings, loaded)

                submit_experiment(recorder)
