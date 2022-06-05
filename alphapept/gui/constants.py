
import streamlit as st
import pandas as pd

import alphapept.constants
import alphapept.settings

@st.cache
def load_mods(path):
    df = pd.read_csv(path, delimiter="\t")
    return df


def constants():
    """Streamlit page to display internal constants / modifications."""
    st.write("# Constants")
    st.text(
        f"Constants shows modifications and proteases that are available in AlphaPept."
    )
    st.write('## Modificatios')
    st.text(
        f"Available modifications are generated from the *.tsv file located at {alphapept.constants.modfile_path}."
        "\nThis file can be modified to add custom modifications. After changing the modifications, restart AlphaPept or press button below."
        "\nThe column `Monoisotopic Mass Shift (Da)` will be used."
    )
    mod_df = load_mods(alphapept.constants.modfile_path)
    st.write(mod_df)

    st.write('## Amino Acids')
    st.text(
        f"Available amino acids are generated from the *.tsv file located at {alphapept.constants.aafile_path}."
        "\nThis file can be modified to add custom modifications. After changing the amino acids, restart AlphaPept press button below."
        "\nThe column `Monoisotopic Mass (Da)` will be used."
    )
    aa_df = load_mods(alphapept.constants.aafile_path)
    st.write(aa_df)

    st.write('## Proteases')
    protease_dict = alphapept.constants.protease_dict
    st.write(pd.DataFrame(protease_dict.items(), columns=['Protease', 'RegEx']))

    st.write('## Reload')
    if st.button('Reload constants'):
        alphapept.settings.create_default_settings()
        st.success('Done.')
