import os
import streamlit as st
import numpy as np
import plotly.express as px
import pandas as pd
import datetime

from alphapept.paths import PLOT_SETTINGS, PROCESSED_PATH
from alphapept.gui.utils import files_in_folder, compare_date, load_files, check_group, filter_by_tag
from alphapept.settings import load_settings
from typing import Callable


def load_plot_settings() -> dict:
    """Helper function to load customized plot settings.

    Returns:
        dict: A dictionary containing plot_settings loaded from a defined location.
    """
    plot_settings = load_settings(PLOT_SETTINGS)
    return plot_settings

def create_single_plot(
    all_results: dict,
    files: list,
    acquisition_date_times: list,
    mode: str,
    groups: list,
    plot: str,
    minimum_date: datetime,
):
    """Helper function to create a plotly express plot based on the all_results dict and the specified fields.

    Args:
        all_results (dict): A dictionary containing the summary of all results.yaml files.
        files (list): List of files.
        acquisition_date_times (list): List of acquisition date times.
        mode (str): Plotting mode. Values will be sorted according to this field.
        groups (list): List of groups.
        plot (str): Name of the column that should be plotted.
        minimum_date (datetime): Minimum acquistion date for files to be displayed.
    """
    vals = np.empty(len(all_results))
    for idx, _ in enumerate(all_results.keys()):
        if plot == "timing (min)":
            try:
                vals[idx] = all_results[_]["summary"]["timing"]["total (min)"]
            except (KeyError, ValueError):
                vals[idx] = np.nan
        else:
            try:
                vals[idx] = all_results[_]["summary"][files[idx]][plot]
            except (KeyError, ValueError):
                vals[idx] = np.nan

    plot_df = pd.DataFrame([files, acquisition_date_times, vals]).T
    plot_df = plot_df[~plot_df[0].isna()]
    plot_df = plot_df[plot_df[1].apply(lambda x : compare_date(x, minimum_date))]

    plot_df.columns = ["Filename", "AcquisitionDateTime", plot]

    if groups != []:
        plot_df["group"] = plot_df["Filename"].apply(lambda x: check_group(x, groups))
    else:
        plot_df["group"] = "None"

    median_ = plot_df[plot].median()
    plot_df = plot_df.sort_values(mode)

    if mode == "Filename":
        height = 800
    else:
        height = 400

    fig = px.scatter(
        plot_df,
        x=mode,
        y=plot,
        color="group",
        hover_name="Filename",
        hover_data=["AcquisitionDateTime"],
        title=f"{plot} - median {median_:.2f}",
        height=height,
    ).update_traces(mode="lines+markers")
    fig.add_hline(y=median_, line_dash="dash")
    st.plotly_chart(fig)


def create_multiple_plots(all_results: dict, groups: list, to_plot: list):
    """Creates multiple plotly express plots.

    Args:
        all_results (dict): A dictionary containing the summary of all results.yaml files.
        groups (list): List of groups.
        to_plot (list): Name of the column that should be plotted.
    """

    files = np.empty(len(all_results), dtype='object')
    acquisition_date_times = np.empty(len(all_results), dtype='object')

    fields = set()

    for idx, result in enumerate(all_results.values()):
        if "summary" in result:
            summary = result["summary"]
            files[idx] = os.path.splitext(summary["processed_files"][0])[0]
            acquisition_date_times[idx] = summary[files[idx]]["acquisition_date_time"]
            fields.update(summary[files[idx]].keys())

    fields.remove("acquisition_date_time")
    fields = list(fields)
    fields.sort()

    if to_plot == []:
        plot_types = fields + ["timing (min)"]
    else:
        plot_types = [_ for _ in to_plot if _ in fields]

    c1, c2  = st.columns(2)

    mode = c1.selectbox("X-Axis", options=["AcquisitionDateTime", "Filename"])
    minimum_date = c2.date_input('Minimum acquisition date', datetime.datetime.today() - datetime.timedelta(days=28))

    minimum_date = datetime.datetime.combine(minimum_date, datetime.datetime.min.time())

    with st.spinner("Creating plots.."):
        for plot in plot_types:
            create_single_plot(
                all_results, files, acquisition_date_times, mode, groups, plot, minimum_date,
            )

@st.cache
def filter_for_single_file(results):

    results_list = []
    for _ in results.keys():

        if len(results[_]['experiment']['shortnames']) == 1:
            try:
                x = results[_]['summary'][results[_]['experiment']['shortnames'][0]]
                x['timing (min)'] = results[_]['summary']['timing']['total (min)']
                x['filename'] = results[_]['experiment']['shortnames'][0]

                results_list.append(x)
            except Exception as e:
                pass

    result_df = pd.DataFrame(results_list)

    return result_df

@st.cache
def convert_df(df):
    return df.to_csv().encode('utf-8')

def history():
    """Streamlit page to plot a historical overview of previous results."""
    st.write("# History")
    st.text(
        f"History allows to display summary information from multiple previous analysis."
        f"\nIt checks {PROCESSED_PATH} for *.yaml files."
        "\nFiles can be filtered to only include a subset."
        "\nOnly experiments with a single file will be displayed."
        "\nIf retention time (rt) is displayed, the unit is minutes."
    )

    processed_files = files_in_folder(PROCESSED_PATH, ".yaml")

    with st.expander(f"Processed files ({len(processed_files)})"):
        st.table(processed_files)

    plot_settings = load_plot_settings()
    if "history" in plot_settings:
        history_settings = plot_settings["history"]
    else:
        history_settings = {}

    if "groups" in history_settings:
        groups = history_settings["groups"]
    else:
        groups = []
    if "plots" in history_settings:
        to_plot = history_settings["plots"]
    else:
        to_plot = []

    with st.expander("Customize plots"):
        st.text(
            f"Plots can be modified by changing {PLOT_SETTINGS}, set groups to group plots according to filename, set plots to define the plots."
        )
        st.write(history_settings)


    all_results = load_files(processed_files, callback=st.progress(0))

    filtered = filter_by_tag(all_results)

    if len(filtered) > 0:
        mode = st.selectbox('Select Mode', ['Graph', 'Table'])
        if mode == 'Table':
            st.table(filtered.style.bar(color='lightgreen').format(precision=3))
            csv = convert_df(filtered)
            st.download_button(
            f"Click to download as (csv)",
            csv,
            "file.csv",
            "text/csv",
            key='download-csv'
            )
        else:
            plot_df = filtered.copy()
            c1, c2 = st.columns(2)
            x = c1.selectbox('X axis', filtered.columns)
            y = c2.selectbox('Y axis', [_ for _ in filtered.columns if _ is not x])

            if groups != []:
                plot_df["group"] = plot_df["file_in_experiment"].apply(lambda x: check_group(x, groups))
            else:
                plot_df["group"] = "None"

            try:
                median_ = plot_df[y].median()
                plot_df = plot_df.sort_values(x)

                if mode == "Filename":
                    height = 800
                else:
                    height = 400

                fig = px.scatter(
                    plot_df,
                    x=x,
                    y=y,
                    color="group",
                    hover_name="file_in_experiment",
                    hover_data=["acquisition_date_time"],
                    title=f"{x} - median {median_:.2f}",
                    height=height,
                ).update_traces(mode="lines+markers")
                fig.add_hline(y=median_, line_dash="dash")
                st.plotly_chart(fig)
            except Exception as e:
                st.warning(e)
