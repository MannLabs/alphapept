from tqdm import tqdm as tqdm
from functools import partial
import logging

import os
import pandas as pd
import sys

from functools import partial

from alphapept.constants import mass_dict
from alphapept.search import search_parallel_db, search_parallel
from alphapept.utils import check_hardware, check_python_env, check_settings, assemble_df
from alphapept.recalibration import calibrate_hdf_parallel
from alphapept.io import raw_to_npz_parallel
from alphapept.score import score_hdf_parallel, protein_groups_hdf_parallel
from alphapept.feature_finding import find_and_save_features_parallel
from alphapept.fasta import pept_dict_from_search, generate_database, generate_spectra, save_database, generate_database_parallel
from alphapept.quantification import protein_profile_parallel, protein_profile, delayed_normalization


def tqdm_wrapper(pbar, update):
    current_value = pbar.n
    delta = update - current_value
    pbar.update(delta)

# Logger config
root = logging.getLogger()
root.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)-s - %(message)s', "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
root.addHandler(handler)


def run_alphapept(settings, callback=None):

    check_hardware()
    check_python_env()
    settings = check_settings(settings)

    database_path = settings['fasta']['database_path']

    # Database Creation
    if settings['fasta']['save_db']:
        if os.path.isfile(database_path):
            logging.info('Database path set and exists. Using {} as database.'.format(database_path))
        else:
            logging.info('Database path {} is not a file.'.format(database_path))
            for fasta_file in settings['fasta']['fasta_files']:
                if os.path.isfile(fasta_file):
                    logging.info('Found FASTA file {} with size {:.2f} Mb.'.format(fasta_file, os.stat(fasta_file).st_size/(1024**2)))
                else:
                    raise FileNotFoundError('File {} not found'.format(fasta_file))

            logging.info('Creating a new database from FASTA.')
            spectra, pept_dict, fasta_dict = generate_database_parallel(settings, callback = partial(tqdm_wrapper, tqdm(total=1)))
            logging.info('Digested {:,} proteins and generated {:,} spectra'.format(len(fasta_dict), len(spectra)))

            save_database(spectra, pept_dict, fasta_dict, **settings['fasta'])
            logging.info('Database saved to {}. Filesize of database is {:.2f} GB'.format(database_path, os.stat(database_path).st_size/(1024**3)))

            settings['fasta']['database_path'] = database_path

    else:
        logging.info('Not using a stored database. Create database on the fly.')

    # File Conversion
    files_npz = []
    to_convert = []

    for _ in settings['experiment']['files']:
        base, ext = os.path.splitext(_)
        npz_path = base+'.npz'
        files_npz.append(npz_path)
        if os.path.isfile(npz_path):
            logging.info('Found *.npz file or {}'.format(_))
        else:
            to_convert.append(_)
            logging.info('No *.npz file found for {}. Adding to conversion list.'.format(_))
    files_npz.sort()

    if len(to_convert) > 0:
        logging.info('Starting file conversion.')
        raw_to_npz_parallel(to_convert, settings, callback=partial(tqdm_wrapper, tqdm(total=1)))
        logging.info('File conversion complete.')

    settings['experiment']['files_npz'] = files_npz

    # Feature Finding
    to_convert = []
    for _ in settings['experiment']['files']:
        base, ext = os.path.splitext(_)
        hdf_path = base+'.hdf'

        if os.path.isfile(hdf_path):
            try:
                pd.read_hdf(hdf_path, 'features')
                logging.info('Found *.hdf with features for {}'.format(_))
            except KeyError:
                to_convert.append(_)
                logging.info('No *.hdf file with features found for {}. Adding to feature finding list.'.format(_))
        else:
            to_convert.append(_)
            logging.info('No *.hdf file with features found for {}. Adding to feature finding list.'.format(_))

    if len(to_convert) > 0:
        logging.info('Feature extraction for {} file(s).'.format(len(to_convert)))
        find_and_save_features_parallel(to_convert, settings, callback=partial(tqdm_wrapper, tqdm(total=1)))

    # First Search
    if settings['fasta']['save_db']:
        logging.info('Starting first search with DB.')
        fasta_dict, pept_dict = search_parallel_db(settings, callback=partial(tqdm_wrapper, tqdm(total=1)))

    else:
        logging.info('Starting first search.')
        fasta_dict = search_parallel(settings, callback=partial(tqdm_wrapper, tqdm(total=1)))
        pept_dict = None

    logging.info('First search complete.')


    # Recalibration and Second Search
    if settings['search']['calibrate']:
        logging.info('Performing recalibration.')

        offsets = calibrate_hdf_parallel(settings, callback=partial(tqdm_wrapper, tqdm(total=1)))

        logging.info('Recalibration complete.')

        if settings['fasta']['save_db']:
            logging.info('Starting second search with DB.')
            fasta_dict, pept_dict = search_parallel_db(settings, calibration=offsets, callback=partial(tqdm_wrapper, tqdm(total=1)))

        else:
            logging.info('Starting second search.')
            fasta_dict = search_parallel(settings, calibration=offsets, callback=partial(tqdm_wrapper, tqdm(total=1)))
            pept_dict = None

        logging.info('Second search complete.')

    # Scoring
    score_hdf_parallel(settings, callback=partial(tqdm_wrapper, tqdm(total=1)))
    logging.info('Scoring complete.')

    if not settings['fasta']['save_db']:
        pept_dict = pept_dict_from_search(settings)

    # Protein groups
    logging.info('Extracting protein groups.')
    # This is on each file individually -> when having repeats maybe use differently (if this matter at all )
    protein_groups_hdf_parallel(settings, pept_dict, fasta_dict, callback=partial(tqdm_wrapper, tqdm(total=1)))
    logging.info('Protein groups complete')

    logging.info('Assembling dataframe.')
    df = assemble_df(settings)
    logging.info('Assembly complete.')

    if settings['general']['find_features']:
        # We could include another protein fdr in here..
        if 'fraction' in df.keys():
            logging.info('Normalizing fractions.')
            df, normalization = delayed_normalization(df)
            df.to_hdf(settings['experiment']['evidence'], 'combined_protein_fdr_dn')
            pd.DataFrame(normalization).to_hdf(settings['experiment']['evidence'], 'fraction_normalization')
            field = settings['quantification']['mode']
            df = df.groupby(['experiment', 'precursor', 'protein', 'filename'])[['{}_dn'.format(field)]].sum().reset_index()
            logging.info('Complete. ')

        logging.info('Starting profile extraction.')
        protein_table = protein_profile_parallel(settings, df, callback=partial(tqdm_wrapper, tqdm(total=1)))
        protein_table.to_hdf(settings['experiment']['evidence'], 'protein_table')
        logging.info('LFQ complete.')

    import yaml

    base, ext = os.path.splitext(settings['experiment']['evidence'])
    out_path_settings = base+'.yaml'

    with open(out_path_settings, 'w') as file:
        yaml.dump(settings, file)

    logging.info('Settings saved to {}'.format(out_path_settings))
    logging.info('Complete')


if __name__ == "__main__":

    print('Runner not configured yet.')
