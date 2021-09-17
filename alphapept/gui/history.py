import os
import yaml
import streamlit as st
import numpy as np
import plotly.express as px
import pandas as pd
import datetime

from alphapept.paths import PROCESSED_PATH, PLOT_SETTINGS
from alphapept.gui.utils import files_in_folder, compare_date
from alphapept.settings import load_settings
from typing import Callable, Union


def load_plot_settings() -> dict:
    """Helper function to load customized plot settings.

    Returns:
        dict: A dictionary containing plot_settings loaded from a defined location.
    """
    plot_settings = load_settings(PLOT_SETTINGS)
    return plot_settings

@st.cache
def load_file(file:str) -> dict:
    """Cached streamlit function to read summary stats from a file.

    Args:
        file (str): List of file paths.

    Returns:
        dict: A dictionary containing the summary of a results.yaml file.
    """
    with open(os.path.join(PROCESSED_PATH, file), "r") as settings_file:
        results = yaml.load(settings_file, Loader=yaml.FullLoader)
    return results

def load_files(file_list: list, callback: Union[Callable, None] = None) -> dict:
    """Read multiple results.yaml files and combine them into a dict.

    Args:
        file_list (list): List of file paths.
        callback (Union[Callable, None], optional): Callback function to report progress. Defaults to None.

    Returns:
        dict: A dictionary containing the summary of all results.yaml files.
    """
    all_results = {}

    for idx, _ in enumerate(file_list):
        base, ext = os.path.splitext(_)
        all_results[base] = load_file(_)

        if callback:
            callback.progress((idx + 1) / len(file_list))

    return all_results


def filter_by_tag(files: list) -> list:
    """Streamlit widget to filter a list based on a user input.

    Args:
        files (list): List of files to be filtered.

    Returns:
        list: Reduced file list with files containing the tag.
    """
    filter = st.text_input("Filter by name")

    if filter:
        filtered = [_ for _ in files if filter in _]
    else:
        filtered = files

    st.write(f"Remaining {len(filtered)} of {len(files)} files.")

    return filtered


def check_group(filename: str, groups: list) -> Union[str, None]:
    """Helper function to check if a group exists for a given filename.

    Args:
        filename (str): Name of file to be checked.
        groups (list): List of groups.

    Returns:
        Union[str, None]: Returns None if group is not present, else the group name.
    """
    for group in groups:
        if group in filename:
            return group
    return "None"


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
            except KeyError:
                vals[idx] = np.nan
        else:
            try:
                vals[idx] = all_results[_]["summary"][files[idx]][plot]
            except KeyError:
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


def history():
    """Streamlit page to plot a historical overview of previous results."""
    st.write("# History")
    st.text(
        f"History allows to visualize summary information from multiple previous analysis."
        f"\nIt checks {PROCESSED_PATH} for *.yaml files."
        "\nFiles can be filtered to only include a subset."
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

    filtered = filter_by_tag(processed_files)
    all_results = load_files(filtered, callback=st.progress(0))

    if len(all_results) > 0:
        create_multiple_plots(all_results, groups, to_plot)
