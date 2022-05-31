import os
from shutil import copyfile

_this_file = os.path.abspath(__file__)
_this_directory = os.path.dirname(_this_file)

HOME = os.path.expanduser("~")
AP_PATH = os.path.join(HOME, ".alphapept")
QUEUE_PATH = os.path.join(HOME, ".alphapept", "queue")
PROCESSED_PATH = os.path.join(HOME, ".alphapept", "finished")
FAILED_PATH = os.path.join(HOME, ".alphapept", "failed")
FASTA_PATH = os.path.join(HOME, ".alphapept", "fasta")

DEFAULT_SETTINGS_PATH = os.path.join(AP_PATH, 'default_settings.yaml')
SETTINGS_TEMPLATE_PATH = os.path.join(AP_PATH, 'settings_template.yaml')

PLOT_SETTINGS = os.path.join(AP_PATH, 'custom_plots.yaml')

PROCESS_FILE = os.path.join(QUEUE_PATH, 'process')
FILE_WATCHER_FILE = os.path.join(QUEUE_PATH, 'file_watcher')

for folder in [AP_PATH, QUEUE_PATH, PROCESSED_PATH, FAILED_PATH, FASTA_PATH]:
    if not os.path.isdir(folder):
        os.mkdir(folder)

if not os.path.isfile(PLOT_SETTINGS):
    copyfile(os.path.join(_this_directory, 'custom_plots.yaml'), PLOT_SETTINGS)
