import os
import alphapept.settings
import sys
sys.path.append(os.path.join(".."))
import test_ci


tmp_folder = os.path.join(os.getcwd(),'temp/')

BASE_DIR = os.path.join(tmp_folder , 'test_files/') # Storarge location for test files
TEST_DIR = os.path.join(tmp_folder, 'test_temp/')
ARCHIVE_DIR = os.path.join(tmp_folder, ' test_archive/')

MONGODB_USER = ''
MONGODB_URL = ''

if not os.path.isdir(tmp_folder):
    os.mkdir(tmp_folder)

test_ci.config_test_paths(BASE_DIR, TEST_DIR, ARCHIVE_DIR, MONGODB_USER, MONGODB_URL)

timing_check = {}

def get_timings(run):
    settings = alphapept.settings.load_settings(os.getcwd() + '/temp/test_temp/results.yaml')

    total = settings['summary']['timing']['total (min)']
    total_no_db = total - settings['summary']['timing']['create_database (min)']
    total_no_db_ff_raw = total_no_db - settings['summary']['timing']['feature_finding (min)'] - settings['summary']['timing']['import_raw_data (min)']

    return run, total, total_no_db, total_no_db_ff_raw

def run_and_time(run):
    try:
        test_ci.main(run)
        with open("timings.txt", "a") as text_file:
            text_file.write(f"{get_timings(run)}\n")
    except Exception as e:
        print(e)
        pass

if __name__ == "__main__":

    for run in ['thermo_irt','thermo_hela','PXD006109','bruker_irt','bruker_hela','PXD010012']:
        run_and_time(run)
