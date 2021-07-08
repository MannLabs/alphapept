import streamlit as st
from alphapept.paths import FASTA_PATH
from alphapept.gui.utils import files_in_folder_pandas
import os
import wget
import datetime

proteomes = {}
proteomes['Homo_sapiens_UP000005640'] = 'UP000005640'
proteomes['Escherichia_coli_UP000000625'] = 'UP000000625'
proteomes['Saccharomyces_cerevisiae_UP000002311'] = 'UP000002311'
proteomes['Arabidopsis_thaliana_UP000006548'] = 'UP000006548'

def fasta():
    st.write('# FASTA')

    st.text(f'AlphaPept looks for FASTA files in {FASTA_PATH}.\nThese can be selected in the new experiment tab.\nYou can add own FASTA files to this folder.')

    st.write('### Existing files')

    fasta_files = files_in_folder_pandas(FASTA_PATH)

    st.table(fasta_files)

    st.write('### Download FASTA from Uniprot')

    for p_ in proteomes:
        if st.button(p_):

            download_link = f'https://www.uniprot.org/uniprot/?query=proteome:{proteomes[p_]}%20reviewed:yes&format=fasta'
            new_file = os.path.join(FASTA_PATH, datetime.datetime.today().strftime('%Y_%m_%d_')+p_+'.fasta')

            st.code(f"Downloading {p_} to {new_file}.")

            download_bar = st.progress(0)

            def bar(current, total, width):
                download_bar.progress(current/total)

            with st.spinner('Downloading..'):
                wget.download(download_link, new_file, bar = bar)

            raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))
