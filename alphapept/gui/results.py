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
import plotly.graph_objects as go
from scipy import stats
import numpy as np

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

def ion_plot(ms_file, options):
    """
    Displays summary statistics from matched ions

    """

    if 'ions' in options:
        if st.button('Ion calibration'):
            with st.spinner('Creating plot.'):
                ions = ms_file.read(dataset_name='ions')
                delta_ppm = ((ions['db_mass'] - ions['ion_mass'])/((ions['db_mass'] + ions['ion_mass'])/2)*1e6).values
                counts, bins =np.histogram(delta_ppm, bins=100, density=True)
                bin_edges = bins[1:] + (bins[1] - bins[0])/2
                bins=np.arange(ions['db_mass'].min(), ions['db_mass'].max(), 1)
                offset = stats.binned_statistic(ions['ion_mass'].values, delta_ppm, 'mean', bins=bins)
                counts_ = stats.binned_statistic(ions['ion_mass'].values, delta_ppm, 'count', bins=bins)
                counts_ = counts_.statistic

                fig = make_subplots(rows=1, cols=2, column_widths=[0.8, 0.2], subplot_titles=("Mean ion offset (ppm) over m/z", "Histogram of Offset (ppm)"))
                fig.add_trace(go.Scatter(x = offset.bin_edges[1:], y = offset.statistic, marker_color='#17212b', mode = 'markers', marker={'opacity': np.sqrt(counts_/np.max(counts_))}), row=1, col=1)
                fig.add_bar(y= counts, x= bin_edges, row=1, col=2, marker_color='#17212b')
                fig.update_layout(showlegend=False)

                st.write(fig)

def protein_rank(ms_file, options):
    """
    Displays summary statistics from matched ions

    """
    if 'protein_fdr' in options:
        if st.button('Protein Rank'):
            with st.spinner('Creating plot.'):
                protein_fdr = ms_file.read(dataset_name='protein_fdr')
                p_df = protein_fdr.groupby('protein').sum()['int_sum'].sort_values()[::-1].apply(np.log).to_frame().reset_index().reset_index()
                p_df['protein_index'] =p_df['protein']

                p_df = p_df.set_index('protein_index')
                fig = px.scatter(p_df, x='index', y='int_sum', hover_data=["protein"], title='Protein Rank')
                fig.update_layout(showlegend=False)

                st.write(fig)

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

    st.write('Basic Plots')
    ion_plot(ms_file, options)
    protein_rank(ms_file, options)

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

    for _ in ['feature_table (n in table)', 'sequence (protein_fdr, n unique)', 'protein_group (protein_fdr, n unique)']:
        if _ not in data_df:
            data_df[_] = 0

    median_features = int(data_df['feature_table (n in table)'].median())
    median_peptides = int(data_df['sequence (protein_fdr, n unique)'].median())
    median_protein_groups = int(data_df['protein_group (protein_fdr, n unique)'].median())

    st.write(f"### Median: {median_features:,} features | {median_peptides:,} peptides | {median_protein_groups:,}  protein groups ")

    fig = make_subplots(rows=1, cols=3, subplot_titles=("Features", "Peptides", "Protein Groups", ))

    hovertext = list(data_df['filename'].values)

    fig.add_bar(x=data_df.index, y=data_df['feature_table (n in table)'], hovertext = hovertext, row=1, col=1, marker_color='#3dc5ef')
    fig.add_bar(x=data_df.index, y=data_df['sequence (protein_fdr, n unique)'], hovertext = hovertext, row=1, col=2, marker_color='#42dee1')
    fig.add_bar(x=data_df.index, y=data_df['protein_group (protein_fdr, n unique)'], hovertext = hovertext, row=1, col=3, marker_color='#6eecb9')

    fig.update_layout(showlegend=False)
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
        selection = st.selectbox('Last run', results_files)

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
