import os
import datetime
import wget
import streamlit as st
from alphapept.paths import FASTA_PATH
from alphapept.gui.utils import files_in_folder_pandas

proteomes = {}
proteomes["Homo_sapiens_UP000005640"] = "UP000005640"
proteomes["Escherichia_coli_UP000000625"] = "UP000000625"
proteomes["Saccharomyces_cerevisiae_UP000002311"] = "UP000002311"
proteomes["Arabidopsis_thaliana_UP000006548"] = "UP000006548"

def fasta():
    """Streamlit page to display the FASTA tab."""
    st.write("# FASTA")

    st.text(
        f"AlphaPept looks for FASTA files in {FASTA_PATH}.\nThese can be selected in the new experiment tab.\nYou can add own FASTA files to this folder."
    )

    st.write("### Existing files")

    fasta_files = files_in_folder_pandas(FASTA_PATH)

    st.table(fasta_files)

    st.write("### Download FASTA from Uniprot")

    for p_ in proteomes:
        if st.button(p_):

            download_link = f"https://rest.uniprot.org/uniprotkb/stream?compressed=false&format=fasta&query={proteomes[p_]}%20AND%20%28reviewed%3Atrue%29"
            new_file = os.path.join(
                FASTA_PATH,
                datetime.datetime.today().strftime("%Y_%m_%d_") + p_ + ".fasta",
            )


            st.code(f"Downloading {p_} to {new_file}.")

            with st.spinner("Downloading.."):
                wget.download(download_link, new_file)

            st.success('Complete. Please refresh page.')
            st.stop()
