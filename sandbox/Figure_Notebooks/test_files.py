import os
import wget
import shutil


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

FILE_DICT['PXD006109_ref.txt'] = 'https://datashare.biochem.mpg.de/s/fLhxQ8mVb29x9xH/download'
FILE_DICT['PXD006109_ref_evd.txt'] = 'https://datashare.biochem.mpg.de/s/BkMMHPregCQgKLg/download'

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


def delete_folder(dir_name):
    if os.path.exists(dir_name):
        shutil.rmtree(dir_name)

def create_folder(dir_name):
    if not os.path.exists(dir_name):
        print(f'Creating dir {dir_name}.')
        os.makedirs(dir_name)

def get_files(folder, file_list):
    """
    Downloads files to test_files folder (this is meant to be an archive so that files only need to be downloaded once)
    """
    tmp_folder = os.path.join(folder, 'test_files')

    if not os.path.isdir(tmp_folder):
        os.mkdir(tmp_folder)

    for file in file_list:
        link = FILE_DICT[file]
        filename = os.path.join(tmp_folder, file)
        if not (os.path.isfile(filename) or os.path.isdir(filename)):
            print(f'Downloading {filename}.')
            if filename.endswith('.d'):
                wget.download(link, filename+'_temp')
                with zipfile.ZipFile(filename+'_temp', 'r') as zip_ref:
                    logging.info('Unzipping.')
                    zip_ref.extractall(filename+'_')

                print('Cleaning up zipfile')
                source_dir = os.path.join(filename+'_', os.listdir(filename+'_')[0])
                files_to_move = os.listdir(source_dir)
                os.mkdir(filename)
                for to_move in files_to_move:
                    shutil.move(os.path.join(source_dir, to_move), os.path.join(filename, to_move))
                os.rmdir(source_dir)
                os.rmdir(filename+'_')
            else:
                wget.download(link, filename)


def prepare_test(file_list, folder, target_folder):
    """
    Moves files to target_folder from tmp_folder
    """

    BASE_DIR = os.path.join(folder, 'test_files')
    TEST_DIR = os.path.join(folder, target_folder)

    delete_folder(TEST_DIR)
    create_folder(TEST_DIR)

    for file in file_list:
        if file.endswith('.d'):
            shutil.copytree(os.path.join(BASE_DIR, file), os.path.join(TEST_DIR, file))
        else:
            shutil.copyfile(os.path.join(BASE_DIR, file), os.path.join(TEST_DIR, file))
