import wget
import logging
import shutil

import pandas as pd
from time import time
import os
from datetime import datetime
import sys
import platform
import zipfile
import subprocess
import numpy as np

import alphapept.interface
from alphapept.settings import load_settings, load_settings_as_template
import yaml
import alphapept
import alphapept.io
from alphapept.__version__ import VERSION_NO as alphapept_version
from alphapept.paths import DEFAULT_SETTINGS_PATH

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
FILE_DICT['arabidopsis.fasta'] = 'https://datashare.biochem.mpg.de/s/YQXTFSVnF4AMTOM/download'
FILE_DICT['all_uniprot_reviewed.fasta'] = 'https://datashare.biochem.mpg.de/s/QbzV6IvG2oHDYn6/download'

#PXD006109

FILE_DICT['PXD006109_HeLa12_1.raw'] = 'https://datashare.biochem.mpg.de/s/8S6i1KObhDKABft/download'
FILE_DICT['PXD006109_HeLa12_2.raw'] = 'https://datashare.biochem.mpg.de/s/y7uY3Pt6tq5PmFn/download'
FILE_DICT['PXD006109_HeLa12_3.raw'] = 'https://datashare.biochem.mpg.de/s/wl6Av0BKY2eShsd/download'
FILE_DICT['PXD006109_HeLa2_1.raw'] = 'https://datashare.biochem.mpg.de/s/QOi7Lsmsbr4NhnF/download'
FILE_DICT['PXD006109_HeLa2_2.raw'] = 'https://datashare.biochem.mpg.de/s/aZi5xdNQhaypRok/download'
FILE_DICT['PXD006109_HeLa2_3.raw'] = 'https://datashare.biochem.mpg.de/s/WiymcH8Oz58ASnx/download'

#PXD010012

FILE_DICT['PXD010012_CT_1_C1_01_Base.d'] = 'https://datashare.biochem.mpg.de/s/lAWp1NSk4Mvw89r/download'
FILE_DICT['PXD010012_CT_2_C1_01_Base.d'] = 'https://datashare.biochem.mpg.de/s/SoaccnPn9eaAM41/download'
FILE_DICT['PXD010012_CT_3_C1_01_Base.d'] = 'https://datashare.biochem.mpg.de/s/kGUNxrIf3AZMWNt/download'
FILE_DICT['PXD010012_CT_4_C1_01_Base.d'] = 'https://datashare.biochem.mpg.de/s/Rsaw8kj49ujZxBm/download'
FILE_DICT['PXD010012_CT_5_C1_01_Base.d'] = 'https://datashare.biochem.mpg.de/s/wTgzZ88hwdBLF1Q/download'
FILE_DICT['PXD010012_CT_1_C2_01_Ratio.d'] = 'https://datashare.biochem.mpg.de/s/DIwnuYgLPRtUPmF/download'
FILE_DICT['PXD010012_CT_2_C2_01_Ratio.d'] = 'https://datashare.biochem.mpg.de/s/ZofHi6wcJlTQD32/download'
FILE_DICT['PXD010012_CT_3_C2_01_Ratio.d'] = 'https://datashare.biochem.mpg.de/s/H8HLHxmQG9EFeMA/download'
FILE_DICT['PXD010012_CT_4_C2_01_Ratio.d'] = 'https://datashare.biochem.mpg.de/s/swO523hdX1aqN3R/download'
FILE_DICT['PXD010012_CT_5_C2_01_Ratio.d'] = 'https://datashare.biochem.mpg.de/s/Kbq97G9IzxQ8AHb/download'

BASE_DIR = 'E:/test_files/' # Storarge location for test files
TEST_DIR = 'E:/test_temp/'
ARCHIVE_DIR = 'E:/test_archive/'

MONGODB_USER = 'github_actions'
MONGODB_URL = 'ci.yue0n.mongodb.net/'


def delete_folder(dir_name):
    if os.path.exists(dir_name):
        shutil.rmtree(dir_name)


def create_folder(dir_name):
    if not os.path.exists(dir_name):
        logging.info(f'Creating dir {dir_name}.')
        os.makedirs(dir_name)

EXE_PATH = 'C:/actions-runner/_work/alphapept/alphapept/installer/one_click_windows/dist/alphapept/alphapept.exe'

class TestRun():
    """
    Class to prepare and download files to make a default test run
    """
    def __init__(self, id, experimental_files, fasta_paths, new_files, custom_settings = None):

        self.id = id
        self.file_paths = experimental_files
        self.fasta_paths = fasta_paths
        self.m_tol = 20
        self.m_offset = 20
        self.new_files = new_files

        self.custom_settings = custom_settings


        # Flag to run mixed_species_quantification
        self.run_mixed_analysis = None
        if os.path.isfile(EXE_PATH):
            self.exe_path = EXE_PATH
        else:
            self.exe_path = None


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

        self.settings = load_settings_as_template(DEFAULT_SETTINGS_PATH)
        self.settings['experiment']['file_paths'] =  [TEST_DIR + _ for _ in self.file_paths]
        self.settings['experiment']['fasta_paths'] = [TEST_DIR + _ for _ in self.fasta_paths]

        self.settings['search']['m_offset'] =  self.m_offset
        self.settings['search']['m_tol'] =  self.m_tol

    def run(self, password=None):
        if self.new_files:
            self.prepare_files()
        self.prepare_settings()

        report = {}
        report['timestamp'] = datetime.now()

        settings = self.settings

        if self.custom_settings is not None:
            for group in self.custom_settings:
                for key in self.custom_settings[group]:
                    settings[group][key] = self.custom_settings[group][key]

        start = time()
        if self.exe_path is not None: #call compiled exe file
            dirname = os.path.dirname(settings['experiment']['results_path'])
            settings_path = os.path.join(dirname, '_.yaml')
            with open(settings_path, "w") as file:
                yaml.dump(settings, file)

            logging.info(f'Starting exe from {self.exe_path}') #TODO: Change for different OS
            process = subprocess.Popen(f'"{self.exe_path}" workflow "{settings_path}"', stdout=subprocess.PIPE)
            for line in iter(process.stdout.readline, b''):  # replace '' with b'' for Python 3
                logging.info(line.decode('utf8'))

            base, ext = os.path.splitext(settings['experiment']['results_path'])
            settings_path = os.path.join(base, '.yaml')
            settings = load_settings(settings_path)
        else:
            settings = alphapept.interface.run_complete_workflow(settings)
        end = time()

        report['test_id'] = self.id
        report['settings'] = settings
        report['time_elapsed_min'] = (end-start)/60
        report['branch'] = subprocess.check_output("git branch --show-current").decode("utf-8").rstrip('\n')
        report['commit'] = subprocess.check_output("git rev-parse --verify HEAD").decode("utf-8").rstrip('\n')
        report['version'] = alphapept_version

        if self.exe_path:
            report['pyinstaller'] = True
        else:
            report['pyinstaller'] = False

        report['sysinfo'] = platform.uname()

        if self.run_mixed_analysis:
            species, groups = self.run_mixed_analysis
            report['mixed_species_quantification'] = self.mixed_species_quantification(self.settings, species, groups)


        report['protein_fdr_arabidopsis'] = self.mixed_species_fdr(self.settings, ('ARATH','HUMAN')) #ECO for now

        self.report = report
        if password:
            post_id = self.upload_to_db(password)
            # Copy results file to archive location
            base, ext = os.path.splitext(settings['experiment']['results_path'])
            shutil.copyfile(settings['experiment']['results_path'], ARCHIVE_DIR+str(post_id)+ext)

    def upload_to_db(self, password):
        from pymongo import MongoClient
        logging.info('Uploading to DB')
        string = f"mongodb+srv://{MONGODB_USER}:{password}@{MONGODB_URL}?ssl=true&ssl_cert_reqs=CERT_NONE"
        client = MongoClient(string)

        #When having keys with dots like filename.ms_data.hdf, mongodb causes an error. This is to remove the dots.
        report = self.report

        files_old = report['settings']['summary']['file_sizes']['files'].copy()
        report['settings']['summary']['file_sizes']['files'] = {}
        for file in files_old.keys():
            new_filename = file.replace('.ms_data.hdf', '')
            report['settings']['summary']['file_sizes']['files'][new_filename] = files_old[file]

        post_id = client['github']['performance_runs'].insert_one(report).inserted_id

        logging.info(f"Uploaded {post_id}.")

        return post_id

    def mixed_species_fdr(self, settings, species):
        """
        Estimate FDR by searching against differenft FASTAs
        """
        file_name = os.path.splitext(settings['experiment']['file_paths'][0])[0]+'.ms_data.hdf'
        df = alphapept.io.MS_Data_File(file_name).read(dataset_name='protein_fdr')
        fdr = len([_ for _ in df['protein_group'] if (species[0] in _) & (species[1] not in _)])/len(df)

        return fdr

    def mixed_species_quantification(self, settings, species, groups, min_count = 2):
        """
        Mixed species analysis
        """

        df = pd.read_hdf(settings['experiment']['results_path'], 'protein_table')
        results = {}

        for i in ['','_LFQ']:
            res = pd.DataFrame()

            if i == "_LFQ":
                groups = ([_+i for _ in groups[0]], [_+ i for _ in groups[1]])

            res['ratio'] = df[groups[0]].median(axis=1)
            res['base'] = df[groups[1]].median(axis=1)
            res['ratio_count'] = (df[groups[0]] != np.nan).sum(axis=1)
            res['base_count'] = (df[groups[1]] != np.nan).sum(axis=1)

            res['_ratio'] = np.log2(res['base'] / res['ratio'])
            res['_sum'] = np.log2(res['ratio'])

            valid = res.query('ratio_count >= @min_count and base_count >= @min_count')

            results['cv_median_ratio'+i] = np.nanmedian(df[groups[0]].std(axis=1) / df[groups[0]].mean(axis=1))
            results['cv_std_ratio'+i] = np.nanstd(df[groups[0]].std(axis=1) / df[groups[0]].mean(axis=1))

            results['cv_median_base'+i] = np.nanmedian(df[groups[1]].std(axis=1) / df[groups[1]].mean(axis=1))
            results['cv_std_base'+i] = np.nanstd(df[groups[1]].std(axis=1) / df[groups[1]].mean(axis=1))

            for s in species:
                sub = valid.loc[[_ for _ in valid.index if s in _]]['_ratio'].values
                sub_ratio = np.nanmean(sub[~np.isinf(sub)])
                sub_std = np.nanstd(sub[~np.isinf(sub)])

                results[s+i+'_mean'] = sub_ratio
                results[s+i+'_std'] = sub_std

            results['DELTA'+i]  = results[species[1]+i+'_mean'] - results[species[0]+i+'_mean']
            results['STD'+i]  = np.sqrt(results[species[1]+i+'_std']**2 + results[species[0]+i+'_std']**2)
            results['T'+i]  = results['DELTA'+i] / results['STD'+i]

        return results


def main():
    print(sys.argv, len(sys.argv))

    if len(sys.argv) == 2:
        password = None
        runtype = sys.argv[1]
    else:
        password = sys.argv[1]
        runtype = sys.argv[2]

    new_files = True

    if runtype == 'bruker_irt':
        files = ['bruker_IRT.d']
        fasta_files = ['IRT_fasta.fasta','contaminants.fasta']
        run = TestRun(runtype, files, fasta_files, new_files)
        run.run(password=password)
    elif runtype == 'bruker_hela':
        files = ['bruker_HeLa.d']
        fasta_files = ['human.fasta', 'arabidopsis.fasta', 'contaminants.fasta']
        run = TestRun(runtype, files, fasta_files, new_files)
        run.run(password=password)
    elif runtype == 'thermo_irt':
        files = ['thermo_IRT.raw']
        fasta_files = ['IRT_fasta.fasta','contaminants.fasta']
        run = TestRun(runtype, files, fasta_files, new_files)
        run.run(password=password)
    elif runtype == 'thermo_hela':
        files = ['thermo_HeLa.raw']
        fasta_files = ['human.fasta', 'arabidopsis.fasta', 'contaminants.fasta']
        run = TestRun(runtype, files, fasta_files, new_files)
        run.run(password=password)
    elif runtype == 'thermo_hela_large_fasta':
        files = ['thermo_HeLa.raw']
        fasta_files = ['all_uniprot_reviewed.fasta', 'contaminants.fasta']
        run = TestRun(runtype, files, fasta_files, new_files)
        run.run(password=password)
    elif runtype == 'thermo_hela_modifications':
        files = ['thermo_HeLa.raw']
        fasta_files = ['human.fasta', 'contaminants.fasta']
        custom_settings = {}
        fasta = {}
        fasta['mods_variable'] = ['oxM','pS','pT','pY']
        custom_settings['fasta'] = fasta
        run = TestRun(runtype, files, fasta_files, new_files, custom_settings)
        run.run(password=password)
    elif runtype == 'PXD006109':
        files = ['PXD006109_HeLa12_1.raw','PXD006109_HeLa12_2.raw','PXD006109_HeLa12_3.raw','PXD006109_HeLa2_1.raw','PXD006109_HeLa2_2.raw','PXD006109_HeLa2_3.raw']
        fasta_files = ['human.fasta','e_coli.fasta','contaminants.fasta']
        #Multi-Species test
        test_run = TestRun(runtype, files, fasta_files, new_files)
        species = ['HUMAN', 'ECO']
        groups = (['PXD006109_HeLa12_1', 'PXD006109_HeLa12_2', 'PXD006109_HeLa12_3'], ['PXD006109_HeLa2_1', 'PXD006109_HeLa2_2', 'PXD006109_HeLa2_3'])
        test_run.run_mixed_analysis = (species, groups)
        test_run.run(password=password)
    elif runtype == 'PXD010012':
        files =  ['PXD010012_CT_1_C1_01_Base.d', 'PXD010012_CT_2_C1_01_Base.d', 'PXD010012_CT_3_C1_01_Base.d', 'PXD010012_CT_4_C1_01_Base.d', 'PXD010012_CT_5_C1_01_Base.d', 'PXD010012_CT_1_C2_01_Ratio.d', 'PXD010012_CT_2_C2_01_Ratio.d', 'PXD010012_CT_3_C2_01_Ratio.d', 'PXD010012_CT_4_C2_01_Ratio.d', 'PXD010012_CT_5_C2_01_Ratio.d']
        fasta_files = ['human.fasta','e_coli.fasta','contaminants.fasta']
        #Multi-Species test
        test_run = TestRun(runtype, files, fasta_files, new_files)
        species = ['HUMAN', 'ECO']
        groups = (['PXD010012_CT_1_C2_01_Ratio', 'PXD010012_CT_2_C2_01_Ratio', 'PXD010012_CT_3_C2_01_Ratio', 'PXD010012_CT_4_C2_01_Ratio', 'PXD010012_CT_5_C2_01_Ratio'], ['PXD010012_CT_1_C1_01_Base', 'PXD010012_CT_2_C1_01_Base', 'PXD010012_CT_3_C1_01_Base', 'PXD010012_CT_4_C1_01_Base', 'PXD010012_CT_5_C1_01_Base'])
        test_run.run_mixed_analysis = (species, groups)
        test_run.run(password=password)

    else:
        raise NotImplementedError(runtype)


if __name__ == "__main__":
    main()
