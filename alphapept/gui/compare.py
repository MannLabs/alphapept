import streamlit as st


def compare():
    st.write('# Compare')
    st.text('Compare the results of two different software.')


    file_folder_1 = st.text_input("Enter path to file 1.", os.getcwd())
    if not os.path.isdir(file_folder_1):
        st.warning('Not a valid folder.')
        file_folder_1 = None

    file_folder_2 = st.text_input("Enter path to file 2.", os.getcwd())
    if not os.path.isdir(file_folder_2):
        st.warning('Not a valid folder.')
        file_folder_2 = None

    if file_folder_1 is not None and file_folder_2 is not None:

        with st.spinner('Parsing Folder'):






    #else:
    #with st.spinner('Parsing folder'):
