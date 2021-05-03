import os 
from alphapept.settings import load_settings_as_template

_this_file = os.path.abspath(__file__)
_this_directory = os.path.dirname(_this_file)

DEFAULT_SETTINGS_PATH = os.path.join(_this_directory, 'default_settings.yaml')
SETTINGS_TEMPLATE_PATH = os.path.join(_this_directory, 'settings_template.yaml')

SETTINGS_TEMPLATE = load_settings_as_template(SETTINGS_TEMPLATE_PATH)

HOME = os.path.expanduser("~")
AP_PATH = os.path.join(HOME, "alphapept")
QUEUE_PATH = os.path.join(HOME, "alphapept", "queue")
PROCESSED_PATH = os.path.join(HOME, "alphapept", "finished")
FAILED_PATH = os.path.join(HOME, "alphapept", "failed")
PROCESS_FILE = os.path.join(QUEUE_PATH, 'process')
FILE_WATCHER_FILE = os.path.join(QUEUE_PATH, 'file_watcher')

for folder in [AP_PATH, QUEUE_PATH, PROCESSED_PATH, FAILED_PATH]:
    if not os.path.isdir(folder):
        os.mkdir(folder)
        

