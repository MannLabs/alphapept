import streamlit as st
import os
import pandas as pd
import datetime
import yaml
from typing import Union, Tuple

from alphapept.paths import (
    SETTINGS_TEMPLATE_PATH,
    QUEUE_PATH,
    PROCESSED_PATH,
    DEFAULT_SETTINGS_PATH,
    FASTA_PATH,
)
from alphapept.settings import load_settings_as_template, save_settings, load_settings
from alphapept.gui.utils import escape_markdown, files_in_folder
from alphapept.utils import get_size
from st_aggrid import GridOptionsBuilder, AgGrid

# Dict to match workflow
WORKFLOW_DICT = {}
WORKFLOW_DICT["create_database"] = ["fasta"]
WORKFLOW_DICT["import_raw_data"] = ["raw"]
WORKFLOW_DICT["find_features"] = ["features"]
WORKFLOW_DICT["search_data"] = ["search", "score"]
WORKFLOW_DICT["recalibrate_data"] = ["calibration"]
WORKFLOW_DICT["align"] = []
WORKFLOW_DICT["match"] = ["matching"]
WORKFLOW_DICT["lfq_quantification"] = ["quantification"]
SETTINGS_TEMPLATE = load_settings(SETTINGS_TEMPLATE_PATH)


def parse_folder(file_folder: str) -> Tuple[list, list, list]:
    """Checks a folder for raw, fasta and db_data.hdf files.

    Args:
        file_folder (str): Path to folder.

    Returns:
        list: List of raw files in folder.
        list: List of FASTA files in folder.
        list: List of db_files in folder.
    """

    raw_files = [
        _
        for _ in os.listdir(file_folder)
        if _.lower().endswith(".raw") or _.lower().endswith(".d") or _.lower().endswith(".mzml")
    ]
    fasta_files = [_ for _ in os.listdir(file_folder) if _.lower().endswith(".fasta")]
    db_files = [
        _ for _ in os.listdir(file_folder) if _.lower().endswith(".db_data.hdf")
    ]

    return raw_files, fasta_files, db_files


def widget_from_setting(
    recorder: dict,
    key: str,
    group: str,
    element: str,
    override: Union[float, None] = None,
    indent: bool = False,
) -> dict:
    """Creates streamlit widgets from settings.
    Returns a recorder to extract set values.

    Args:
        recorder (dict): A dictionary that stores all widgets.
        key (str): Key to the widget that should be created.
        group (str): Groupname of the widget that should be created.
        element (str): Element of thw widget that should be created.
        override (Union[float, None], optional): Override value for the default value. Defaults to None.
        indent (bool, optional): Flag to indent the widget via the st.columns widget. Defaults to False.

    Returns:
        dict: A dictionary that stores all widgets.
    """

    _ = group[element]

    if key not in recorder:
        recorder[key] = {}

    if "description" in _:
        tooltip = _["description"]
    else:
        tooltip = ""

    value = _["default"]

    if override:
        value = override

    if indent:
        c1, c2 = st.columns((1, 8))
    else:
        c2 = st

    if _["type"] == "doublespinbox":
        recorder[key][element] = c2.number_input(
            element,
            min_value=float(_["min"]),
            max_value=float(_["max"]),
            value=float(value),
            help=tooltip,
        )
    elif _["type"] == "spinbox":
        recorder[key][element] = c2.number_input(
            element, min_value=_["min"], max_value=_["max"], value=value, help=tooltip
        )
    elif _["type"] == "checkbox":
        recorder[key][element] = c2.checkbox(element, value=value, help=tooltip)
    elif _["type"] == "checkgroup":
        opts = list(_["value"].keys())
        recorder[key][element] = c2.multiselect(
            label=element, options=opts, default=value, help=tooltip
        )
    elif _["type"] == "combobox":
        recorder[key][element] = c2.selectbox(
            label=element, options=_["value"], index=_["value"].index(value), help=tooltip
        )
    elif _["type"] == "string":
        recorder[key][element] = c2.text_input(label=element, default=value, help=tooltip)
    else:
        st.write(f"Not understood {_}")

    return recorder


def submit_experiment(recorder: dict):
    """Widget that asks for an experiment name, extracts all current values and saves the experiment.

    Args:
        recorder (dict): A dictionary that stores all widgets.
    """
    name = st.text_input(
        "Enter experiment name and press enter.",
        datetime.datetime.today().strftime("%Y_%m_%d_"),
    )

    long_name = name + ".yaml"
    long_name_path_queue = os.path.join(QUEUE_PATH, long_name)
    long_name_path_processed = os.path.join(PROCESSED_PATH, long_name)

    if os.path.exists(long_name_path_queue):
        st.error(f"Name {escape_markdown(long_name)} already exists. Please rename.")
    elif os.path.exists(long_name_path_processed):
        st.error(f"Name {escape_markdown(long_name)} already exists. Please rename.")
    else:
        st.info(
            f"Filename will be: {escape_markdown(long_name)}. Click submit button to add to queue."
        )

        if (recorder['workflow']['match']) | (recorder['workflow']['match']):
            if len(recorder['experiment']['shortnames']) > 100:
                st.warning('Performance Warning: More than 100 files are selected and matching / align is selected.'
                'Matching / Align could take a long time. If you experience issues please contact mstrauss@biochem.mpg.de')

        if st.button("Submit"):
            settings = load_settings_as_template(DEFAULT_SETTINGS_PATH)
            for group in recorder:
                for key in recorder[group]:
                    settings[group][key] = recorder[group][key]

            save_settings(settings, long_name_path_queue)
            # Change things from experiment
            st.success(
                f"Experiment {escape_markdown(long_name)} submitted. Switch to Status tab to track progress."
            )


def customize_settings(recorder: dict, uploaded_settings: dict, loaded: bool) -> dict:
    """Widget to customize the settings with respect to the settings template.

    Args:
        recorder (dict): A dictionary that stores all widgets.
        uploaded_settings (dict): A dictionary that has uploaded settings.
        loaded (bool): Flag to indicate that data was uploaded.
    """

    with st.expander("Settings", loaded):
        checked = [_ for _ in recorder["workflow"] if not recorder["workflow"][_]]
        checked_ = []
        for _ in checked:
            if _ in WORKFLOW_DICT:
                checked_.extend(WORKFLOW_DICT[_])

        exclude = ["experiment", "workflow"] + checked_

        for key in SETTINGS_TEMPLATE.keys():
            if key not in exclude:

                group = SETTINGS_TEMPLATE[key]
                # Check if different than default
                if loaded:
                    changed = (
                        sum(
                            [
                                uploaded_settings[key][element]
                                != group[element]["default"]
                                for element in group
                            ]
                        )
                        > 0
                    )
                else:
                    changed = False

                if st.checkbox(key, changed):
                    for element in group:
                        override = None
                        if changed:
                            if (
                                uploaded_settings[key][element]
                                != group[element]["default"]
                            ):
                                override = uploaded_settings[key][element]

                        recorder = widget_from_setting(
                            recorder, key, group, element, override, indent=True
                        )

    return recorder


def file_df_from_files(raw_files: list, file_folder: str) -> pd.DataFrame:
    """Helper function that creates a pandas dataframe from a list of files.
    This function also adds the size of the files and the creation date.

    Args:
        raw_files (list): List of raw files.
        file_folder (str): Folder that contained the raw files.

    Returns:
        pd.DataFrame: DataFrame with file information.
    """
    raw_files.sort()
    sizes = [
        round(get_size(os.path.join(file_folder, _)) / 1024 ** 3, 2)
        for _ in raw_files
    ]
    created = [
        datetime.datetime.fromtimestamp(os.path.getctime(os.path.join(file_folder, _)))
        for _ in raw_files
    ]
    file_df = pd.DataFrame(
        list(zip(range(1, len(raw_files) + 1), raw_files, created, sizes)),
        columns=["#", "Filename", "Creation date", "Size (GB)"],
    )
    file_df["Shortname"] = [os.path.splitext(_)[0] for _ in raw_files]

    return file_df


def experiment():
    """Streamlit page to display the experiment tab."""
    error = 0
    st.write("# New experiment")
    st.write("## Files")

    recorder = {}
    recorder["experiment"] = {}

    cwd = os.getcwd()
    file_folder = st.text_input(
        "Enter path to folder that contains all experimental files. AlphaPept will parse for raw (.d / .raw), FASTA and AlphaPept database (.db_files.hdf) files and add them to the experiment.",
        cwd,
    )

    if not os.path.isdir(file_folder):
        st.warning("Not a valid folder.")
    else:
        with st.spinner("Parsing folder"):

            raw_files, fasta_files, db_files = parse_folder(file_folder)

            if st.button("Reload folder"):
                raw_files, fasta_files, db_files = parse_folder(file_folder)

            fasta_files = [os.path.join(file_folder, _) for _ in fasta_files]

            recorder["experiment"]["file_paths"] = [
                os.path.join(file_folder, _) for _ in raw_files
            ]

            if len(raw_files) == 0:
                st.warning("No raw files in folder.")

            else:
                exclude = st.multiselect("Exclude files", raw_files)
                raw_files = [_ for _ in raw_files if _ not in exclude]

                file_df = file_df_from_files(raw_files, file_folder)
                file_df['Sample group'] = file_df['Shortname']
                file_df['Fraction'] = [1 for i in range(len(file_df))]
                file_df["Matching group"] = [str(0)]*len(file_df)

                gb = GridOptionsBuilder.from_dataframe(file_df)
                gb.configure_default_column(
                    groupable=True,
                    value=True,
                    enableRowGroup=True,
                    aggFunc="sum",
                    editable=True,
                )
                gb.configure_grid_options(domLayout="normal")
                gridOptions = gb.build()

                grid_response = AgGrid(
                    file_df,
                    height=300,
                    gridOptions=gridOptions,
                )

                file_df_selected = grid_response["data"]

                with st.expander("Additional info"):
                    st.write(
                        "- Filename: Name of the file."
                        " \n- Creation date of file."
                        " \n- Size (GB): Size in GB of the file."
                        " \n- Shortname: Unique shortname for each file."
                        " \n- Sample group: Files with the same sample group will be quanted together (e.g. for fractionated samples)."
                        " \n- Fraction: Fraction number, if you have fractionated samples. Leave at 1 if no fractions exists."
                        " \n- Matching group: Match-between-runs only among members of this group or neighboring groups. Leave as is if matching between all files."
                    )

                shortnames = file_df_selected["Shortname"].values.tolist()
                if len(shortnames) != len(set(shortnames)):
                    st.warning("Warning: Shortnames are not unique.")
                    error += 1

                try:
                    matching_group = file_df_selected["Matching group"].values.astype('int').tolist()
                except:
                    matching_group = [str(0)]*len(file_df)

                    st.warning("Warning: Matching groups contain non-integer values. Please only use integers (0,1,2...).")
                    error += 1

                fasta_files_home_dir = files_in_folder(FASTA_PATH, ".fasta")
                fasta_files_home_dir = [
                    os.path.join(FASTA_PATH, _) for _ in fasta_files_home_dir
                ]

                fasta_files_home_dir += fasta_files

                selection = st.multiselect(
                    "Select FASTA files",
                    options=fasta_files_home_dir,
                    default=fasta_files,
                )
                recorder["experiment"]["fasta_paths"] = selection

                if len(recorder["experiment"]["fasta_paths"]) == 0:
                    st.warning("Warning: No FASTA files selected.")
                    error += 1

                recorder["experiment"]["shortnames"] = shortnames
                recorder["experiment"]["file_paths"] = [
                    os.path.join(file_folder, _)
                    for _ in file_df_selected["Filename"].values.tolist()
                ]

                recorder["experiment"]['sample_group'] = file_df_selected[
                    'Sample group'
                ].values.tolist()
                recorder["experiment"]['fraction'] = file_df_selected[
                    'Fraction'
                ].values.tolist()
                recorder["experiment"]["matching_group"] = matching_group

                st.write(f"## Workflow")

                with st.expander("Steps"):
                    group = SETTINGS_TEMPLATE["workflow"]
                    for element in group:
                        recorder = widget_from_setting(
                            recorder, "workflow", group, element
                        )

                st.write("## Modify settings")

                prev_settings = st.checkbox("Use previous settings as template")

                loaded = False
                uploaded_settings = None
                if prev_settings:
                    uploaded_file = st.file_uploader("Choose a file")
                    if uploaded_file is not None:
                        uploaded_settings = yaml.load(
                            uploaded_file, Loader=yaml.FullLoader
                        )
                        loaded = True

                recorder = customize_settings(recorder, uploaded_settings, loaded)

                st.write("## Submit experiment")
                if error != 0:
                    st.warning("Some warnings exist. Please check settings.")
                else:
                    submit_experiment(recorder)
