# from configparser import ConfigParser
# import os
#
# config = ConfigParser(delimiters=['='])
# config.read(
#     os.path.join(
#         os.path.dirname(__file__),
#         '..',
#         'settings.ini'
#     )
# )
# cfg = config['DEFAULT']

# This was causing problems when library is not yet installed
#import sys
#if sys.version_info.minor == 6:
#    import importlib_metadata
#    metadata = importlib_metadata.metadata("alphapept")
#    VERSION_NO = metadata["Version"]
#if sys.version_info.minor == 7:
#    import pkg_resources
#    VERSION_NO = pkg_resources.get_distribution("alphapept").version
#elif sys.version_info.minor == 8:
#    import importlib.metadata
#    metadata = importlib.metadata.metadata("alphapept")
#    VERSION_NO = metadata["Version"]

LIB_NAME = "alphapept"
USER = "mannlabs"
DESCRIPTION = "A modular, python-based framework for mass spectrometry."
KEYWORDS = "MS, mass spectrometry, python, numba"
AUTHOR = "Maximilian T. Strauss"
AUTHOR_EMAIL = "straussmaximilian@gmail.com"
COPYRIGHT = "Mann Labs"
BRANCH = "master"
VERSION_NO = "0.4.9"
MIN_PYTHON = "3.6"
MAX_PYTHON = "4"
AUDIENCE = "Developers"
LANGUAGE = "English"
CUSTOM_SIDEBAR = "False"
LICENSE = "MIT"
STATUS = "2"
NBS_PATH = "nbs"
DOC_PATH = "docs"
DOC_HOST = "https://mannlabs.github.io"
DOC_BASEURL = "/alphapept/"
GIT_URL = "https://github.com/mannlabs/alphapept/tree/master/"
LIB_PATH = "alphapept"
TITLE = "alphapept"
HOST = "github"
URL = "https://github.com/MannLabs/alphapept"
URL_DOCUMENTATION = "https://mannlabs.github.io/alphapept/"
URL_ISSUE = "https://github.com/MannLabs/alphapept/issues"
URL_CONTRIBUTE = "https://github.com/MannLabs/alphapept/blob/master/CONTRIBUTING.md"
