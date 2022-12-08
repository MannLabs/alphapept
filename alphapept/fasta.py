# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/03_fasta.ipynb (unless otherwise specified).

__all__ = ['get_missed_cleavages', 'cleave_sequence', 'count_missed_cleavages', 'count_internal_cleavages', 'parse',
           'list_to_numba', 'get_decoy_sequence', 'swap_KR', 'swap_AL', 'get_decoys', 'add_decoy_tag', 'add_fixed_mods',
           'add_variable_mod', 'get_isoforms', 'add_variable_mods', 'add_fixed_mod_terminal', 'add_fixed_mods_terminal',
           'add_variable_mods_terminal', 'get_unique_peptides', 'generate_peptides', 'check_peptide', 'get_precmass',
           'get_fragmass', 'get_frag_dict', 'get_spectrum', 'get_spectra', 'read_fasta_file', 'read_fasta_file_entries',
           'check_sequence', 'add_to_pept_dict', 'merge_pept_dicts', 'generate_fasta_list', 'generate_database',
           'generate_spectra', 'block_idx', 'blocks', 'digest_fasta_block', 'generate_database_parallel', 'mass_dict',
           'pept_dict_from_search', 'save_database', 'read_database']

# Cell
from alphapept import constants
import re

def get_missed_cleavages(sequences:list, n_missed_cleavages:int) -> list:
    """
    Combine cleaved sequences to get sequences with missed cleavages
    Args:
        seqeuences (list of str): the list of cleaved sequences, no missed cleavages are there.
        n_missed_cleavages (int): the number of miss cleavage sites.
    Returns:
        list (of str): the sequences with missed cleavages.
    """
    missed = []
    for k in range(len(sequences)-n_missed_cleavages):
        missed.append(''.join(sequences[k-1:k+n_missed_cleavages]))

    return missed


def cleave_sequence(
    sequence:str="",
    n_missed_cleavages:int=0,
    protease:str="trypsin",
    pep_length_min:int=6,
    pep_length_max:int=65,
    **kwargs
)->list:
    """
    Cleave a sequence with a given protease. Filters to have a minimum and maximum length.
    Args:
        sequence (str): the given (protein) sequence.
        n_missed_cleavages (int): the number of max missed cleavages.
        protease (str): the protease/enzyme name, the regular expression can be found in alphapept.constants.protease_dict.
        pep_length_min (int): min peptide length.
        pep_length_max (int): max peptide length.
    Returns:
        list (of str): cleaved peptide sequences with missed cleavages.
    """

    proteases = constants.protease_dict
    pattern = proteases[protease]

    p = re.compile(pattern)

    cutpos = [m.start()+1 for m in p.finditer(sequence)]
    cutpos.insert(0,0)
    cutpos.append(len(sequence))

    base_sequences = [sequence[cutpos[i]:cutpos[i+1]] for i in range(len(cutpos)-1)]

    sequences = base_sequences.copy()

    for i in range(1, n_missed_cleavages+1):
        sequences.extend(get_missed_cleavages(base_sequences, i))

    sequences = [_ for _ in sequences if len(_)>=pep_length_min and len(_)<=pep_length_max]

    return sequences

# Cell
import re
from alphapept import constants

def count_missed_cleavages(sequence:str="", protease:str="trypsin", **kwargs) -> int:
    """
    Counts the number of missed cleavages for a given sequence and protease
    Args:
        sequence (str): the given (peptide) sequence.
        protease (str): the protease/enzyme name, the regular expression can be found in alphapept.constants.protease_dict.
    Returns:
        int: the number of miss cleavages
    """
    proteases = constants.protease_dict
    protease = proteases[protease]
    p = re.compile(protease)
    n_missed = len(p.findall(sequence))
    return n_missed

def count_internal_cleavages(sequence:str="", protease:str="trypsin", **kwargs) -> int:
    """
    Counts the number of internal cleavage sites for a given sequence and protease
    Args:
        sequence (str): the given (peptide) sequence.
        protease (str): the protease/enzyme name, the regular expression can be found in alphapept.constants.protease_dict.
    Returns:
        int (0 or 1): if the sequence is from internal cleavage.
    """
    proteases = constants.protease_dict
    protease = proteases[protease]
    match = re.search(protease,sequence[-1]+'_')
    if match:
        n_internal = 0
    else:
        n_internal = 1
    return n_internal

# Cell
from numba import njit
from numba.typed import List

@njit
def parse(peptide:str)->List:
    """
    Parser to parse peptide strings
    Args:
        peptide (str): modified peptide sequence.
    Return:
        List (numba.typed.List): a list of animo acids and modified amono acids
    """
    if "_" in peptide:
        peptide = peptide.split("_")[0]
    parsed = List()
    string = ""

    for i in peptide:
        string += i
        if i.isupper():
            parsed.append(string)
            string = ""

    return parsed

def list_to_numba(a_list) -> List:
    """
    Convert Python list to numba.typed.List
    Args:
        a_list (list): Python list.
    Return:
        List (numba.typed.List): Numba typed list.
    """
    numba_list = List()

    for element in a_list:
        numba_list.append(element)

    return numba_list

# Cell
@njit
def get_decoy_sequence(peptide:str, pseudo_reverse:bool=False, AL_swap:bool=False, KR_swap:bool = False)->str:
    """
    Reverses a sequence and adds the '_decoy' tag.
    Args:
        peptide (str): modified peptide to be reversed.
        pseudo_reverse (bool): If True, reverse the peptide bug keep the C-terminal amino acid; otherwise reverse the whole peptide. (Default: False)
        AL_swap (bool): replace A with L, and vice versa. (Default: False)
        KR_swap (bool): replace K with R at the C-terminal, and vice versa. (Default: False)
    Returns:
        str: reversed peptide ending with the '_decoy' tag.
    """
    pep = parse(peptide)
    if pseudo_reverse:
        rev_pep = pep[:-1][::-1]
        rev_pep.append(pep[-1])
    else:
        rev_pep = pep[::-1]

    if AL_swap:
        rev_pep = swap_AL(rev_pep)

    if KR_swap:
        rev_pep = swap_KR(rev_pep)

    rev_pep = "".join(rev_pep)

    return rev_pep


@njit
def swap_KR(peptide:str)->str:
    """
    Swaps a terminal K or R. Note: Only if AA is not modified.

    Args:
        peptide (str): peptide.

    Returns:
        str: peptide with swapped KRs.
    """
    if peptide[-1] == 'K':
        peptide[-1] = 'R'
    elif peptide[-1] == 'R':
        peptide[-1] = 'K'

    return peptide


@njit
def swap_AL(peptide:str)->str:
    """
    Swaps a A with L. Note: Only if AA is not modified.
    Args:
        peptide (str): peptide.

    Returns:
        str: peptide with swapped ALs.
    """
    i = 0
    while i < len(range(len(peptide) - 1)):
        if peptide[i] == "A":
            peptide[i] = peptide[i + 1]
            peptide[i + 1] = "A"
            i += 1
        elif peptide[i] == "L":
            peptide[i] = peptide[i + 1]
            peptide[i + 1] = "L"
            i += 1
        i += 1

    return peptide

def get_decoys(peptide_list, pseudo_reverse=False, AL_swap=False, KR_swap = False, **kwargs)->list:
    """
    Wrapper to get decoys for lists of peptides
    Args:
        peptide_list (list): the list of peptides to be reversed.
        pseudo_reverse (bool): If True, reverse the peptide bug keep the C-terminal amino acid; otherwise reverse the whole peptide. (Default: False)
        AL_swap (bool): replace A with L, and vice versa. (Default: False)
        KR_swap (bool): replace K with R at the C-terminal, and vice versa. (Default: False)
    Returns:
        list (of str): a list of decoy peptides
    """
    decoys = []
    decoys.extend([get_decoy_sequence(peptide, pseudo_reverse, AL_swap, KR_swap) for peptide in peptide_list])
    return decoys

def add_decoy_tag(peptides):
    """
    Adds a '_decoy' tag to a list of peptides
    """
    return [peptide + "_decoy" for peptide in peptides]

# Cell
def add_fixed_mods(seqs:list, mods_fixed:list, **kwargs)->list:
    """
    Adds fixed modifications to sequences.
    Args:
        seqs (list of str): sequences to add fixed modifications
        mods_fixed (list of str): the string list of fixed modifications. Each modification string must be in lower case, except for that the last letter must be the modified amino acid (e.g. oxidation on M should be oxM).
    Returns:
        list (of str): the list of the modified sequences. 'ABCDEF' with fixed mod 'cC' will be 'ABcCDEF'.
    """
    if not mods_fixed:
        return seqs
    else:
        for mod_aa in mods_fixed:
            seqs = [seq.replace(mod_aa[-1], mod_aa) for seq in seqs]
        return seqs

# Cell
def add_variable_mod(peps:list, mods_variable_dict:dict)->list:
    """
    Function to add variable modification to a list of peptides.
    Args:
        peps (list): List of peptides.
        mods_variable_dict (dict): Dicitionary with modifications. The key is AA, and value is the modified form (e.g. oxM).
    Returns:
        list : the list of peptide forms for the given peptide.
    """
    peptides = []
    for pep_ in peps:
        pep, min_idx = pep_
        for mod in mods_variable_dict:
            for i in range(len(pep)):
                if i >= min_idx:
                    c = pep[i]
                    if c == mod:
                        peptides.append((pep[:i]+[mods_variable_dict[c]]+pep[i+1:], i))
    return peptides


def get_isoforms(mods_variable_dict:dict, peptide:str, isoforms_max:int, n_modifications_max:int=None)->list:
    """
    Function to generate modified forms (with variable modifications) for a given peptide - returns a list of modified forms.
    The original sequence is included in the list
    Args:
        mods_variable_dict (dict): Dicitionary with modifications. The key is AA, and value is the modified form (e.g. oxM).
        peptide (str): the peptide sequence to generate modified forms.
        isoforms_max (int): max number of modified forms to generate per peptide.
        n_modifications_max (int, optional): max number of variable modifications per peptide.
    Returns:
        list (of str): the list of peptide forms for the given peptide
    """
    pep = list(parse(peptide))

    peptides = [pep]
    new_peps = [(pep, 0)]

    iteration = 0
    while len(peptides) < isoforms_max:


        if n_modifications_max:
            if iteration >= n_modifications_max:
                break

        new_peps = add_variable_mod(new_peps, mods_variable_dict)

        if len(new_peps) == 0:
            break
        if len(new_peps) > 1:
            if new_peps[0][0] == new_peps[1][0]:
                new_peps = new_peps[0:1]

        for _ in new_peps:
            if len(peptides) < isoforms_max:
                peptides.append(_[0])

        iteration +=1



    peptides = [''.join(_) for _ in peptides]

    return peptides

# Cell
from itertools import chain

def add_variable_mods(peptide_list:list, mods_variable:list, isoforms_max:int, n_modifications_max:int, **kwargs)->list:
    """
    Add variable modifications to the peptide list
    Args:
        peptide_list (list of str): peptide list.
        mods_variable (list of str): modification list.
        isoforms_max (int): max number of modified forms per peptide sequence.
        n_modifications_max (int): max number of variable modifications per peptide.
    Returns:
        list (of str): list of modified sequences for the given peptide list.
    """

    #the peptide_list originates from one peptide already -> limit isoforms here

    max_ = isoforms_max - len(peptide_list) + 1

    if max_ < 0:
        max_ = 0

    if not mods_variable:
        return peptide_list
    else:
        mods_variable_r = {}
        for _ in mods_variable:
            mods_variable_r[_[-1]] = _

        peptide_list = [get_isoforms(mods_variable_r, peptide, max_, n_modifications_max) for peptide in peptide_list]
        return list(chain.from_iterable(peptide_list))

# Cell
def add_fixed_mod_terminal(peptides:list, mod:str)->list:
    """
    Adds fixed terminal modifications
    Args:
        peptides (list of str): peptide list.
        mod (str): n-term mod contains '<^' (e.g. a<^ for Acetyl@N-term); c-term mod contains '>^'.
    Raises:
        "Invalid fixed terminal modification 'mod name'" for the given mod.
    Returns:
        list (of str): list of peptides with modification added.
    """
    # < for left side (N-Term), > for right side (C-Term)
    if "<^" in mod: #Any n-term, e.g. a<^
        peptides = [mod[:-2] + peptide for peptide in peptides]
    elif ">^" in mod: #Any c-term, e.g. a>^
        peptides = [peptide[:-1] + mod[:-2] + peptide[-1] for peptide in peptides]
    elif "<" in mod: #only if specific AA, e.g. ox<C
        peptides = [peptide[0].replace(mod[-1], mod[:-2]+mod[-1]) + peptide[1:] for peptide in peptides]
    elif ">" in mod:
        peptides = [peptide[:-1] + peptide[-1].replace(mod[-1], mod[:-2]+mod[-1]) for peptide in peptides]
    else:
        # This should not happen
        raise ("Invalid fixed terminal modification {}.".format(mod))
    return peptides

def add_fixed_mods_terminal(peptides:list, mods_fixed_terminal:list, **kwargs)->list:
    """
    Wrapper to add fixed mods on sequences and lists of mods
    Args:
        peptides (list of str): peptide list.
        mods_fixed_terminal (list of str): list of fixed terminal mods.
    Raises:
        "Invalid fixed terminal modification {mod}" exception for the given mod.
    Returns:
        list (of str): list of peptides with modification added.
    """
    if mods_fixed_terminal == []:
        return peptides
    else:
        # < for left side (N-Term), > for right side (C-Term)
        for key in mods_fixed_terminal:
            peptides = add_fixed_mod_terminal(peptides, key)
        return peptides

# Cell
def add_variable_mods_terminal(peptides:list, mods_variable_terminal:list, **kwargs)->list:
    """
    Function to add variable terminal modifications.
    Args:
        peptides (list of str): peptide list.
        mods_variable_terminal (list of str): list of variable terminal mods.
    Returns:
        list (of str): list of peptides with modification added.
    """
    if not mods_variable_terminal:
        return peptides
    else:
        new_peptides_n = peptides.copy()

        for key in mods_variable_terminal:
            if "<" in key:
                # Only allow one variable mod on one end
                new_peptides_n.extend(
                    add_fixed_mod_terminal(peptides, key)
                )
        new_peptides_n = get_unique_peptides(new_peptides_n)
        # N complete, let's go for c-terminal
        new_peptides_c = new_peptides_n
        for key in mods_variable_terminal:
            if ">" in key:
                # Only allow one variable mod on one end
                new_peptides_c.extend(
                    add_fixed_mod_terminal(new_peptides_n, key)
                )

        return get_unique_peptides(new_peptides_c)

def get_unique_peptides(peptides:list) -> list:
    """
    Function to return unique elements from list.
    Args:
        peptides (list of str): peptide list.
    Returns:
        list (of str): list of peptides (unique).
    """
    return list(set(peptides))

# Cell
def generate_peptides(peptide:str, **kwargs)->list:
    """
    Wrapper to get modified peptides (fixed and variable mods) from a peptide.

    Args:
        peptide (str): the given peptide sequence.
    Returns:
        list (of str): all modified peptides.

    TODO:
        There can be some edge-cases which are not defined yet.
        Example:
        Setting the same fixed modification - once for all peptides and once for only terminal for the protein.
        The modification will then be applied twice.
    """
    mod_peptide = add_fixed_mods_terminal([peptide], kwargs['mods_fixed_terminal_prot'])
    mod_peptide = add_variable_mods_terminal(mod_peptide, kwargs['mods_variable_terminal_prot'])

    peptides = []
    [peptides.extend(cleave_sequence(_, **kwargs)) for _ in mod_peptide]

    peptides = [_ for _ in peptides if check_peptide(_, constants.AAs)]

    isoforms_max = kwargs['isoforms_max']

    all_peptides = []
    for peptide in peptides: #1 per, limit the number of isoforms

        #Regular peptides
        mod_peptides = add_fixed_mods([peptide], **kwargs)
        mod_peptides = add_fixed_mods_terminal(mod_peptides, **kwargs)
        mod_peptides = add_variable_mods_terminal(mod_peptides, **kwargs)

        kwargs['isoforms_max'] = isoforms_max - len(mod_peptides)
        mod_peptides = add_variable_mods(mod_peptides, **kwargs)

        all_peptides.extend(mod_peptides)

        #Decoys:
        decoy_peptides = get_decoys([peptide], **kwargs)

        mod_peptides_decoy = add_fixed_mods(decoy_peptides, **kwargs)
        mod_peptides_decoy = add_fixed_mods_terminal(mod_peptides_decoy, **kwargs)
        mod_peptides_decoy = add_variable_mods_terminal(mod_peptides_decoy, **kwargs)

        kwargs['isoforms_max'] = isoforms_max - len(mod_peptides_decoy)

        mod_peptides_decoy = add_variable_mods(mod_peptides_decoy, **kwargs)

        mod_peptides_decoy = add_decoy_tag(mod_peptides_decoy)

        all_peptides.extend(mod_peptides_decoy)

    return all_peptides

def check_peptide(peptide:str, AAs:set)->bool:
    """
    Check if the peptide contains non-AA letters.
    Args:
        peptide (str): peptide sequence.
        AAs (set): the set of legal amino acids. See alphapept.constants.AAs
    Returns:
        bool: True if all letters in the peptide is the subset of AAs, otherwise False
    """
    if set([_ for _ in peptide if _.isupper()]).issubset(AAs):
        return True
    else:
        return False

# Cell
from numba import njit
from numba.typed import List
import numpy as np
import numba

@njit
def get_precmass(parsed_pep:list, mass_dict:numba.typed.Dict)->float:
    """
    Calculate the mass of the neutral precursor
    Args:
        parsed_pep (list or numba.typed.List of str): the list of amino acids and modified amono acids.
        mass_dict (numba.typed.Dict): key is the amino acid or the modified amino acid, and the value is the mass.
    Returns:
        float: the peptide neutral mass.
    """
    tmass = mass_dict["H2O"]
    for _ in parsed_pep:
        tmass += mass_dict[_]

    return tmass

# Cell
import numba

@njit
def get_fragmass(parsed_pep:list, mass_dict:numba.typed.Dict)->tuple:
    """
    Calculate the masses of the fragment ions
    Args:
        parsed_pep (numba.typed.List of str): the list of amino acids and modified amono acids.
        mass_dict (numba.typed.Dict): key is the amino acid or the modified amino acid, and the value is the mass.
    Returns:
        Tuple[np.ndarray(np.float64), np.ndarray(np.int8)]: the fragment masses and the fragment types (represented as np.int8).
        For a fragment type, positive value means the b-ion, the value indicates the position (b1, b2, b3...); the negative value means
        the y-ion, the absolute value indicates the position (y1, y2, ...).
    """
    n_frags = (len(parsed_pep) - 1) * 2

    frag_masses = np.zeros(n_frags, dtype=np.float64)
    frag_type = np.zeros(n_frags, dtype=np.int8)

    # b-ions > 0
    n_frag = 0

    frag_m = mass_dict["Proton"]
    for idx, _ in enumerate(parsed_pep[:-1]):
        frag_m += mass_dict[_]
        frag_masses[n_frag] = frag_m
        frag_type[n_frag] = (idx+1)
        n_frag += 1

    # y-ions < 0
    frag_m = mass_dict["Proton"] + mass_dict["H2O"]
    for idx, _ in enumerate(parsed_pep[::-1][:-1]):
        frag_m += mass_dict[_]
        frag_masses[n_frag] = frag_m
        frag_type[n_frag] = -(idx+1)
        n_frag += 1

    return frag_masses, frag_type

# Cell
def get_frag_dict(parsed_pep:list, mass_dict:dict)->dict:
    """
    Calculate the masses of the fragment ions
    Args:
        parsed_pep (list or numba.typed.List of str): the list of amino acids and modified amono acids.
        mass_dict (numba.typed.Dict): key is the amino acid or the modified amino acid, and the value is the mass.
    Returns:
        dict{str:float}: key is the fragment type (b1, b2, ..., y1, y2, ...), value is fragment mass.
    """
    frag_dict = {}
    frag_masses, frag_type = get_fragmass(parsed_pep, mass_dict)

    for idx, _ in enumerate(frag_masses):

        cnt = frag_type[idx]
        if cnt > 0:
            identifier = 'b'
        else:
            identifier = 'y'
            cnt = -cnt
        frag_dict[identifier+str(cnt)] = _

    return frag_dict

# Cell
@njit
def get_spectrum(peptide:str, mass_dict:numba.typed.Dict)->tuple:
    """
    Get neutral peptide mass, fragment masses and fragment types for a peptide
    Args:
        peptide (str): the (modified) peptide.
        mass_dict (numba.typed.Dict): key is the amino acid or modified amino acid, and the value is the mass.
    Returns:
        Tuple[float, str, np.ndarray(np.float64), np.ndarray(np.int8)]: (peptide mass, peptide, fragment masses, fragment_types), for fragment types, see get_fragmass.
    """
    parsed_peptide = parse(peptide)

    fragmasses, fragtypes = get_fragmass(parsed_peptide, mass_dict)
    sortindex = np.argsort(fragmasses)
    fragmasses = fragmasses[sortindex]
    fragtypes = fragtypes[sortindex]

    precmass = get_precmass(parsed_peptide, mass_dict)

    return (precmass, peptide, fragmasses, fragtypes)

@njit
def get_spectra(peptides:numba.typed.List, mass_dict:numba.typed.Dict)->List:
    """
    Get neutral peptide mass, fragment masses and fragment types for a list of peptides
    Args:
        peptides (list of str): the (modified) peptide list.
        mass_dict (numba.typed.Dict): key is the amino acid or modified amino acid, and the value is the mass.
    Raises:
        Unknown exception and pass.
    Returns:
        list of Tuple[float, str, np.ndarray(np.float64), np.ndarray(np.int8)]: See get_spectrum.
    """
    spectra = List()

    for i in range(len(peptides)):
        try:
            spectra.append(get_spectrum(peptides[i], mass_dict))
        except Exception: #TODO: This is to fix edge cases when having multiple modifications on the same AA.
            pass

    return spectra

# Cell
from Bio import SeqIO
import os
from glob import glob
import logging

def read_fasta_file(fasta_filename:str=""):
    """
    Read a FASTA file line by line
    Args:
        fasta_filename (str): fasta.
    Yields:
        dict {id:str, name:str, description:str, sequence:str}: protein information.
    """
    with open(fasta_filename, "rt") as handle:
        iterator = SeqIO.parse(handle, "fasta")
        while iterator:
            try:
                record = next(iterator)
                parts = record.id.split("|")  # pipe char
                if len(parts) > 1:
                    id = parts[1]
                else:
                    id = record.name
                sequence = str(record.seq)
                entry = {
                    "id": id,
                    "name": record.name,
                    "description": record.description,
                    "sequence": sequence,
                }

                yield entry
            except StopIteration:
                break


def read_fasta_file_entries(fasta_filename=""):
    """
    Function to count entries in fasta file
    Args:
        fasta_filename (str): fasta.
    Returns:
        int: number of entries.
    """
    with open(fasta_filename, "rt") as handle:
        iterator = SeqIO.parse(handle, "fasta")
        count = 0
        while iterator:
            try:
                record = next(iterator)
                count+=1
            except StopIteration:
                break

        return count


def check_sequence(element:dict, AAs:set, verbose:bool = False)->bool:
    """
    Checks wheter a sequence from a FASTA entry contains valid AAs
    Args:
        element (dict): fasta entry of the protein information.
        AAs (set): a set of amino acid letters.
        verbose (bool): logging the invalid amino acids.
    Returns:
        bool: False if the protein sequence contains non-AA letters, otherwise True.
    """
    if not set(element['sequence']).issubset(AAs):
        unknown = set(element['sequence']) - set(AAs)
        if verbose:
            logging.error(f'This FASTA entry contains unknown AAs {unknown} - Peptides with unknown AAs will be skipped: \n {element}\n')
        return False
    else:
        return True



# Cell
def add_to_pept_dict(pept_dict:dict, new_peptides:list, i:int)->tuple:
    """
    Add peptides to the peptide dictionary
    Args:
        pept_dict (dict): the key is peptide sequence, and the value is protein id list indicating where the peptide is from.
        new_peptides (list): the list of peptides to be added to pept_dict.
        i (int): the protein id where new_peptides are from.
    Returns:
        dict: same as the pept_dict in the arguments.
        list (of str): the peptides from new_peptides that not in the pept_dict.
    """
    added_peptides = List()
    for peptide in new_peptides:
        if peptide in pept_dict:
            if i not in pept_dict[peptide]:
                pept_dict[peptide].append(i)
        else:
            pept_dict[peptide] = [i]
            added_peptides.append(peptide)

    return pept_dict, added_peptides

# Cell

def merge_pept_dicts(list_of_pept_dicts:list)->dict:
    """
    Merge a list of peptide dict into a single dict.
    Args:
        list_of_pept_dicts (list of dict): the key of the pept_dict is peptide sequence, and the value is protein id list indicating where the peptide is from.
    Returns:
        dict: the key is peptide sequence, and the value is protein id list indicating where the peptide is from.
    """
    if len(list_of_pept_dicts) == 0:
        raise ValueError('Need to pass at least 1 element.')

    new_pept_dict = list_of_pept_dicts[0]

    for pept_dict in list_of_pept_dicts[1:]:

        for key in pept_dict.keys():
            if key in new_pept_dict:
                for element in pept_dict[key]:
                    new_pept_dict[key].append(element)
            else:
                new_pept_dict[key] = pept_dict[key]

    return new_pept_dict

# Cell
from collections import OrderedDict

def generate_fasta_list(fasta_paths:list, callback = None, **kwargs)->tuple:
    """
    Function to generate a database from a fasta file
    Args:
        fasta_paths (str or list of str): fasta path or a list of fasta paths.
        callback (function, optional): callback function.
    Returns:
        fasta_list (list of dict): list of protein entry dict {id:str, name:str, description:str, sequence:str}.
        fasta_dict (dict{int:dict}): the key is the protein id, the value is the protein entry dict.
    """
    fasta_list = []

    fasta_dict = OrderedDict()

    fasta_index = 0

    if type(fasta_paths) is str:
        fasta_paths = [fasta_paths]
        n_fastas = 1

    elif type(fasta_paths) is list:
        n_fastas = len(fasta_paths)

    for f_id, fasta_file in enumerate(fasta_paths):
        n_entries = read_fasta_file_entries(fasta_file)

        fasta_generator = read_fasta_file(fasta_file)

        for element in fasta_generator:
            check_sequence(element, constants.AAs)
            fasta_list.append(element)
            fasta_dict[fasta_index] = element
            fasta_index += 1


    return fasta_list, fasta_dict



# Cell

def generate_database(mass_dict:dict, fasta_paths:list, callback = None, **kwargs)->tuple:
    """
    Function to generate a database from a fasta file
    Args:
        mass_dict (dict): not used, will be removed in the future.
        fasta_paths (str or list of str): fasta path or a list of fasta paths.
        callback (function, optional): callback function.
    Returns:
        to_add (list of str): non-redundant (modified) peptides to be added.
        pept_dict (dict{str:list of int}): the key is peptide sequence, and the value is protein id list indicating where the peptide is from.
        fasta_dict (dict{int:dict}): the key is the protein id, the value is the protein entry dict {id:str, name:str, description:str, sequence:str}.
    """
    to_add = List()
    fasta_dict = OrderedDict()
    fasta_index = 0

    pept_dict = {}

    if type(fasta_paths) is str:
        fasta_paths = [fasta_paths]
        n_fastas = 1

    elif type(fasta_paths) is list:
        n_fastas = len(fasta_paths)

    for f_id, fasta_file in enumerate(fasta_paths):
        n_entries = read_fasta_file_entries(fasta_file)

        fasta_generator = read_fasta_file(fasta_file)

        for element in fasta_generator:

            fasta_dict[fasta_index] = element
            mod_peptides = generate_peptides(element["sequence"], **kwargs)
            pept_dict, added_seqs = add_to_pept_dict(pept_dict, mod_peptides, fasta_index)
            if len(added_seqs) > 0:
                to_add.extend(added_seqs)

            fasta_index += 1

            if callback:
                callback(fasta_index/n_entries/n_fastas+f_id)

    return to_add, pept_dict, fasta_dict

# Cell

def generate_spectra(to_add:list, mass_dict:dict, callback = None)->list:
    """
    Function to generate spectra list database from a fasta file
    Args:
        to_add (list):
        mass_dict (dict{str:float}): amino acid mass dict.
        callback (function, optional): callback function. (Default: None)
    Returns:
        list (of tuple): list of (peptide mass, peptide, fragment masses, fragment_types), see get_fragmass.
    """

    if len(to_add) > 0:

        if callback: #Chunk the spectra to get a progress_bar
            spectra = []

            stepsize = int(np.ceil(len(to_add)/1000))

            for i in range(0, len(to_add), stepsize):
                sub = to_add[i:i + stepsize]
                spectra.extend(get_spectra(sub, mass_dict))
                callback((i+1)/len(to_add))

        else:
            spectra = get_spectra(to_add, mass_dict)
    else:
        raise ValueError("No spectra to generate.")

    return spectra

# Cell
from typing import Generator

def block_idx(len_list:int, block_size:int = 1000)->list:
    """
    Helper function to split length into blocks
    Args:
        len_list (int): list length.
        block_size (int, optional, default 1000): size per block.
    Returns:
        list[(int, int)]: list of (start, end) positions of blocks.
    """
    blocks = []
    start = 0
    end = 0

    while end <= len_list:
        end += block_size
        blocks.append((start, end))
        start = end

    return blocks

def blocks(l:int, n:int)->Generator[list, None, None]:
    """
    Helper function to create blocks from a given list
    Args:
        l (list): the list
        n (int): size per block
    Returns:
        Generator: List with splitted elements
    """
    n = max(1, n)
    return (l[i:i+n] for i in range(0, len(l), n))

# Cell

from multiprocessing import Pool
from alphapept import constants
mass_dict = constants.mass_dict

#This function is a wrapper function and to be tested by the integration test
def digest_fasta_block(to_process:tuple)-> (list, dict):
    """
    Digest and create spectra for a whole fasta_block for multiprocessing. See generate_database_parallel.
    """

    fasta_index, fasta_block, settings = to_process

    to_add = List()

    f_index = 0

    pept_dict = {}
    for element in fasta_block:
        sequence = element["sequence"]
        mod_peptides = generate_peptides(sequence, **settings['fasta'])
        pept_dict, added_peptides = add_to_pept_dict(pept_dict, mod_peptides, fasta_index+f_index)
        if len(added_peptides) > 0:
            to_add.extend(added_peptides)
        f_index += 1

    spectra = []
    if len(to_add) > 0:
        for specta_block in blocks(to_add, settings['fasta']['spectra_block']):
            spectra.extend(generate_spectra(specta_block, mass_dict))

    return (spectra, pept_dict)

import alphapept.performance

#This function is a wrapper function and to be tested by the integration test
def generate_database_parallel(settings:dict, callback = None):
    """
    Function to generate a database from a fasta file in parallel.
    Args:
        settings: alphapept settings.
    Returns:
        list: theoretical spectra. See generate_spectra()
        dict: peptide dict. See add_to_pept_dict()
        dict: fasta_dict. See generate_fasta_list()
    """

    n_processes = alphapept.performance.set_worker_count(
        worker_count=settings['general']['n_processes'],
        set_global=False
    )

    fasta_list, fasta_dict = generate_fasta_list(fasta_paths = settings['experiment']['fasta_paths'], **settings['fasta'])

    logging.info(f'FASTA contains {len(fasta_list):,} entries.')

    blocks = block_idx(len(fasta_list), settings['fasta']['fasta_block'])

    to_process = [(idx_start, fasta_list[idx_start:idx_end], settings) for idx_start, idx_end in  blocks]

    spectra = []
    pept_dicts = []
    with Pool(n_processes) as p:
        max_ = len(to_process)
        for i, _ in enumerate(p.imap_unordered(digest_fasta_block, to_process)):
            if callback:
                callback((i+1)/max_)
            spectra.extend(_[0])
            pept_dicts.append(_[1])

    spectra = sorted(spectra, key=lambda x: x[1])
    spectra_set = [spectra[idx] for idx in range(len(spectra)-1) if spectra[idx][1] != spectra[idx+1][1]]
    spectra_set.append(spectra[-1])

    pept_dict = merge_pept_dicts(pept_dicts)

    return spectra_set, pept_dict, fasta_dict

# Cell
#This function is a wrapper function and to be tested by the integration test
def pept_dict_from_search(settings:dict):
    """
    Generates a peptide dict from a large search.
    """

    paths = settings['experiment']['file_paths']
    bases = [os.path.splitext(_)[0]+'.ms_data.hdf' for _ in paths]

    all_dfs = []
    for _ in bases:
        try:
            df = alphapept.io.MS_Data_File(_).read(dataset_name="peptide_fdr")
        except KeyError:
            df = pd.DataFrame()

        if len(df) > 0:
            all_dfs.append(df)

    if sum([len(_) for _ in all_dfs]) == 0:
        raise ValueError("No sequences present to concatenate.")

    df = pd.concat(all_dfs)

    df['fasta_index'] = df['fasta_index'].str.split(',')

    lst_col = 'fasta_index'

    df_ = pd.DataFrame({
          col:np.repeat(df[col].values, df[lst_col].str.len())
          for col in df.columns.drop(lst_col)}
        ).assign(**{lst_col:np.concatenate(df[lst_col].values)})[df.columns]

    df_['fasta_index'] = df_['fasta_index'].astype('int')
    df_grouped = df_.groupby(['sequence'])['fasta_index'].unique()

    pept_dict = {}
    for keys, vals in zip(df_grouped.index, df_grouped.values):
        pept_dict[keys] = vals.tolist()

    return pept_dict

# Cell
import alphapept.io
import pandas as pd

def save_database(spectra:list, pept_dict:dict, fasta_dict:dict, database_path:str, **kwargs):
    """
    Function to save a database to the *.hdf format. Write the database into hdf.

    Args:
        spectra (list): list: theoretical spectra. See generate_spectra().
        pept_dict (dict): peptide dict. See add_to_pept_dict().
        fasta_dict (dict): fasta_dict. See generate_fasta_list().
        database_path (str): Path to database.
    """

    precmasses, seqs, fragmasses, fragtypes = zip(*spectra)
    sortindex = np.argsort(precmasses)
    fragmasses = np.array(fragmasses, dtype=object)[sortindex]
    fragtypes = np.array(fragtypes, dtype=object)[sortindex]

    lens = [len(_) for _ in fragmasses]

    n_frags = sum(lens)

    frags = np.zeros(n_frags, dtype=fragmasses[0].dtype)
    frag_types = np.zeros(n_frags, dtype=fragtypes[0].dtype)

    indices = np.zeros(len(lens) + 1, np.int64)
    indices[1:] = lens
    indices = np.cumsum(indices)

    #Fill data

    for _ in range(len(indices)-1):

        start = indices[_]
        end = indices[_+1]
        frags[start:end] = fragmasses[_]
        frag_types[start:end] = fragtypes[_]

    to_save = {}

    to_save["precursors"] = np.array(precmasses)[sortindex]
    to_save["seqs"] = np.array(seqs, dtype=object)[sortindex]
    to_save["proteins"] = pd.DataFrame(fasta_dict).T

    to_save["fragmasses"] = frags
    to_save["fragtypes"] = frag_types
    to_save["indices"] = indices

    db_file = alphapept.io.HDF_File(database_path, is_new_file=True)
    for key, value in to_save.items():
        db_file.write(value, dataset_name=key)

    peps = np.array(list(pept_dict), dtype=object)
    indices = np.empty(len(peps) + 1, dtype=np.int64)
    indices[0] = 0
    indices[1:] = np.cumsum([len(pept_dict[i]) for i in peps])
    proteins = np.concatenate([pept_dict[i] for i in peps])

    db_file.write("peptides")
    db_file.write(
        peps,
        dataset_name="sequences",
        group_name="peptides"
    )
    db_file.write(
        indices,
        dataset_name="protein_indptr",
        group_name="peptides"
    )
    db_file.write(
        proteins,
        dataset_name="protein_indices",
        group_name="peptides"
    )

# Cell
import collections

def read_database(database_path:str, array_name:str=None)->dict:
    """
    Read database from hdf file.
    Args:
        database_path (str): hdf database file generate by alphapept.
        array_name (str): the dataset name to read
    return:
        dict: key is the dataset_name in hdf file, value is the python object read from the dataset_name
    """
    db_file = alphapept.io.HDF_File(database_path)
    if array_name is None:
        db_data = {
            key: db_file.read(
                dataset_name=key
            ) for key in db_file.read() if key not in (
                "proteins",
                "peptides"
            )
        }
        db_data["fasta_dict"] = np.array(
            collections.OrderedDict(db_file.read(dataset_name="proteins").T)
        )
        peps = db_file.read(dataset_name="sequences", group_name="peptides")
        protein_indptr = db_file.read(
            dataset_name="protein_indptr",
            group_name="peptides"
        )
        protein_indices = db_file.read(
            dataset_name="protein_indices",
            group_name="peptides"
        )
        db_data["pept_dict"] = np.array(
            {
                pep: (protein_indices[s: e]).tolist() for pep, s, e in zip(
                    peps,
                    protein_indptr[:-1],
                    protein_indptr[1:],
                )
            }
        )
        db_data["seqs"] = db_data["seqs"].astype(str)
    else:
        db_data = db_file.read(dataset_name=array_name)
    return db_data