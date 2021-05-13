import streamlit as st
from alphapept.gui.utils import files_in_folder, read_log
from alphapept.paths import PROCESSED_PATH
from alphapept.settings import load_settings
import os
import yaml
import alphapept.io
import pandas as pd
import base64
import plotly.express as px
from plotly.subplots import make_subplots

def readable_files_from_yaml(results_yaml):
    """
    Returns all readable files from results yaml
    """

    raw_files = [os.path.splitext(_)[0]+'.ms_data.hdf' for _ in results_yaml['experiment']['file_paths']]
    raw_files = raw_files + [results_yaml['experiment']['results_path']]
    raw_files = [_ for _ in raw_files if os.path.exists(_)]

    return raw_files

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


def make_df_downloadble(df, file):
    """
    Creates checkbox to make displayed data downloadable
    """
    if st.button('Create download link'):
        file_name = os.path.splitext(os.path.split(file)[-1])[0] + '.csv'
        get_table_download_link(df, file_name)


def parse_file_and_display(file):
    """
    Loads file and displays dataframe in streamlit
    """

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
        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)

        data_range = st.slider('Data range', 0, len(df), (0,1000))
        st.write(df.iloc[data_range[0]:data_range[1]])

        make_df_downloadble(df, file)

def plot_summary(results_yaml):
    """
    Plot summary
    """

    files = [os.path.splitext(_)[0] for _ in results_yaml['summary']['processed_files']]
    data = [results_yaml['summary'][_] for _ in files]

    data_df = pd.DataFrame(data)
    data_df['filename'] = files

    median_features = int(data_df['feature_table'].median())
    median_protein_groups= int(data_df['protein_fdr_n_protein_group'].median())
    median_peptides = int(data_df['protein_fdr_n_sequence'].median())

    st.write(f"### Median: {median_features:,} features | {median_peptides:,} peptides | {median_protein_groups:,}  protein groups ")

    col1, col2, col3 = st.beta_columns(3)

    fig = make_subplots(rows=1, cols=3, subplot_titles=("Features", "Peptides", "Protein Groups", ))

    hovertext = [data_df['filename'].values]

    fig.add_bar(x=data_df.index, y=data_df['feature_table'], hovertext = hovertext, row=1, col=1, marker_color='#3dc5ef')
    fig.add_bar(x=data_df.index, y=data_df['protein_fdr_n_protein_group'], hovertext = hovertext, row=1, col=2, marker_color='#42dee1')
    fig.add_bar(x=data_df.index, y=data_df['protein_fdr_n_sequence'], hovertext = hovertext, row=1, col=3, marker_color='#6eecb9')

    fig.update_layout(showlegend=False)
    #fig.update_xaxes(tickmode = 'array', ticktext=list((range(len(data_df)))))

    fig.update_layout(title_text="Run Summary")

    st.write(fig)

#42dee1

def results():
    st.write("# Results")

    st.text("This page allows to explore the analysis results.\nAlphaPept uses the HDF container format which can be accessed here.")

    #TOdo: include previously processed output files..

    file = ''

    selection = st.selectbox('File selection', ('Previous results', 'Enter file'))

    if selection == 'Previous results':

        results_files = files_in_folder(PROCESSED_PATH, '.yaml', sort='date')

        with st.beta_expander(f"Total {len(results_files)} Files"):
            st.table(results_files)

        st.write('### Select results file')

        selection = st.selectbox('Run', results_files)

        if selection:

            filepath_selection = os.path.join(PROCESSED_PATH, selection)
            results_yaml = load_settings(filepath_selection)

            plot_summary(results_yaml)

            with st.beta_expander("Run summary"):
                st.write(results_yaml['summary'])

            read_log(os.path.splitext(filepath_selection)[0]+'.log')
            raw_files = readable_files_from_yaml(results_yaml)
            st.write('### Explore tables from experiment')
            file = st.selectbox('Select file from experiment', raw_files)

    elif selection == 'Enter file':
        file = st.text_input("Enter path to hdf file.", os.getcwd())
    else:
        pass

    if file is None:
        file = ''

    if not os.path.isfile(file):
        st.warning('Not a valid file.')
    else:
        with st.spinner('Parsing file'):
            parse_file_and_display(file)
