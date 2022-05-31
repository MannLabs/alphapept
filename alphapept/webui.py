import streamlit as st
from alphapept.gui import history, results, filewatcher, status, experiment, fasta, start, constants
from PIL import Image
from alphapept.__version__ import VERSION_NO
import os
import socket

_this_file = os.path.abspath(__file__)
_this_directory = os.path.dirname(_this_file)
LOGO_PATH = os.path.join(_this_directory, 'ap_round.png')
ICON_PATH = os.path.join(_this_directory, 'favicon.ico')
image = Image.open(LOGO_PATH)
icon = Image.open(ICON_PATH)
computer_name = socket.gethostname()

st.set_page_config(
    page_title=f"Alphapept {VERSION_NO}",
    page_icon=icon,
    layout="wide",
)

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>

"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.sidebar.image(image, width = 300)
st.sidebar.code(f"AlphaPept {VERSION_NO} \n{computer_name}")

sidebar = {'Start': start.start,
           'Status': status.status,
           'New experiment': experiment.experiment,
           'FASTA': fasta.fasta,
           'Results': results.results,
           'History': history.history,
           'FileWatcher': filewatcher.filewatcher,
           'Constants': constants.constants}

menu = st.sidebar.radio("", list(sidebar.keys()))

if menu:
    sidebar[menu]()

link = '[AlphaPept on GitHub](https://github.com/MannLabs/alphapept)'
st.sidebar.markdown(link, unsafe_allow_html=True)
