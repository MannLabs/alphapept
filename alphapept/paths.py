import os
from shutil import copyfile

_this_file = os.path.abspath(__file__)
_this_directory = os.path.dirname(_this_file)

DEFAULT_SETTINGS_PATH = os.path.join(_this_directory, 'default_settings.yaml')
SETTINGS_TEMPLATE_PATH = os.path.join(_this_directory, 'settings_template.yaml')

HOME = os.path.expanduser("~")
AP_PATH = os.path.join(HOME, ".alphapept")
QUEUE_PATH = os.path.join(HOME, ".alphapept", "queue")
PROCESSED_PATH = os.path.join(HOME, ".alphapept", "finished")
FAILED_PATH = os.path.join(HOME, ".alphapept", "failed")
FASTA_PATH = os.path.join(HOME, ".alphapept", "fasta")

PLOT_SETTINGS = os.path.join(HOME, ".alphapept", 'custom_plots.yaml')

PROCESS_FILE = os.path.join(QUEUE_PATH, 'process')
FILE_WATCHER_FILE = os.path.join(QUEUE_PATH, 'file_watcher')

for folder in [AP_PATH, QUEUE_PATH, PROCESSED_PATH, FAILED_PATH, FASTA_PATH]:
    if not os.path.isdir(folder):
        os.mkdir(folder)

if not os.path.isfile(PLOT_SETTINGS):
    copyfile(os.path.join(_this_directory, 'custom_plots.yaml'), PLOT_SETTINGS)
