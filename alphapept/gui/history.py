import os
import streamlit as st
import plotly.express as px
import yaml 
import pandas as pd 
from alphapept.paths import PROCESSED_PATH, AP_PATH
from alphapept.gui.utils import files_in_folder

def load_files(file_list, callback = None):
    """
    Read multiple yaml files and return a dict with results
    """
    all_results = {}

    for idx, _ in enumerate(file_list):
        with open(os.path.join(PROCESSED_PATH, _), "r") as settings_file:
            results = yaml.load(settings_file, Loader=yaml.FullLoader)
            base, ext = os.path.splitext(_)
            all_results[base] = results

        if callback:
            callback.progress((idx+1)/len(file_list))

    return all_results

def read_groups():
    """
    Checks the AlphaPept Home Folder if a group.txt is present
    """
    group_txt = os.path.join(AP_PATH, 'groups.txt')
    if os.path.isfile(group_txt):
        with open(group_txt, 'r') as f:
            groups = f.readlines()
            groups = [_.rstrip('\n') for _ in groups]
    else:
        groups = []

    return groups

def filter_by_tag(files):
    """
    Streamlit text input to filter filenames by tag
    """
    filter = st.text_input('Filter')

    if filter:
        filtered = [_ for _ in files if filter in _]
    else:
        filtered = files

    st.write(filter)
    st.write(f"Remaining {len(filtered)} of {len(files)} files.")

    return filtered

def check_group(filename, groups):
    for group in groups:
        if group in filename:
            return group
    return 'None'


def create_single_plot(all_results, files, acquisition_date_times, mode, groups, plot):
    """
    Creates single plotly express plot 
    """
    vals = []
    for idx, _ in enumerate(all_results.keys()):
        if plot == 'timing':
            vals.append(all_results[_]["summary"]["timing"]["total"])
        else:
            try:
                vals.append(all_results[_]["summary"][files[idx]][plot])
            except KeyError:
                vals.append(0)

    plot_df = pd.DataFrame([files, acquisition_date_times, vals]).T
    plot_df.columns = ['Filename', 'AcquisitionDateTime', plot]

    if groups != []:
        plot_df['group'] = plot_df['Filename'].apply(lambda x: check_group(x, groups))
    else:
        plot_df['group'] = 'None'

    median_ = plot_df[plot].median()
    plot_df = plot_df.sort_values(mode)

    if mode == 'Filename':
        height = 800
    else:
        height = 400

    fig = px.scatter(plot_df, x=mode, y=plot, color = 'group', hover_name='Filename', hover_data=['AcquisitionDateTime'], title=f'{plot} - median {median_:.2f}', height=height).update_traces(mode='lines+markers')
    fig.add_hline(y=median_, line_dash="dash")
    st.plotly_chart(fig)

def create_multiple_plots(all_results, groups):
    """
    Creates multiple plotly express plots 

    """
    plot_types = ['feature_table', 'feature_table_median_rt_length','protein_fdr_n_sequence','protein_fdr_n_protein', 'protein_fdr_n_protein_group', 'id_rate','timing']
    mode = st.selectbox('X-Axis', options = ['AcquisitionDateTime','Filename'])

    with st.spinner('Creating plots..'):

        # Get filename and acquisition_date_time
        files = [os.path.splitext(all_results[_]['summary']['processed_files'][0])[0] for _ in all_results.keys()]
        acquisition_date_times = [all_results[_]["summary"][files[idx]]['acquisition_date_time'] for idx, _ in enumerate(all_results.keys())]

        for plot in plot_types:
            create_single_plot(all_results, files, acquisition_date_times, mode, groups, plot)


def history():
    """
    Plot history of previous experiments
    """
    st.write("# History")
    st.text(f'History allows to visualize summary information from multiple previous analysis.'
    f'\nIt checks {PROCESSED_PATH} for *.yaml files.'
    '\nFiles can be filtered to only include a subset.')

    processed_files = files_in_folder(PROCESSED_PATH, '.yaml')

    with st.beta_expander(f"Processed files ({len(processed_files)})"):
        st.table(processed_files)

    groups = read_groups()

    with st.beta_expander(f"Group files"):
        st.text(f"If a groups.txt is present in the AlphaPept folder {AP_PATH}, data will be grouped.")
        groups = st.multiselect('Groups', default = groups, options=groups)

    filtered = filter_by_tag(processed_files)
    filtered = filtered[:st.slider('Preview', 1, len(filtered), min(len(filtered), 50))]
    all_results = load_files(filtered, callback=st.progress(0))

    if len(all_results) > 0:
        create_multiple_plots(all_results, groups)