import wget
import logging
import shutil
from pymongo import MongoClient
import pandas as pd
from time import time
import os
from datetime import datetime
import sys
import platform
import zipfile
import subprocess

from alphapept.runner import run_alphapept
from alphapept.settings import load_settings
import alphapept
import alphapept.io
from alphapept.__version__ import VERSION_NO as alphapept_version


# Global dictionary to store links to the files
FILE_DICT = {}
FILE_DICT['thermo_IRT.raw'] = 'https://datashare.biochem.mpg.de/s/GpXsATZtMwgQoQt/download'
FILE_DICT['bruker_IRT.d'] = 'https://datashare.biochem.mpg.de/s/2sWNvImHwdELg55/download'
FILE_DICT['thermo_HeLa.raw'] = 'https://datashare.biochem.mpg.de/s/QGdWkld0oXN768W/download'
FILE_DICT['bruker_HeLa.d'] = 'https://datashare.biochem.mpg.de/s/h2skyiMU9qWKKv2/download'
FILE_DICT['IRT_fasta.fasta'] = 'https://datashare.biochem.mpg.de/s/p8Qu3KolzbSiCHH/download'
FILE_DICT['contaminants.fasta'] = 'https://datashare.biochem.mpg.de/s/aRaFlwxdCH08OWd/download'
FILE_DICT['human.fasta'] = 'https://datashare.biochem.mpg.de/s/7KvRKOmMXQTTHOp/download'
FILE_DICT['yeast.fasta'] = 'https://datashare.biochem.mpg.de/s/8zioyWKVHEPeo34/download'
FILE_DICT['e_coli.fasta'] = 'https://datashare.biochem.mpg.de/s/ZUqqruTOxBbSf1k/download'

BASE_DIR = 'C:/test_files/' # Storarge location for test files
TEST_DIR = 'C:/test_temp/'

MONGODB_USER = 'github_actions'
MONGODB_URL = 'ci.yue0n.mongodb.net/'


def delete_folder(dir_name):
    if os.path.exists(dir_name):
        shutil.rmtree(dir_name)


def create_folder(dir_name):
    if not os.path.exists(dir_name):
        logging.info(f'Creating dir {dir_name}.')
        os.makedirs(dir_name)


class TestRun():
    """
    Class to prepare and download files to make a default test run
    """
    def __init__(self, experimental_files, fasta_paths):

        self.file_paths = experimental_files
        self.fasta_paths = fasta_paths
        self.m_tol = 20
        self.m_offset = 20

    def get_file(self, filename, link):
        """
        Downloads test file or folder if it does not exist yet.
        """
        if not (os.path.isfile(filename) or os.path.isdir(filename)):
            logging.info(f'Downloading {filename}.')
            if filename.endswith('.d'):
                wget.download(link, filename+'_temp')
                with zipfile.ZipFile(filename+'_temp', 'r') as zip_ref:
                    logging.info('Unzipping.')
                    zip_ref.extractall(filename+'_')

                logging.info('Cleaning up zipfile')
                source_dir = os.path.join(filename+'_', os.listdir(filename+'_')[0])
                files_to_move = os.listdir(source_dir)
                os.mkdir(filename)
                for to_move in files_to_move:
                    shutil.move(os.path.join(source_dir, to_move), os.path.join(filename, to_move))
                os.rmdir(source_dir)
                os.rmdir(filename+'_')
            else:
                wget.download(link, filename)

    def prepare_files(self):
        """
        Downloads files to base_dir and copies to test folder for a test run
        """
        create_folder(BASE_DIR)

        for file in self.file_paths + self.fasta_paths:
            self.get_file(BASE_DIR+file, FILE_DICT[file])

        delete_folder(TEST_DIR)
        create_folder(TEST_DIR)

        for file in self.file_paths + self.fasta_paths:

            if file.endswith('.d'):
                shutil.copytree(BASE_DIR+file, TEST_DIR+file)
            else:
                shutil.copyfile(BASE_DIR+file, TEST_DIR+file)

    def prepare_settings(self):
        """
        Prepares the settings according to the test run
        """

        self.settings = load_settings('default_settings.yaml')
        self.settings['experiment']['file_paths'] =  [TEST_DIR + _ for _ in self.file_paths]

        self.settings['fasta']['fasta_paths'] = [TEST_DIR + _ for _ in self.fasta_paths]

        self.settings['search']['m_offset'] =  self.m_offset
        self.settings['search']['m_tol'] =  self.m_tol

    def run(self, password=None):
        self.prepare_files()
        self.prepare_settings()

        report = {}
        report['timestamp'] = datetime.now()

        start = time()
        settings = run_alphapept(self.settings)
        end = time()

        report['settings'] = settings
        report['time_elapsed_min'] = (end-start)/60

        report['branch'] = subprocess.check_output("git branch --show-current").decode("utf-8").rstrip('\n')
        report['commit'] = subprocess.check_output("git rev-parse --verify HEAD").decode("utf-8").rstrip('\n')

        report['version'] = alphapept_version

        report['sysinfo'] = platform.uname()

        #File Sizes:
        report['file_sizes'] = {}
        report['file_sizes']['database'] = os.path.getsize(settings['fasta']['database_path'])/1024**2

        summary = {}

        file_sizes = {}
        for _ in settings['experiment']['file_paths']:

            base, ext = os.path.splitext(_)
            filename = os.path.split(base)[1]
            file_sizes[base+"_ms_data"] = os.path.getsize(os.path.splitext(_)[0] + ".ms_data.hdf")/1024**2
            # file_sizes[base+"_result"] = os.path.getsize(os.path.splitext(_)[0] + ".hdf")/1024**2

            ms_data = alphapept.io.MS_Data_File(os.path.splitext(_)[0] + ".ms_data.hdf")
            for key in ms_data.read():
                if "is_pd_dataframe" in ms_data.read(
                    attr_name="",
                    group_name=key
                ):
                    summary[filename+'_'+key.lstrip('/')] = len(
                        ms_data.read(
                            dataset_name=key,
                        )
                    )


        report['file_sizes']['files'] = file_sizes
        report['file_sizes']['results'] = os.path.getsize(settings['experiment']['results_path'])/1024**2

        report['results'] = summary

        self.report = report
        if password:
            self.upload_to_db(password)

    def upload_to_db(self, password):

        logging.info('Uploading to DB')
        string = f"mongodb+srv://{MONGODB_USER}:{password}@{MONGODB_URL}"
        client = MongoClient(string)

        post_id = client['github']['performance_runs'].insert_one(self.report).inserted_id

        logging.info(f"Uploaded {post_id}.")


class BrukerTestRun(TestRun):
    def __init__(self, *args):
        TestRun.__init__(self, *args)

        self.m_tol = 30
        self.m_offset = 30


class ThermoTestRun(TestRun):
    def __init__(self, *args):
        TestRun.__init__(self, *args)
        self.m_tol = 20
        self.m_offset = 20


def main():
    print(sys.argv, len(sys.argv))

    password = sys.argv[1]
    runtype = sys.argv[2]
    files = sys.argv[3].strip('[]').split(',')
    fasta_files = sys.argv[4].strip('[]').split(',')

    if runtype == 'bruker':
        BrukerTestRun(files, fasta_files).run(password=password)
    elif runtype == 'thermo':
        ThermoTestRun(files, fasta_files).run(password=password)
    else:
        raise NotImplementedError(runtype)


if __name__ == "__main__":
   main()
