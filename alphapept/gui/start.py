import streamlit as st
from alphapept.gui.utils import markdown_link
from alphapept.utils import check_github_version
from alphapept.__version__ import VERSION_NO

SHOW_WARNING = False
try:
    import clr
except ModuleNotFoundError:
    SHOW_WARNING = True

def start():
    """Streamlit page that displays information on how to get started."""
    st.write("# Getting started")
    st.text("Welcome to AlphaPept.")

    if SHOW_WARNING:
        st.warning('Pythonnet not found. Please check installation instructions.')

    with st.expander("Navigation"):
        st.write("Use the sidebar to the left to navigate through the different menus.")
        st.write(
            "- Status: Displays the current processing status."
            " \n- New experiment: Define a new experiment here."
            " \n- FASTA: Download FASTA files."
            " \n- Results: Explore the results of a run."
            " \n- History: Explore summary statistics of multiple processed files."
            " \n- FileWatcher: Set up a file watcher to automatically process files."
            " \n- Constants: Overview of availale modifications and proteases."
        )

    with st.expander("Resources"):
        st.write(
            "On the following pages you can find additional information about AlphaPept:"
        )
        markdown_link("AlphaPept on GitHub", "https://github.com/MannLabs/alphapept")
        markdown_link("Code documentation", "https://mannlabs.github.io/alphapept/")
        markdown_link(
            "Report an issue or suggest a feature (GitHub)",
            "https://github.com/MannLabs/alphapept/issues/new/choose",
        )
        markdown_link("Installation manual", "https://github.com/MannLabs/alphapept")
        markdown_link(
            "Understanding column names", "https://github.com/MannLabs/alphapept"
        )
        markdown_link(
            "Version performance",
            "https://charts.mongodb.com/charts-alphapept-itfxv/public/dashboards/5f671dcf-bcd6-4d90-8494-8c7f724b727b",
        )
        markdown_link(
            "Contact (e-mail)",
            f"mailto:opensource@alphapept.com?subject=AlphaPept({VERSION_NO})",
        )

    with st.expander("Server"):

        st.write(
            "When starting AlphaPept you launch a server that can be closed when closing the terminal window."
        )
        st.write(
            "If your firewall policy allows external access, this page can also be accessed from other computers in the network."
        )
        st.write(
            "The server starts an AlphaPept process in the background that will process new experiments once they are submitted."
        )

    with st.expander("Sample Run"):
        st.write("Download the following sample files:")
        markdown_link(
            "Download IRT sample here.",
            "https://datashare.biochem.mpg.de/s/GpXsATZtMwgQoQt/download",
        )
        markdown_link(
            "Download IRT FASTA here.",
            "https://datashare.biochem.mpg.de/s/p8Qu3KolzbSiCHH/download",
        )
        st.write("Put both files in one folder and go to the New experiment tab.")


    latest_version = check_github_version()
    if latest_version and (VERSION_NO != latest_version):
        st.info(
            f"You're using AlphaPept {VERSION_NO} but version {latest_version} is now avaliable! See [here](https://github.com/MannLabs/alphapept) for details"
        )
