from configparser import ConfigParser
import os

config = ConfigParser(delimiters=['='])
config.read(
    os.path.join(
        os.path.dirname(__file__),
        '..',
        'settings.ini'
    )
)
cfg = config['DEFAULT']

LIB_NAME = cfg["lib_name"]
USER = cfg["user"]
DESCRIPTION = cfg["description"]
KEYWORDS = cfg["keywords"]
AUTHOR = cfg["author"]
AUTHOR_EMAIL = cfg["author_email"]
COPYRIGHT = cfg["copyright"]
BRANCH = cfg["branch"]
VERSION_NO = cfg["version"]
MIN_PYTHON = cfg["min_python"]
MAX_PYTHON = cfg["max_python"]
AUDIENCE = cfg["audience"]
LANGUAGE = cfg["language"]
CUSTOM_SIDEBAR = cfg["custom_sidebar"]
LICENSE = cfg["license"]
STATUS = cfg["status"]
NBS_PATH = cfg["nbs_path"]
DOC_PATH = cfg["doc_path"]
DOC_HOST = cfg["doc_host"]
DOC_BASEURL = cfg["doc_baseurl"]
GIT_URL = cfg["git_url"]
LIB_PATH = cfg["lib_path"]
TITLE = cfg["title"]
HOST = cfg["host"]
URL = cfg["url"]
URL_DOCUMENTATION = cfg["url_documentation"]
URL_ISSUE = cfg["url_issue"]
URL_CONTRIBUTE = cfg["url_contribute"]
