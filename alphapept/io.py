# AUTOGENERATED! DO NOT EDIT! File to edit: nbs\02_io.ipynb (unless otherwise specified).

__all__ = ['get_most_abundant', 'calculate_mass', 'M_PROTON', 'load_thermo_raw', 'parse_kwargs_path', 'raw_to_npz',
           'load_bruker_raw', 'check_sanity', 'extract_mzml_info', 'extract_mzxml_info', 'read_mzML', 'read_mzXML',
           'list_to_numpy_f32', 'save_query_as_npz']

# Cell
from tqdm import tqdm
import numpy as np
from numba.typed import List
from numba import njit
from pyteomics import mzml, mzxml
import gzip
import sys
import os


def get_most_abundant(mass, intensity, n_max):
    """
    Returns the n_max most abundant peaks of a spectrum
    """


    if len(mass) < n_max:
        return mass, intensity
    else:
        sortindex = np.argsort(intensity)[::-1][:n_max]
        sortindex.sort()

    return mass[sortindex], intensity[sortindex]


from .constants import mass_dict

M_PROTON = mass_dict['Proton']

@njit
def calculate_mass(mono_mz, charge):
    """
    Calculate the precursor mass from mono mz and charge
    """
    prec_mass = mono_mz * abs(charge) - charge * M_PROTON

    return prec_mass

# Cell
def load_thermo_raw(raw_file, most_abundant, callback=None, **kwargs):
    """
    Load thermo raw file and extract spectra
    """

    from pymsfilereader import MSFileReader
    rawfile = MSFileReader(raw_file)

    spec_indices = np.array(
        range(rawfile.FirstSpectrumNumber, rawfile.LastSpectrumNumber + 1)
    )

    scan_list = []
    rt_list = []
    mass_list = []
    int_list = []
    ms_list = []
    prec_mzs_list = []
    mono_mzs_list = []
    charge_list = []

    for idx, i in enumerate(spec_indices):
        ms_order = rawfile.GetMSOrderForScanNum(i)
        rt = rawfile.RTFromScanNum(i)

        prec_mz = rawfile.GetPrecursorMassForScanNum(i, 2)

        trailer_extra = rawfile.GetTrailerExtraForScanNum(i)

        label_data = rawfile.GetLabelData(i)
        intensity = np.array(label_data[0][1])
        masses = np.array(label_data[0][0])

        mono_mz = trailer_extra["Monoisotopic M/Z"]
        charge = trailer_extra["Charge State"]

        if ms_order == 2:
            masses, intensity = get_most_abundant(masses, intensity, most_abundant)

        scan_list.append(i)
        rt_list.append(rt)
        mass_list.append(np.array(masses))
        int_list.append(np.array(intensity, dtype=np.int64))
        ms_list.append(ms_order)
        prec_mzs_list.append(prec_mz)
        mono_mzs_list.append(mono_mz)
        charge_list.append(charge)

        if callback:
            callback((idx+1)/len(spec_indices))

    scan_list_ms1 = [scan_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    rt_list_ms1 = [rt_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    mass_list_ms1 = [mass_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    int_list_ms1 = [int_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    ms_list_ms1 = [ms_list[i] for i, _ in enumerate(ms_list) if _ == 1]

    scan_list_ms2 = [scan_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    rt_list_ms2 = [rt_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    mass_list_ms2 = [mass_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    int_list_ms2 = [int_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    ms_list_ms2 = [ms_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    mono_mzs2 = [mono_mzs_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    charge2 = [charge_list[i] for i, _ in enumerate(ms_list) if _ == 2]

    prec_mass_list2 = [
        calculate_mass(mono_mzs_list[i], charge_list[i])
        for i, _ in enumerate(ms_list)
        if _ == 2
    ]

    check_sanity(mass_list)

    query_data = {}

    query_data["scan_list_ms1"] = np.array(scan_list_ms1)
    query_data["rt_list_ms1"] = np.array(rt_list_ms1)
    query_data["mass_list_ms1"] = np.array(mass_list_ms1)
    query_data["int_list_ms1"] = np.array(int_list_ms1)
    query_data["ms_list_ms1"] = np.array(ms_list_ms1)

    query_data["scan_list_ms2"] = np.array(scan_list_ms2)
    query_data["rt_list_ms2"] = np.array(rt_list_ms2)
    query_data["mass_list_ms2"] = mass_list_ms2
    query_data["int_list_ms2"] = int_list_ms2
    query_data["ms_list_ms2"] = np.array(ms_list_ms2)
    query_data["prec_mass_list2"] = np.array(prec_mass_list2)
    query_data["mono_mzs2"] = np.array(mono_mzs2)
    query_data["charge2"] = np.array(charge2)

    return query_data


# Cell

def parse_kwargs_path(kwargs, filetype='.raw'):
    """
    Checks the raw_path of the kwargs, replaces it when a list of rawfiles if this is a folder
    """

    path = kwargs["raw_path"]

    if isinstance(path, list):
        return kwargs

    if not os.path.exists(path):
        raise FileNotFoundError('File {} not found.'.format(path))

    if os.path.isdir(path):
        rawfiles = []
        for file in os.listdir(path):
            print(file)
            if file.endswith(filetype.lower()) or file.endswith(filetype.upper()):
                rawfiles.append(os.path.join(path, file))

        print('Found {} rawfiles in folder.'.format(len(rawfiles)))
        kwargs["raw_path"] = rawfiles

    elif os.path.isfile(path):
        kwargs["raw_path"] = path
    else:
        raise('This should never happen.')

    return kwargs

#export
def raw_to_npz(kwargs, callback=None):
    """
    Wrapper function to convert raw to npz
    """
    if not "raw_path" in kwargs.keys():
        raise FileNotFoundError('Raw Path not set.')

    kwargs = parse_kwargs_path(kwargs)
    path = kwargs["raw_path"]

    out_path = []

    raw_file = path
    base, ext = os.path.splitext(raw_file)

    if ext == '.raw':
        query_data = load_thermo_raw(raw_file, callback=partial_progress, **kwargs)
    elif ext == '.d':
        query_data = load_bruker_raw(raw_file, callback=partial_progress, **kwargs)
    else:
        raise NotImplementedError('File extension {} not understood.'.format(ext))

    save_path = base + ".npz"
    save_query_as_npz(save_path, query_data)

    out_path.append(save_path)

    return out_path

# Cell
def load_bruker_raw(raw_file, most_abundant, callback=None, **kwargs):
    """
    Load bruker raw file and extract spectra
    """
    import sqlalchemy as db
    from ext.bruker import timsdata

    tdf = os.path.join(raw_file, 'analysis.tdf')
    engine = db.create_engine('sqlite:///{}'.format(tdf))
    prec_data = pd.read_sql_table('Precursors', engine)
    frame_data = pd.read_sql_table('Frames', engine)
    frame_data = frame_data.set_index('Id')

    from .constants import mass_dict

    tdf = timsdata.TimsData(raw_file)

    M_PROTON = mass_dict['Proton']

    prec_data['Mass'] = prec_data['MonoisotopicMz'].values * prec_data['Charge'].values - prec_data['Charge'].values*M_PROTON

    from .io import list_to_numpy_f32, get_most_abundant

    mass_list_ms2 = []
    int_list_ms2 = []
    scan_list_ms2 = []

    prec_data = prec_data.sort_values(by='Mass', ascending=True)

    precursor_ids = prec_data['Id'].tolist()

    for idx, key in enumerate(precursor_ids):

        ms2_data = tdf.readPasefMsMs([key])
        masses, intensity = ms2_data[key]

        masses, intensity = get_most_abundant(np.array(masses), np.array(intensity), most_abundant)

        mass_list_ms2.append(masses)
        int_list_ms2.append(intensity)
        scan_list_ms2.append(key)

        if callback:
            callback((idx+1)/len(precursor_ids))


    check_sanity(mass_list_ms2)

    query_data = {}

    query_data['prec_mass_list2'] = prec_data['Mass'].values
    query_data['prec_id'] = prec_data['Id'].values
    query_data['mono_mzs2'] = prec_data['MonoisotopicMz'].values
    query_data['rt_list_ms2'] = frame_data.loc[prec_data['Parent'].values]['Time'].values / 60 #convert to minutes
    query_data['scan_list_ms2'] = prec_data['Parent'].values
    query_data['charge2'] = prec_data['Charge'].values
    query_data['mobility'] = tdf.scanNumToOneOverK0(1, prec_data['ScanNumber'].to_list()) #check if its okay to always use first frame
    query_data["mass_list_ms2"] = mass_list_ms2
    query_data["int_list_ms2"] = int_list_ms2
    query_data['bounds'] = np.sum(query_data['mass_list_ms2']>=0,axis=0).astype(np.int64)

    return query_data

# Cell

def check_sanity(mass_list):
    """
    Sanity check for mass list to make sure the masses are sorted
    """

    if not all(
        mass_list[0][i] <= mass_list[0][i + 1] for i in range(len(mass_list[0]) - 1)
    ):
        raise ValueError("Masses are not sorted.")



def extract_mzml_info(input_dict):
    rt = float(input_dict.get('scanList').get('scan')[0].get('scan start time'))  # rt_list_ms1/2
    masses = input_dict.get('m/z array')
    intensities = input_dict.get('intensity array')
    ms_order = input_dict.get('ms level')  # ms_list_ms1/2
    prec_mass = 0
    if ms_order == 2:
        charge = int(
            input_dict.get('precursorList').get('precursor')[0].get('selectedIonList').get('selectedIon')[0].get(
                'charge state'))
        mono_mz = round(
            input_dict.get('precursorList').get('precursor')[0].get('selectedIonList').get('selectedIon')[0].get(
                'selected ion m/z'), 4)
        prec_mass = calculate_mass(mono_mz, charge)
    return rt, masses, intensities, ms_order, prec_mass


def extract_mzxml_info(input_dict):
    rt = float(input_dict.get('retentionTime'))
    masses = input_dict.get('m/z array')
    intensities = input_dict.get('intensity array')
    ms_order = input_dict.get('msLevel')  # ms_list_ms1/2
    prec_mass = 0
    if ms_order == 2:
        charge = int(input_dict.get('precursorMz')[0].get('precursorCharge'))
        mono_mz = round(input_dict.get('precursorMz')[0].get('precursorMz'), 4)
        prec_mass = calculate_mass(mono_mz, charge)
    return rt, masses, intensities, ms_order, prec_mass


def read_mzML(filename, most_abundant):
    """
    Read spectral data from an mzML file and return various lists separately for ms1 and ms2 data.
    """

    try:
        if os.path.splitext(filename)[1] == '.gz':
            reader = mzml.read(gzip.open(filename), use_index=True)
        else:
            reader = mzml.read(filename, use_index=True)
        spec_indices = np.array(range(1, len(reader) + 1))

    except OSError:
        print('Could not open the file. Please, specify the correct path to the file.')
        sys.exit(1)

    scan_list = []
    rt_list = []
    mass_list = []
    int_list = []
    ms_list = []
    prec_mzs_list = []

    print('Start reading mzML file...')
    if reader:
        for i in tqdm(spec_indices):
            spec = next(reader)
            scan_list.append(i)
            rt, masses, intensities, ms_order, prec_mass = extract_mzml_info(spec, min_charge, max_charge)
            if ms_order == 2:
                masses, intensities = get_most_abundant(masses, intensities, most_abundant)
            rt_list.append(rt)
            mass_list.append(masses)
            int_list.append(intensities)
            ms_list.append(ms_order)
            prec_mzs_list.append(prec_mass)

    check_sanity(mass_list)

    scan_list_ms1 = [scan_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    rt_list_ms1 = [rt_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    mass_list_ms1 = [mass_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    int_list_ms1 = [int_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    ms_list_ms1 = [ms_list[i] for i, _ in enumerate(ms_list) if _ == 1]

    scan_list_ms2 = [scan_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    rt_list_ms2 = [rt_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    mass_list_ms2 = [mass_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    int_list_ms2 = [int_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    ms_list_ms2 = [ms_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    prec_mass_list2 = [prec_mzs_list[i] for i, _ in enumerate(ms_list) if _ == 2]

    query_data = {}

    query_data["scan_list_ms1"] = np.array(scan_list_ms1)
    query_data["rt_list_ms1"] = np.array(rt_list_ms1)
    query_data["mass_list_ms1"] = np.array(mass_list_ms1)
    query_data["int_list_ms1"] = np.array(int_list_ms1)
    query_data["ms_list_ms1"] = np.array(ms_list_ms1)

    query_data["scan_list_ms2"] = np.array(scan_list_ms2)
    query_data["rt_list_ms2"] = np.array(rt_list_ms2)
    query_data["mass_list_ms2"] = mass_list_ms2
    query_data["int_list_ms2"] = int_list_ms2
    query_data["ms_list_ms2"] = np.array(ms_list_ms2)
    query_data["prec_mass_list2"] = np.array(prec_mass_list2)
    query_data["mono_mzs2"] = np.array(mono_mzs2)
    query_data["charge2"] = np.array(charge2)

    return query_data


def read_mzXML(filename, most_abundant):
    """
    Read spectral data from an mzXML file and return various lists separately for ms1 and ms2 data.
    """

    try:
        if os.path.splitext(filename)[1] == '.gz':
            reader = mzxml.read(gzip.open(filename), use_index=True)
        else:
            reader = mzxml.read(filename, use_index=True)
        spec_indices = np.array(range(1, len(reader) + 1))

    except OSError:
        print('Could not open the file. Please, specify the correct path to the file.')
        sys.exit(1)

    scan_list = []
    rt_list = []
    mass_list = []
    int_list = []
    ms_list = []
    prec_mzs_list = []

    print('Start reading mzXML file...')
    if reader:
        for i in tqdm(spec_indices):
            spec = next(reader)
            scan_list.append(i)
            rt, masses, intensities, ms_order, prec_mass = extract_mzxml_info(spec, min_charge, max_charge)
            if ms_order == 2:
                masses, intensities = get_most_abundant(masses, intensities, most_abundant)
            rt_list.append(rt)
            mass_list.append(masses)
            int_list.append(intensities)
            ms_list.append(ms_order)
            prec_mzs_list.append(prec_mass)

    check_sanity(mass_list)

    scan_list_ms1 = [scan_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    rt_list_ms1 = [rt_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    mass_list_ms1 = [mass_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    int_list_ms1 = [int_list[i] for i, _ in enumerate(ms_list) if _ == 1]
    ms_list_ms1 = [ms_list[i] for i, _ in enumerate(ms_list) if _ == 1]

    scan_list_ms2 = [scan_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    rt_list_ms2 = [rt_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    mass_list_ms2 = [mass_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    int_list_ms2 = [int_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    ms_list_ms2 = [ms_list[i] for i, _ in enumerate(ms_list) if _ == 2]
    prec_mass_list2 = [prec_mzs_list[i] for i, _ in enumerate(ms_list) if _ == 2]

    check_sanity(mass_list)

    query_data = {}

    query_data["scan_list_ms1"] = np.array(scan_list_ms1)
    query_data["rt_list_ms1"] = np.array(rt_list_ms1)
    query_data["mass_list_ms1"] = np.array(mass_list_ms1)
    query_data["int_list_ms1"] = np.array(int_list_ms1)
    query_data["ms_list_ms1"] = np.array(ms_list_ms1)

    query_data["scan_list_ms2"] = np.array(scan_list_ms2)
    query_data["rt_list_ms2"] = np.array(rt_list_ms2)
    query_data["mass_list_ms2"] = mass_list_ms2
    query_data["int_list_ms2"] = int_list_ms2
    query_data["ms_list_ms2"] = np.array(ms_list_ms2)
    query_data["prec_mass_list2"] = np.array(prec_mass_list2)
    query_data["mono_mzs2"] = np.array(mono_mzs2)
    query_data["charge2"] = np.array(charge2)

    return query_data

# Cell
def list_to_numpy_f32(long_list):
    """
    Function to convert a list to float32 array
    """
    np_array = (
        np.zeros(
            [len(max(long_list, key=lambda x: len(x))), len(long_list)],
            dtype=np.float32,
        )
        - 1
    )
    for i, j in enumerate(long_list):
        np_array[0 : len(j), i] = j

    return np_array


def save_query_as_npz(raw_file_npz, query_data):
    """
    Saves query_data as npz
    """

    to_save = {}

    for key in query_data.keys():
        if key in ['mass_list_ms2','int_list_ms2']:
            to_save[key] = list_to_numpy_f32(query_data[key])
        else:
            to_save[key] = query_data[key]

    to_save["bounds"] = np.sum(to_save['mass_list_ms2']>=0,axis=0).astype(np.int64)

    np.savez(raw_file_npz, **to_save)

    return raw_file_npz