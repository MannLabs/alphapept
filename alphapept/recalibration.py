# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/07_recalibration.ipynb (unless otherwise specified).

__all__ = ['remove_outliers', 'transform', 'kneighbors_calibration', 'get_calibration', 'chunks', 'density_scatter',
           'save_fragment_calibration', 'save_precursor_calibration', 'calibrate_fragments_nn', 'calibrate_hdf',
           'get_db_targets', 'align_run_to_db', 'calibrate_fragments']

# Cell

import numpy as np
import pandas as pd

def remove_outliers(
    df:  pd.DataFrame,
    outlier_std: float) -> pd.DataFrame:
    """Helper function to remove outliers from a dataframe.
    Outliers are removed based on the precursor offset mass (prec_offset).
    All values within x standard deviations to the median are kept.

    Args:
        df (pd.DataFrame): Input dataframe that contains a prec_offset_ppm-column.
        outlier_std (float): Range of standard deviations to filter outliers

    Raises:
        ValueError: An error if the column is not present in the dataframe.

    Returns:
        pd.DataFrame: A dataframe w/o outliers.
    """

    if 'prec_offset_ppm' not in df.columns:
        raise ValueError(f"Column prec_offset_ppm not in df")
    else:
        # Remove outliers for calibration
        o_mass_std = np.abs(df['prec_offset_ppm'].std())
        o_mass_median = df['prec_offset_ppm'].median()

        df_sub = df.query('prec_offset_ppm < @o_mass_median+@outlier_std*@o_mass_std and prec_offset_ppm > @o_mass_median-@outlier_std*@o_mass_std').copy()

        return df_sub

# Cell

def transform(
    x:  np.ndarray,
    column: str,
    scaling_dict: dict) -> np.ndarray:
    """Helper function to transform an input array for neighbors lookup used for calibration

    Note: The scaling_dict stores information about how scaling is applied and is defined in get_calibration

    Relative transformation: Compare distances relatively, for mz that is ppm, for mobility %.
    Absolute transformation: Compare distance absolute, for RT it is the timedelta.

    An example definition is below:

    scaling_dict = {}
    scaling_dict['mz'] = ('relative', calib_mz_range/1e6)
    scaling_dict['rt'] = ('absolute', calib_rt_range)
    scaling_dict['mobility'] = ('relative', calib_mob_range)

    Args:
        x (np.ndarray): Input array.
        column (str): String to lookup what scaling should be applied.
        scaling_dict (dict): Lookup dict to retrieve the scaling operation and factor for the column.

    Raises:
        KeyError: An error if the column is not present in the dict.
        NotImplementedError: An error if the column is not present in the dict.

    Returns:
        np.ndarray: A scaled array.
    """
    if column not in scaling_dict:
        raise KeyError(f"Column {_} not in scaling_dict")
    else:
        type_, scale_ = scaling_dict[column]

        if type_ == 'relative':
            return np.log(x, out=np.zeros_like(x), where=(x>0))/scale_
        elif type_ == 'absolute':
            return x/scale_
        else:
            raise NotImplementedError(f"Type {type_} not known.")

# Cell

from sklearn.neighbors import KNeighborsRegressor
import logging

def kneighbors_calibration(df: pd.DataFrame, features: pd.DataFrame, cols: list, target: str, scaling_dict: dict, calib_n_neighbors: int) -> np.ndarray:
    """Calibration using a KNeighborsRegressor.
    Input arrays from are transformed to be used with a nearest-neighbor approach.
    Based on neighboring points a calibration is calculated for each input point.

    Args:
        df (pd.DataFrame): Input dataframe that contains identified peptides (w/o outliers).
        features (pd.DataFrame): Features dataframe for which the masses are calibrated.
        cols (list): List of input columns for the calibration.
        target (str): Target column on which offset is calculated.
        scaling_dict (dict): A dictionary that contains how scaling operations are applied.
        calib_n_neighbors (int): Number of neighbors for calibration.

    Returns:
        np.ndarray: A numpy array with calibrated masses.
    """

    data = df[cols]
    tree_points = data.values

    for idx, _ in enumerate(data.columns):
        tree_points[:, idx] = transform(tree_points[:, idx], _, scaling_dict)

    target_points = features[[_+'_matched' for _ in cols]].values

    for idx, _ in enumerate(data.columns):
        target_points[:, idx] = transform(target_points[:, idx], _, scaling_dict)

    if len(tree_points) >= calib_n_neighbors:
        neigh = KNeighborsRegressor(n_neighbors=calib_n_neighbors, weights = 'distance')
        neigh.fit(tree_points, df[target].values)

        y_hat = neigh.predict(target_points)
    else:
        logging.info('Number of identified peptides is smaller than the number of neighbors set for calibration. Skipping calibration.')
        y_hat = np.zeros(len(target_points))

    return y_hat

# Cell

def get_calibration(
    df: pd.DataFrame,
    features:pd.DataFrame,
    file_name = '',
    settings = None,
    outlier_std: float = 3,
    calib_n_neighbors: int = 100,
    calib_mz_range: int = 100,
    calib_rt_range: float = 0.5,
    calib_mob_range: float = 0.3,
    **kwargs) -> (np.ndarray, float):
    """Wrapper function to get calibrated values for the precursor mass.

    Args:
        df (pd.DataFrame): Input dataframe that contains identified peptides.
        features (pd.DataFrame): Features dataframe for which the masses are calibrated.
        outlier_std (float, optional): Range in standard deviations for outlier removal. Defaults to 3.
        calib_n_neighbors (int, optional): Number of neighbors used for regression. Defaults to 100.
        calib_mz_range (int, optional): Scaling factor for mz range. Defaults to 20.
        calib_rt_range (float, optional): Scaling factor for rt_range. Defaults to 0.5.
        calib_mob_range (float, optional): Scaling factor for mobility range. Defaults to 0.3.
        **kwargs: Arbitrary keyword arguments so that settings can be passes as whole.


    Returns:
        corrected_mass (np.ndarray): The calibrated mass
        y_hat_std (float): The standard deviation of the precursor offset after calibration

    """


    target = 'prec_offset_ppm'
    cols = ['mz','rt']

    if 'mobility' in df.columns:
        cols += ['mobility']

    scaling_dict = {}
    scaling_dict['mz'] = ('relative', calib_mz_range/1e6)
    scaling_dict['rt'] = ('absolute', calib_rt_range)
    scaling_dict['mobility'] = ('relative', calib_mob_range)

    df_sub = remove_outliers(df, outlier_std)

    if len(df_sub) > calib_n_neighbors:

        y_hat_ = kneighbors_calibration(df_sub, features, cols, target, scaling_dict, calib_n_neighbors) #ppm
        corrected_mass = (1-y_hat_/1e6) * features['mass_matched']

        feature_lookup_dict = features['feature_idx'].to_dict()
        feature_lookup_dict_r = {v:k for k,v in feature_lookup_dict.items()}
        features.iloc[df_sub['feature_idx'].apply(lambda x: feature_lookup_dict_r[x]).values]
        y_hat = y_hat_[df_sub['feature_idx'].apply(lambda x: feature_lookup_dict_r[x]).values]

        #Correction
        correction = df_sub['prec_offset_ppm'].values - y_hat

        y_hat_std = correction.std()

        mad_offset = np.median(np.absolute(correction - np.median(correction)))

        logging.info(f'Precursor calibration std {y_hat_std:.2f}, {mad_offset:.2f}')

        if settings is not None:
            logging.info(f'Saving precursor calibration')
            df_sub['delta_ppm'] =  df_sub['prec_offset_ppm']

            save_precursor_calibration(df_sub, correction, y_hat_std, file_name, settings)

        return corrected_mass, y_hat_std, mad_offset


    else:
        logging.info('Not enough data points present. Skipping recalibration.')

        mad_offset = np.median(np.absolute(df['prec_offset_ppm'].values - np.median(df['prec_offset_ppm'].values)))

        return features['mass_matched'], np.abs(df['prec_offset_ppm'].std()), mad_offset

# Cell

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize
from scipy.interpolate import interpn

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def density_scatter( x , y, ax = None, sort = True, bins = 20, **kwargs )   :
    """
    Scatter plot colored by 2d histogram
    Adapted from https://stackoverflow.com/questions/20105364/how-can-i-make-a-scatter-plot-colored-by-density-in-matplotlib
    """

    data , x_e, y_e = np.histogram2d( x, y, bins = bins, density = True )
    z = interpn( ( 0.5*(x_e[1:] + x_e[:-1]) , 0.5*(y_e[1:]+y_e[:-1]) ) , data , np.vstack([x,y]).T , method = "splinef2d", bounds_error = False)

    #To be sure to plot all data
    z[np.where(np.isnan(z))] = 0.0

    # Sort the points by density, so that the densest points are plotted last
    if sort :
        idx = z.argsort()
        x, y, z = x[idx], y[idx], z[idx]

    ax.scatter( x, y, c=z, cmap='turbo', **kwargs )

    return ax

def save_fragment_calibration(fragment_ions, corrected, std_offset, file_name, settings):

    f, axes = plt.subplots(2, 2, figsize=(20,10))

    ax1 = axes[0,0]
    ax2 = axes[1,0]
    ax3 = axes[0,1]
    ax4 = axes[1,1]

    ax1 = density_scatter(fragment_ions['rt'].values, fragment_ions['delta_ppm'].values, ax = ax1)
    ax1.set_title('Fragment error before correction')
    ax1.axhline(0, color='w', linestyle='-', alpha=0.5)
    ax1.set_ylabel('Error (ppm)')
    ax1.set_xlabel('RT (min)')

    ax2 = density_scatter(fragment_ions['rt'].values, corrected.values, ax = ax2)
    ax1.axhline(0, color='w', linestyle='-', alpha=0.5)
    ax2.axhline(0, color='w', linestyle='-', alpha=0.5)
    ax2.axhline(0+std_offset*settings['search']['calibration_std_frag'], color='r', linestyle=':', alpha=0.5)
    ax2.axhline(0-std_offset*settings['search']['calibration_std_frag'], color='r', linestyle=':', alpha=0.5)

    ax2.set_title('Fragment error after correction')
    ax2.set_ylabel('Error (ppm)')
    ax2.set_xlabel('RT (min)')

    ax3 = density_scatter(fragment_ions['fragment_ion_mass'].values, fragment_ions['delta_ppm'].values, bins=50, ax = ax3)
    ax3.axhline(0, color='w', linestyle='-', alpha=0.5)

    ax3.set_ylabel('Error (ppm)')
    ax3.set_xlabel('m/z')
    ax3.set_xlim([100,1500])
    ax3.set_title('Fragment error before correction')

    ax4 = density_scatter(fragment_ions['fragment_ion_mass'].values, corrected.values, bins=50, ax = ax4)

    ax4.set_ylabel('Error (ppm)')
    ax4.set_xlabel('m/z')
    ax4.set_xlim([100, 1500])
    ax4.set_title('Fragment error after correction')

    ax4.axhline(0, color='w', linestyle='-', alpha=0.5)
    ax4.axhline(0+std_offset*settings['search']['calibration_std_frag'], color='r', linestyle=':', alpha=0.5)
    ax4.axhline(0-std_offset*settings['search']['calibration_std_frag'], color='r', linestyle=':', alpha=0.5)

    base, ext = os.path.splitext(file_name)

    plt.suptitle(f"Fragment {os.path.split(file_name)[1]}")

    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_ylim([-settings['search']['frag_tol'], settings['search']['frag_tol']])

    plt.savefig(base+'_frag_calib.png')

def save_precursor_calibration(df, corrected, std_offset, file_name, settings):

    f, axes = plt.subplots(2, 2, figsize=(20,10))

    ax1 = axes[0,0]
    ax2 = axes[1,0]
    ax3 = axes[0,1]
    ax4 = axes[1,1]

    ax1 = density_scatter(df['rt'].values, df['delta_ppm'].values, ax = ax1)
    ax1.set_title('Precursor error before correction')
    ax1.axhline(0, color='w', linestyle='-', alpha=0.5)
    ax1.set_ylabel('Error (ppm)')
    ax1.set_xlabel('RT (min)')

    ax2 = density_scatter(df['rt'].values, corrected, ax = ax2)
    ax1.axhline(0, color='w', linestyle='-', alpha=0.5)
    ax2.axhline(0, color='w', linestyle='-', alpha=0.5)
    ax2.axhline(0+std_offset*settings['search']['calibration_std_prec'], color='r', linestyle=':', alpha=0.5)
    ax2.axhline(0-std_offset*settings['search']['calibration_std_prec'], color='r', linestyle=':', alpha=0.5)

    ax2.set_title('Precursor error after correction')
    ax2.set_ylabel('Error (ppm)')
    ax2.set_xlabel('RT (min)')

    ax3 = density_scatter(df['mz'].values, df['delta_ppm'].values, bins=50, ax = ax3)
    ax3.axhline(0, color='w', linestyle='-', alpha=0.5)

    ax3.set_ylabel('Error (ppm)')
    ax3.set_xlabel('m/z')
    ax3.set_xlim([100,1500])
    ax3.set_title('Precursor error before correction')

    ax4 = density_scatter(df['mz'].values, corrected, bins=50, ax = ax4)

    ax4.set_ylabel('Error (ppm)')
    ax4.set_xlabel('m/z')
    ax4.set_xlim([100, 1500])
    ax4.set_title('Precursor error after correction')

    ax4.axhline(0, color='w', linestyle='-', alpha=0.5)
    ax4.axhline(0+std_offset*settings['search']['calibration_std_prec'], color='r', linestyle=':', alpha=0.5)
    ax4.axhline(0-std_offset*settings['search']['calibration_std_prec'], color='r', linestyle=':', alpha=0.5)

    base, ext = os.path.splitext(file_name)

    plt.suptitle(f"Precursor {os.path.split(file_name)[1]}")

    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_ylim([-settings['search']['prec_tol'], settings['search']['prec_tol']])

    plt.savefig(base+'_prec_calib.png')


def calibrate_fragments_nn(ms_file_, file_name, settings):
    logging.info('Starting fragment calibration.')
    skip = False

    try:
        logging.info(f'Calibrating fragments with neighbors')
        fragment_ions = ms_file_.read(dataset_name='fragment_ions')
    except KeyError:
        logging.info('No fragment_ions to calibrate fragment masses found')
        skip = True

    if not skip:
        calib_n_neighbors = 400
        psms = ms_file_.read(dataset_name='first_search')
        psms['psms_index'] = np.arange(len(psms))

        df = score_generic(
            psms,
            fdr_level=settings["search"]["peptide_fdr"],
            plot=False,
            verbose=False,
            **settings["search"]
        )

        #Only calibrate on b & y
        fragment_ions = fragment_ions[fragment_ions['fragment_ion_type'] == 0]
        fragment_ions['delta_ppm'] = ((fragment_ions['db_mass'] - fragment_ions['fragment_ion_mass'])/((fragment_ions['db_mass'] + fragment_ions['fragment_ion_mass'])/2)*1e6).values


        ##Outlier removal

        calib_std = settings["calibration"]['outlier_std']

        delta_ppm = fragment_ions['delta_ppm']

        upper_bound = delta_ppm[delta_ppm>0].std()*calib_std
        lower_bound = -delta_ppm[delta_ppm<0].std()*calib_std

        fragment_ions = fragment_ions[(delta_ppm<upper_bound)&(delta_ppm>lower_bound)]

        #Calculate offset
        psms['keep'] = False
        psms.loc[df['psms_index'].tolist(),'keep'] = True

        fragment_ions['hits'] = psms['hits'][fragment_ions['psms_idx'].values.astype('int')].values
        fragment_ions['keep'] = psms['keep'][fragment_ions['psms_idx'].values.astype('int')].values

        min_score = fragment_ions['hits'].min()
        logging.info(f'Minimum hits for fragments before score {min_score:.2f}.')

        fragment_ions = fragment_ions[fragment_ions['keep']]
        min_score = fragment_ions['hits'].min()
        logging.info(f'Minimum hits for fragments after score {min_score:.2f}.')

        fragment_ions['rt'] = psms['rt'][fragment_ions['psms_idx'].values.astype('int')].values

        if len(fragment_ions) >= calib_n_neighbors:

            #Train regressor
            neigh = KNeighborsRegressor(n_neighbors=calib_n_neighbors, weights = 'distance')
            neigh.fit(fragment_ions['rt'].values.reshape(-1, 1), fragment_ions['delta_ppm'].values)

            #Read required datasets

            rt_list_ms2 = ms_file_.read_DDA_query_data()['rt_list_ms2']
            mass_list_ms2 = ms_file_.read_DDA_query_data()['mass_list_ms2']
            incides_ms2 = ms_file_.read_DDA_query_data()['indices_ms2']
            scan_idx = np.searchsorted(incides_ms2, np.arange(len(mass_list_ms2)), side='right') - 1

            #Estimate offset
            chunk_size = min((len(rt_list_ms2), len(fragment_ions), int(1e4)))
            y_hat = np.concatenate([neigh.predict(_) for _ in chunks(rt_list_ms2.reshape(-1, 1), chunk_size)])
            y_hat_ = np.concatenate([neigh.predict(_) for _ in chunks(fragment_ions['rt'].values.reshape(-1, 1), chunk_size)])

            delta_ppm_corrected = fragment_ions['delta_ppm'] - y_hat_
            median_off_corrected = np.median(delta_ppm_corrected.values)
            delta_ppm_median_corrected = delta_ppm_corrected - median_off_corrected

            mad_offset = np.median(np.abs(delta_ppm_median_corrected))

            try:
                offset = ms_file_.read(dataset_name = 'corrected_fragment_mzs')
            except KeyError:
                offset = np.zeros(len(mass_list_ms2))

            offset += -y_hat[scan_idx] - median_off_corrected

            delta_ppm_median = fragment_ions['delta_ppm'].median()
            delta_ppm_std = fragment_ions['delta_ppm'].std()

            delta_ppm_median_corrected_median = delta_ppm_median_corrected.median()
            delta_ppm_median_corrected_std = delta_ppm_median_corrected.std()

            logging.info(f'Median offset (std) {delta_ppm_median:.2f} ({delta_ppm_std:.2f}) - after calibration {delta_ppm_median_corrected_median:.2f} ({delta_ppm_median_corrected_std:.2f}) Mad offset {mad_offset:.2f}')

            logging.info('Saving calibration')

            save_fragment_calibration(fragment_ions, delta_ppm_median_corrected, delta_ppm_median_corrected_std, file_name, settings)

            ms_file_.write(
                offset,
                dataset_name="corrected_fragment_mzs",
            )

            ms_file_.write(np.array([delta_ppm_median_corrected_std]), dataset_name="estimated_max_fragment_ppm")
        else:
            logging.info(f'Not enough datapoints {len(fragment_ions)} for fragment calibration. Minimum is set to {calib_n_neighbors}. Skipping fragment calibration.')

# Cell

from typing import Union
import alphapept.io
from .score import score_generic
import os


def calibrate_hdf(
    to_process: tuple, callback=None, parallel=True) -> Union[str,bool]:
    """Wrapper function to get calibrate a hdf file when using the parallel executor.
    The function loads the respective dataframes from the hdf, calls the calibration function and applies the offset.

    Args:
        to_process (tuple): Tuple that contains the file index and the settings dictionary.
        callback ([type], optional): Placeholder for callback (unused).
        parallel (bool, optional): Placeholder for parallel usage (unused).

    Returns:
        Union[str,bool]: Either True as boolean when calibration is successfull or the Error message as string.
    """

    try:
        index, settings = to_process
        file_name = settings['experiment']['file_paths'][index]
        logging.info(f'Recalibrating file {file_name}.')
        base_file_name, ext = os.path.splitext(file_name)
        ms_file = base_file_name+".ms_data.hdf"
        ms_file_ = alphapept.io.MS_Data_File(ms_file, is_overwritable=True)

        features = ms_file_.read(dataset_name='features')

        try:
            psms =  ms_file_.read(dataset_name='first_search')
        except KeyError: #no elements in search
            psms = pd.DataFrame()

        df = None

        if len(psms) > 0 :
            df = score_generic(
                psms,
                fdr_level=settings["search"]["peptide_fdr"],
                plot=False,
                verbose=False,
                **settings["search"]
            )
            logging.info(f'Precursor mass calibration for file {file_name}.')
            corrected_mass, prec_offset_ppm_std, prec_offset_ppm_mad = get_calibration(
                df,
                features,
                file_name,
                settings,
                **settings["calibration"]
            )
            ms_file_.write(
                corrected_mass,
                dataset_name="corrected_mass",
                group_name="features"
            )
        else:

            ms_file_.write(
                features['mass_matched'],
                dataset_name="corrected_mass",
                group_name="features"
            )

            prec_offset_ppm_std = 0

        ms_file_.write(
            prec_offset_ppm_std,
            dataset_name="corrected_mass",
            group_name="features",
            attr_name="estimated_max_precursor_ppm"
        )
        logging.info(f'Precursor calibration of file {ms_file} complete.')


        # Calibration of fragments
        calibrate_fragments_nn(ms_file_, file_name, settings)
        logging.info(f'Fragment calibration of file {ms_file} complete.')



        return True
    except Exception as e:
        logging.error(f'Calibration of file {ms_file} failed. Exception {e}.')
        return f"{e}" #Can't return exception object, cast as string

# Cell

import scipy.stats
import scipy.signal
import scipy.interpolate
import alphapept.fasta

#The following function does not have an own unit test but is run by test_calibrate_fragments.
def get_db_targets(
    db_file_name: str,
    max_ppm: int=100,
    min_distance: float=0.5,
    ms_level: int=2,
) ->np.ndarray:
    """Function to extract database targets for database-calibration.
    Based on the FASTA database it finds masses that occur often. These will be used for calibration.


    Args:
        db_file_name (str): Path to the database.
        max_ppm (int, optional): Maximum distance in ppm between two peaks. Defaults to 100.
        min_distance (float, optional): Minimum distance between two calibration peaks. Defaults to 0.5.
        ms_level (int, optional): MS-Level used for calibration, either precursors (1) or fragmasses (2). Defaults to 2.

    Raises:
        ValueError: When ms_level is not valid.

    Returns:
        np.ndarray: Numpy array with calibration masses.
    """

    if ms_level == 1:
        db_mzs_ = alphapept.fasta.read_database(db_file_name, 'precursors')
    elif ms_level == 2:
        db_mzs_ = alphapept.fasta.read_database(db_file_name, 'fragmasses')
    else:
        raise ValueError(f"{ms_level} is not a valid ms level")
    tmp_result = np.bincount(
        (
            np.log10(
                db_mzs_[
                    np.isfinite(db_mzs_) & (db_mzs_ > 0)
                ].flatten()
            ) * 10**6
        ).astype(np.int64)
    )
    db_mz_distribution = np.zeros_like(tmp_result)
    for i in range(1, max_ppm):
        db_mz_distribution[i:] += tmp_result[:-i]
        db_mz_distribution[:-i] += tmp_result[i:]
    peaks = scipy.signal.find_peaks(db_mz_distribution, distance=max_ppm)[0]
    db_targets = 10 ** (peaks / 10**6)
    db_array = np.zeros(int(db_targets[-1]) + 1, dtype=np.float64)
    last_int_mz = -1
    last_mz = -1
    for mz in db_targets:
        mz_int = int(mz)
        if (mz_int != last_int_mz) & (mz > (last_mz + min_distance)):
            db_array[mz_int] = mz
        else:
            db_array[mz_int] = 0
        last_int_mz = mz_int
        last_mz = mz
    return db_array

# Cell

#The following function does not have an own unit test but is run by test_calibrate_fragments.
def align_run_to_db(
    ms_data_file_name: str,
    db_array: np.ndarray,
    max_ppm_distance: int=1000000,
    rt_step_size:float =0.1,
    plot_ppms: bool=False,
    ms_level: int=2,
) ->np.ndarray:
    """Function align a run to it's theoretical FASTA database.

    Args:
        ms_data_file_name (str): Path to the run.
        db_array (np.ndarray): Numpy array containing the database targets.
        max_ppm_distance (int, optional): Maximum distance in ppm. Defaults to 1000000.
        rt_step_size (float, optional): Stepsize for rt calibration. Defaults to 0.1.
        plot_ppms (bool, optional): Flag to indicate plotting. Defaults to False.
        ms_level (int, optional): ms_level for calibration. Defaults to 2.

    Raises:
        ValueError: When ms_level is not valid.

    Returns:
        np.ndarray: Estimated errors
    """

    ms_data = alphapept.io.MS_Data_File(ms_data_file_name)
    if ms_level == 1:
        mzs = ms_data.read(dataset_name="mass_matched", group_name="features")
        rts = ms_data.read(dataset_name="rt_matched", group_name="features")
    elif ms_level == 2:
        mzs = ms_data.read(dataset_name="Raw/MS2_scans/mass_list_ms2")
        inds = ms_data.read(dataset_name="Raw/MS2_scans/indices_ms2")
        precursor_rts = ms_data.read(dataset_name="Raw/MS2_scans/rt_list_ms2")
        rts = np.repeat(precursor_rts, np.diff(inds))
    else:
        raise ValueError(f"{ms_level} is not a valid ms level")

    selected = mzs.astype(np.int64)
    ds = np.zeros((3, len(selected)))
    if len(db_array) < len(selected) + 1:
        tmp = np.zeros(len(selected) + 1)
        tmp[:len(db_array)] = db_array
        db_array = tmp
    ds[0] = mzs - db_array[selected - 1]
    ds[1] = mzs - db_array[selected]
    ds[2] = mzs - db_array[selected + 1]
    min_ds = np.take_along_axis(
        ds,
        np.expand_dims(np.argmin(np.abs(ds), axis=0), axis=0),
        axis=0
    ).squeeze(axis=0)
    ppm_ds = min_ds / mzs * 10**6

    selected = np.abs(ppm_ds) < max_ppm_distance
    selected &= np.isfinite(rts)
    rt_order = np.argsort(rts)
    rt_order = rt_order[selected[rt_order]]


    ordered_rt = rts[rt_order]
    ordered_ppm = ppm_ds[rt_order]

    rt_idx_break = np.searchsorted(
        ordered_rt,
        np.arange(ordered_rt[0], ordered_rt[-1], rt_step_size),
        "left"
    )
    median_ppms = np.empty(len(rt_idx_break) - 1)
    for i in range(len(median_ppms)):
        median_ppms[i] = np.median(
            ordered_ppm[rt_idx_break[i]: rt_idx_break[i + 1]]
        )

    if plot_ppms:
        import matplotlib.pyplot as plt
        plt.plot(
            rt_step_size + np.arange(
                ordered_rt[0],
                ordered_rt[-1],
                rt_step_size
            )[:-1],
            median_ppms
        )
        plt.show()

    estimated_errors = scipy.interpolate.griddata(
        rt_step_size / 2 + np.arange(
            ordered_rt[0],
            ordered_rt[-1] - 2 * rt_step_size,
            rt_step_size
        ),
        median_ppms,
        rts,
        fill_value=0,
        method="linear",
        rescale=True
    )

    estimated_errors[~np.isfinite(estimated_errors)] = 0

    return estimated_errors

# Cell

def calibrate_fragments(
    db_file_name: str,
    ms_data_file_name: str,
    ms_level: int=2,
    write = True,
    plot_ppms = False,
):
    """Wrapper function to calibrate fragments.
    Calibrated values are saved to corrected_fragment_mzs

    Args:
        db_file_name (str): Path to database
        ms_data_file_name (str): Path to ms_data file
        ms_level (int, optional): MS-level for calibration. Defaults to 2.
        write (bool, optional): Boolean flag for test purposes to avoid writing to testfile. Defaults to True.
        plot_ppms (bool, optional):  Boolean flag to plot the calibration. Defaults to False.
    """

    db_array = get_db_targets(
        db_file_name,
        max_ppm=100,
        min_distance=0.5,
        ms_level=ms_level,
    )
    estimated_errors = align_run_to_db(
        ms_data_file_name,
        db_array=db_array,
        ms_level=ms_level,
        plot_ppms=plot_ppms,
    )

    if write:
        ms_file = alphapept.io.MS_Data_File(ms_data_file_name, is_overwritable=True)
        ms_file.write(
            estimated_errors,
            dataset_name="corrected_fragment_mzs",
        )