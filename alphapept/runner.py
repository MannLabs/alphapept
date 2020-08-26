import tqdm
import functools
import logging

import os
import pandas as pd
import sys


import alphapept.search
import alphapept.utils
import alphapept.recalibration
import alphapept.io
import alphapept.score
import alphapept.feature_finding
import alphapept.fasta
import alphapept.quantification

import yaml


def tqdm_wrapper(pbar, update):
    current_value = pbar.n
    delta = update - current_value
    pbar.update(delta)


# Logger config
root = logging.getLogger()
root.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)-s - %(message)s', "%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
root.addHandler(handler)


def run_alphapept(settings, callback=None):

    alphapept.utils.check_hardware()
    alphapept.utils.check_python_env()
    settings = alphapept.utils.check_settings(settings)

    if 'database_path' not in settings['fasta']:
        database_path = ''
    else:
        database_path = settings['fasta']['database_path']

    # Database Creation
    if settings['fasta']['save_db']:
        if os.path.isfile(database_path):
            logging.info(
                'Database path set and exists. Using {} as database.'.format(
                    database_path
                )
            )
        else:
            logging.info(
                'Database path {} is not a file.'.format(database_path)
            )
            for fasta_file in settings['fasta']['fasta_paths']:
                if os.path.isfile(fasta_file):
                    logging.info(
                        'Found FASTA file {} with size {:.2f} Mb.'.format(
                            fasta_file,
                            os.stat(fasta_file).st_size/(1024**2)
                        )
                    )
                else:
                    raise FileNotFoundError(
                        'File {} not found'.format(fasta_file)
                    )

            logging.info('Creating a new database from FASTA.')

            if not callback:
                cb = functools.partial(tqdm_wrapper, tqdm.tqdm(total=1))
            else:
                cb = callback

            (
                spectra,
                pept_dict,
                fasta_dict
            ) = alphapept.fasta.generate_database_parallel(
                settings,
                callback=cb
            )
            logging.info(
                'Digested {:,} proteins and generated {:,} spectra'.format(
                    len(fasta_dict),
                    len(spectra)
                )
            )

            alphapept.fasta.save_database(
                spectra,
                pept_dict,
                fasta_dict,
                **settings['fasta']
            )
            logging.info(
                'Database saved to {}. Filesize of database is {:.2f} GB'.format(
                    database_path,
                    os.stat(database_path).st_size/(1024**3)
                )
            )

            settings['fasta']['database_path'] = database_path

    else:
        logging.info(
            'Not using a stored database. Create database on the fly.'
        )

    # File Conversion
    files_npz = []
    to_convert = []

    for file_name in settings['experiment']['file_paths']:
        base, ext = os.path.splitext(file_name)
        npz_path = base+'.npz'
        files_npz.append(npz_path)
        if os.path.isfile(npz_path):
            logging.info('Found *.npz file or {}'.format(file_name))
        else:
            to_convert.append(file_name)
            logging.info(
                'No *.npz file found for {}. Adding to conversion list.'.format(file_name)
            )
    files_npz.sort()

    if len(to_convert) > 0:
        logging.info('Starting file conversion.')
        if not callback:
            cb = functools.partial(tqdm_wrapper, tqdm.tqdm(total=1))
        else:
            cb = callback
        alphapept.io.raw_to_npz_parallel(to_convert, settings, callback=cb)
        logging.info('File conversion complete.')

    # Feature Finding
    to_convert = []
    for file_name in settings['experiment']['file_paths']:
        base, ext = os.path.splitext(file_name)
        hdf_path = base+'.hdf'

        if os.path.isfile(hdf_path):
            try:
                pd.read_hdf(hdf_path, 'features')
                logging.info(
                    'Found *.hdf with features for {}'.format(file_name)
                )
                alphapept.utils.reset_hdf(hdf_path)
                alphapept.utils.resave_hdf(hdf_path)

            except KeyError:
                to_convert.append(file_name)
                logging.info(
                    'No *.hdf file with features found for {}. Adding to feature finding list.'.format(file_name)
                )
        else:
            to_convert.append(file_name)
            logging.info(
                'No *.hdf file with features found for {}. Adding to feature finding list.'.format(file_name)
            )

    if len(to_convert) > 0:
        logging.info(
            'Feature extraction for {} file(s).'.format(len(to_convert))
        )
        if not callback:
            cb = functools.partial(tqdm_wrapper, tqdm.tqdm(total=1))
        else:
            cb = callback

        alphapept.feature_finding.find_and_save_features_parallel(
            to_convert,
            settings,
            callback=cb
        )

    # First Search
    if settings['fasta']['save_db']:
        logging.info('Starting first search with DB.')

        if not callback:
            cb = functools.partial(tqdm_wrapper, tqdm.tqdm(total=1))
        else:
            cb = callback

        fasta_dict, pept_dict = alphapept.search.search_parallel_db(
            settings,
            callback=cb
        )

    else:
        logging.info('Starting first search.')

        if not callback:
            cb = functools.partial(tqdm_wrapper, tqdm.tqdm(total=1))
        else:
            cb = callback

        fasta_dict = alphapept.search.search_parallel(settings, callback=cb)
        pept_dict = None

    logging.info('First search complete.')

    # Recalibration and Second Search
    if settings['search']['calibrate']:
        logging.info('Performing recalibration.')

        if not callback:
            cb = functools.partial(tqdm_wrapper, tqdm.tqdm(total=1))
        else:
            cb = callback

        offsets = alphapept.recalibration.calibrate_hdf_parallel(
            settings,
            callback=cb
        )

        logging.info('Recalibration complete.')

        if settings['fasta']['save_db']:
            logging.info('Starting second search with DB.')

            if not callback:
                cb = functools.partial(tqdm_wrapper, tqdm.tqdm(total=1))
            else:
                cb = callback

            fasta_dict, pept_dict = alphapept.search.search_parallel_db(
                settings,
                calibration=offsets,
                callback=cb
            )

        else:
            logging.info('Starting second search.')

            if not callback:
                cb = functools.partial(tqdm_wrapper, tqdm.tqdm(total=1))
            else:
                cb = callback

            fasta_dict = alphapept.search.search_parallel(
                settings,
                calibration=offsets,
                callback=cb
            )
            pept_dict = None

        logging.info('Second search complete.')

    # Scoring

    if not callback:
        cb = functools.partial(tqdm_wrapper, tqdm.tqdm(total=1))
    else:
        cb = callback

    alphapept.score.score_hdf_parallel(settings, callback=cb)
    logging.info('Scoring complete.')

    if not settings['fasta']['save_db']:
        pept_dict = alphapept.fasta.pept_dict_from_search(settings)

    # Protein groups
    logging.info('Extracting protein groups.')

    if not callback:
        cb = functools.partial(tqdm_wrapper, tqdm.tqdm(total=1))
    else:
        cb = callback

    # This is on each file individually -> when having repeats maybe
    # use differently (if this matter at all )
    alphapept.score.protein_groups_hdf_parallel(
        settings,
        pept_dict,
        fasta_dict,
        callback=cb
    )
    logging.info('Protein groups complete')

    logging.info('Assembling dataframe.')
    df = alphapept.utils.assemble_df(settings)
    logging.info('Assembly complete.')

    field = settings['quantification']['mode']

    if field in df.keys():  # Check if the quantification information exists.
        # We could include another protein fdr in here..
        if 'fraction' in df.keys():
            logging.info('Delayed Normalization.')
            df, normalization = alphapept.quantification.delayed_normalization(
                df,
                field
            )
            pd.DataFrame(normalization).to_hdf(
                settings['experiment']['results_path'],
                'fraction_normalization'
            )
            df_grouped = df.groupby(
                ['shortname', 'precursor', 'protein', 'filename']
            )[['{}_dn'.format(field)]].sum().reset_index()
        else:
            df_grouped = df.groupby(
                ['shortname', 'precursor', 'protein', 'filename']
            )[field].sum().reset_index()

        df.to_hdf(
            settings['experiment']['results_path'],
            'combined_protein_fdr_dn'
        )

        logging.info('Complete. ')
        logging.info('Starting profile extraction.')

        if not callback:
            cb = functools.partial(tqdm_wrapper, tqdm.tqdm(total=1))
        else:
            cb = callback

        protein_table = alphapept.quantification.protein_profile_parallel(
            settings,
            df_grouped,
            callback=cb
        )
        protein_table.to_hdf(
            settings['experiment']['results_path'],
            'protein_table'
        )
        logging.info('LFQ complete.')

    base, ext = os.path.splitext(settings['experiment']['results_path'])
    out_path_settings = base+'.yaml'

    with open(out_path_settings, 'w') as file:
        yaml.dump(settings, file)

    logging.info('Settings saved to {}'.format(out_path_settings))
    logging.info('Complete')


if __name__ == "__main__":

    print('Runner not configured yet.')
