import streamlit as st
from menu import experiment, status, result, history, system
from PIL import Image
from alphapept.__version__ import VERSION_NO
import os

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>

"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

_this_file = os.path.abspath(__file__)
_this_directory = os.path.dirname(_this_file)
LOGO_PATH = os.path.join(_this_directory, 'ap_round.png')
image = Image.open(LOGO_PATH)
computer_name = os.environ['COMPUTERNAME']

st.sidebar.image(image, width = 300)
st.sidebar.code(f"AlphaPept {VERSION_NO} \n{computer_name}")

sidebar = {'Status': status,
           'New experiment': experiment,
           'Results': result,
           'History': history,
           'System': system}

menu = st.sidebar.radio("", list(sidebar.keys()))

if menu:
    sidebar[menu]()

link = '[AlphaPept on GitHub](https://github.com/MannLabs/alphapept)'
st.sidebar.markdown(link, unsafe_allow_html=True)
