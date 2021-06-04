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
from sklearn.decomposition import PCA


@st.cache
def cached_file(file):
    df = pd.read_hdf(file, 'protein_table')
    return df

def readable_files_from_yaml(results_yaml):
    """
    Returns all readable files from results yaml
    """

    raw_files = [os.path.splitext(_)[0]+'.ms_data.hdf' for _ in results_yaml['experiment']['file_paths']]
    raw_files = [results_yaml['experiment']['results_path']] + raw_files
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



def correlation_heatmap(file, options):
    if '/protein_table' in options:
        with st.beta_expander('Correlation heatmap'):
            df = cached_file(file)

            cols = [_ for _ in df.columns if 'LFQ' in _]
            if len(cols) == 0:
                cols = df.columns

            df = np.log(df[cols])
            corr = df.corr()

            fig = make_subplots(rows=1, cols=1)
            fig.add_trace(trace = go.Heatmap(z=corr.values,
                              x=corr.index.values,
                              y=corr.columns.values, colorscale='Greys'))
            fig.update_layout(height=600, width=600)
            st.write(fig)

def pca_plot(file, options):
    if '/protein_table' in options:
        with st.beta_expander('PCA'):
            df = cached_file(file)

            cols = [_ for _ in df.columns if 'LFQ' in _]
            if len(cols) == 0:
                cols = df.columns

            pca = PCA(n_components=2)
            components = pca.fit_transform(df[cols].fillna(0).T)

            plot_df = pd.DataFrame(components, columns = ['Component 1', 'Component 2'])
            plot_df['Filename'] = cols
            fig = px.scatter(plot_df, x='Component 1', y='Component 2', hover_data=['Filename'], title='PCA')
            fig.update_layout(height=600, width=600)
            fig.update_traces(marker=dict(color='#18212b'))
            st.write(fig)



def volcano_plot(file, options):
    if '/protein_table' in options:
        with st.beta_expander('Volcano plot'):
            df = cached_file(file)

            df_log = np.log(df.copy())
            col1, col2 = st.beta_columns(2)

            group_1 = col1.multiselect('Group1', df.columns)
            group_2 = col2.multiselect('Group2', df.columns)

            show_proteins = st.multiselect('Highlight proteins', df.index)

            if (len(group_1) > 0) and (len(group_2) > 0):


                with st.spinner('Creating plot..'):
                    test = stats.ttest_ind(df_log[group_1].values, df_log[group_2].values, nan_policy='omit', axis=1)

                    t_diff = np.nanmean(df_log[group_1].values, axis = 1) - np.nanmean(df_log[group_2].values, axis = 1)
                    plot_df = pd.DataFrame()

                    plot_df['t_test_diff'] = t_diff
                    plot_df['-log(pvalue)'] = -np.log(test.pvalue.data)
                    plot_df['id'] = df.index
                    plot_df.index = df.index

                    fig = make_subplots()

                    fig.add_trace(
                        go.Scatter(
                                    x= plot_df['t_test_diff'],
                                    y=plot_df['-log(pvalue)'],
                                    hovertemplate ='<b>%{text}</b>' +
                                    '<br>t_test diff: %{y:.3f}'+
                                    '<br>-log(pvalue): %{x:.3f}',
                                    text = plot_df.index,
                                    opacity=0.8,
                                    mode='markers',
                                    marker = dict(color='#3dc5ef')))

                    if len(show_proteins)> 0:
                        fig.add_trace(go.Scatter(
                            x=plot_df.loc[show_proteins]['t_test_diff'],
                            y=plot_df.loc[show_proteins]['-log(pvalue)'],
                            hovertemplate ='<b>%{text}</b>' +
                            '<br>t_test diff: %{y:.3f}'+
                            '<br>-log(pvalue): %{x:.3f}',
                            text = show_proteins,
                            mode="markers+text",
                            textposition="top center",
                            marker_color='#18212b',
                            textfont=dict(
                                family="Courier New, monospace",
                                size=16,
                                color="#18212b"
                                )
                            )
                            )
                    fig.update_layout(height=600, width=600)
                    fig.update_layout(showlegend=False)
                    st.write(fig)

def scatter_plot(file, options):
    if '/protein_table' in options:
        with st.beta_expander('Scatter plot'):
            df = cached_file(file)

            df_log = np.log(df.copy())
            col1, col2 = st.beta_columns(2)

            all_cols = df.columns

            group_1 = col1.selectbox('Group1', df.columns)
            group_2 = col2.selectbox('Group2', df.columns)

            with st.spinner('Creating plot..'):
                df_log['id'] = df_log.index
                fig = px.scatter(df_log, x=group_1, y=group_2, hover_data=['id'], title='Scatterplot', opacity=0.2, trendline="ols")
                fig.update_layout(height=600, width=600)
                fig.update_traces(marker=dict(color='#18212b'))

                results = px.get_trendline_results(fig)

                st.write(fig)
                st.code(results.px_fit_results.iloc[0].summary())

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
        ms_file = None

        with pd.HDFStore(file) as hdf:
            options = list(hdf.keys())

    if pandas_hdf:
        volcano_plot(file, options)
        correlation_heatmap(file, options)
        scatter_plot(file, options)
        pca_plot(file, options)

    if ms_file is not None:
        st.write('Basic Plots')
        ion_plot(ms_file, options)

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

def plot_summary(results_yaml, selection):
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

    st.write(f"### {selection}")
    st.write(f"### {median_features:,} features | {median_peptides:,} peptides | {median_protein_groups:,}  protein groups (median)")

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

    selection = st.selectbox('File selection', ('Previous results', 'Enter file'))

    if selection == 'Previous results':

        results_files = files_in_folder(PROCESSED_PATH, '.yaml', sort='date')
        selection = st.selectbox('Last run', results_files)

        if selection:

            filepath_selection = os.path.join(PROCESSED_PATH, selection)
            results_yaml = load_settings(filepath_selection)

            with st.spinner('Loading data..'):
                plot_summary(results_yaml, selection)

            with st.beta_expander("Run summary"):
                st.write(results_yaml['summary'])

            read_log(os.path.splitext(filepath_selection)[0]+'.log')
            raw_files = readable_files_from_yaml(results_yaml)
            st.write('### Explore tables from experiment')
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
            parse_file_and_display(file)
