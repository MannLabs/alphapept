#Analyze statistics
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import h5py
import os
import alphapept.io
import seaborn as sns
from tqdm.notebook import tqdm as tqdm

def prepare_files(path1, path2):

    df1 = [pd.DataFrame(np.array(h5py.File(path1)['protein_fdr'][_])) for _ in h5py.File(path1)['protein_fdr'].keys()]
    df1 = pd.concat(df1, axis=1)
    df1.columns = h5py.File(path1)['protein_fdr'].keys()

    # add sequence charge
    df1['missed_cleavages'] = df1['sequence'].str[:-1].str.count('K') + df1['sequence'].str[:-1].str.count('R')

    #Convert maxquant
    df2 = pd.read_csv(path2, sep='\t')
    df2['charge'] = df2['Charge']

    list_2 = df2['Modified sequence'].values
    list_2 = [alphapept.io.parse_mq_seq(_) for _ in list_2]
    df2['sequence'] = list_2

    df2['precursor'] = ['_'.join(_) for _ in zip(list_2, df2['Charge'].values.astype('int').astype('str'))]
    df2['protein'] = df2['Leading razor protein']
    df2['decoy'] = df2['Reverse'] == '+'
    df2['score'] = df2['Score']
    df2['int_sum'] = df2['Intensity']
    df2['missed_cleavages'] = df2['sequence'].str[:-1].str.count('K') + df2['sequence'].str[:-1].str.count('R')

    return df1, df2


def compare_field(df1, df2, software_1, software_2, field, exclude_decoy=True):

    title_dict = {'protein':'Number of unique proteins',
                 'sequence': 'Number of unique peptide sequences',
                 'precursor':'Number of unique sequence/charge combinations',
                 'charge':'Occurence of charge states',
                 'digestion':'Occurence of last AA in sequence',
                 'total_missed_cleavages':'Total number of missed cleavages',
                 'missed_cleavages':'Ratio of number of of missed cleavages'}#nicer descriptions for the plots

    if exclude_decoy:
        df1 = df1[~df1['decoy']]
        df2 = df2[~df2['decoy']]

    #Some pre-defined boundaries
    plt.figure(figsize=(5,5))

    if field == 'charge':
        ratios = df1[field].value_counts() / df2[field].value_counts()
        plt.axhline(1, color='k', linestyle=':')
        plt.bar(ratios.index, ratios.values, label='Ratio {}/{}'.format(software_1, software_2))
        plt.legend()
        #bins = np.arange(1,6,0.5)

        #plt.hist(df1[field].values, bins=bins,label=software_1)
        #plt.hist(df2[field].values-0.5, bins=bins, label=software_2)

        plt.legend()

    elif (field == 'protein') or (field == 'sequence') or (field == 'precursor'):
        plt.bar(software_1, len(set(df1[field])))
        plt.bar(software_2, len(set(df2[field])))

    elif (field == 'digestion'):
        ratios = df1['sequence'].str[-1].value_counts() / df2['sequence'].str[-1].value_counts()
        plt.axhline(1, color='k', linestyle=':')
        plt.bar(ratios.index, ratios.values, label='Ratio {}/{}'.format(software_1, software_2))
        plt.legend()


    elif (field == 'total_missed_cleavages'):
        field_ = 'missed_cleavages'
        plt.bar(software_1, df1[field_].sum())
        plt.bar(software_2, df2[field_].sum())


    elif (field == 'missed_cleavages'):
        ratios = df1[field].value_counts() / df2[field].value_counts()
        plt.axhline(1, color='k', linestyle=':')
        plt.bar(ratios.index, ratios.values, label='Ratio {}/{}'.format(software_1, software_2))

    else:
        raise NotImplementedError

    plt.title(title_dict[field])
    plt.show()


from matplotlib_venn import venn2
def compare_populations(df1, df2, software_1, software_2, field, exclude_decoy=True):
    """
    Compare to lists of peptides / proteins

    Convention: all should be uppercase
    ToDo: check this maybe
    """

    title_dict = {'protein':'Shared proteins',
                 'sequence': 'Shared peptide sequences',
                 'precursor':'Shared sequence/charge combinations',
                 }

    if exclude_decoy:
        df1 = df1[~df1['decoy']]
        df2 = df2[~df2['decoy']]

    list_1 = df1[field].values
    list_2 = df2[field].values

    peptides_1 = set(list_1)
    peptides_2 = set(list_2)
    n_1 = len(peptides_1 - peptides_2)
    n_2 = len(peptides_2 - peptides_1)
    shared = len(peptides_1.intersection(peptides_2))

    venn2(subsets = (n_1, n_2, shared), set_labels = (software_1, software_2))
    plt.title(title_dict[field])
    plt.show()

def compare_intensities(df1, df2,software_1, software_2):
    ref_df1 = df1.copy()
    ref_df2 = df2.copy()

    f, (ax1, ax2) = plt.subplots(1, 2, sharey=True,sharex=True, figsize=(10,5))

    axes = [ax1, ax2]

    for idx, _ in enumerate(['protein','precursor']):

        ax = axes[idx]
        d1 = ref_df1[[_,'total_int']].groupby(_).sum()
        d2 = ref_df2[[_,'int_sum']].groupby(_).sum()

        shared = set(d1.index.values).intersection(set(d2.index.values))

        ax.scatter(d1.loc[shared]['total_int'].values, d2.loc[shared]['int_sum'].values, alpha=0.2, marker='.')
        ax.set_xscale('log')
        ax.set_yscale('log')

        ax.set_xlabel(software_1)
        ax.set_ylabel(software_2)
        ax.set_title(f"{_} intensity")

    mins_ = []
    maxs_ = []

    for idx, _ in enumerate(['protein','precursor']):
        ax = axes[idx]

        ylim = ax.get_ylim()
        xlim = ax.get_xlim()

        mins_.append(ylim[0])
        maxs_.append(ylim[1])

        mins_.append(xlim[0])
        maxs_.append(xlim[1])

    min_ = np.min(mins_)
    max_ = np.max(maxs_)

    max_ = 10**np.ceil(np.log10(max_))
    min_ = np.max([1, 10**np.floor(np.log10(min_))])

    for idx, _ in enumerate(['protein','precursor']):
        ax = axes[idx]
        ax.set_xlim([min_, max_])
        ax.set_ylim([min_, max_])
        ax.plot([min_, max_], [min_, max_], 'k:', alpha=0.7)

    plt.show()


def protein_rank(df1, df2, software_1, software_2):
    data_1 = df1[['protein','total_int']].groupby('protein').sum()
    data_1 = data_1.sort_values(by='total_int', ascending=False) #.head(20)

    data_2 = df2[['Leading proteins','Intensity']].groupby('Leading proteins').sum()
    data_2 = data_2.sort_values(by='Intensity', ascending=False) #.head(20)


    plt.figure(figsize=(5,5))
    plt.plot(data_1['total_int'].values, label=software_1)
    plt.plot(data_2['Intensity'].values, label=software_2)
    plt.yscale('log')
    plt.legend()
    plt.ylabel('Protein Intensity')
    plt.show()

def get_plot_df(ref, base_columns, ratio_columns, ax, id_):

    to_plot = pd.DataFrame()
    to_plot['Species'] = ref['Species']

    to_plot['base'] = ref[base_columns].median(axis=1)
    to_plot['ratio'] = ref[ratio_columns].median(axis=1)
    to_plot['base_cnt'] = (ref[base_columns] != 0).sum(axis=1)
    to_plot['ratio_cnt'] = (ref[ratio_columns] != 0).sum(axis=1)

    to_plot['ratio_'] = np.log2(to_plot['base'] / to_plot['ratio'])
    to_plot['sum_'] = np.log2(to_plot['ratio'])

    valid = to_plot.query(f'ratio_cnt >= 2 and base_cnt >=2')

    ax = sns.scatterplot(ax = ax, x="ratio_", y="sum_", hue="Species", data=valid, alpha=0.2)

    homo = valid[valid['Species'] == 'Homo sapiens']['ratio_'].values
    e_coli = valid[valid['Species'] == 'Escherichia coli']['ratio_'].values

    homo_ratio = np.nanmean(homo[~np.isinf(homo)])
    e_coli_ratio = np.nanmean(e_coli[~np.isinf(e_coli)])

    homo_ratio_std = np.nanstd(homo[~np.isinf(homo)])
    e_coli_ratio_std = np.nanstd(e_coli[~np.isinf(e_coli)])

    nl = '\n'
    ax.set_title(f'{id_} {nl} Homo (mean, std) {homo_ratio:.2f}, {homo_ratio_std:.2f} {nl} EColi (mean, std) {e_coli_ratio:.2f}, {e_coli_ratio_std:.2f} {nl} {valid["Species"].value_counts().to_dict()}')

def algorithm_test(evd, ref, base_columns, ratio_columns, base_columns2, ratio_columns2, test_id, software_1, software_2):
    spec_dict = {}
    all_points = []
    species_ = []

    experiments = evd['Raw file'].unique().tolist()

    protein_idx = []

    for i in tqdm(range(len(ref))):

        investigate = ref.iloc[i]
        evd_ids = [int(_) for _ in investigate['Evidence IDs'].split(';')]
        species = investigate['Species']
        subset = evd.loc[evd_ids].copy()

        field_ = 'Intensity'

        subset['protein'] = 'X'
        subset['shortname'] = subset['Raw file']
        subset['precursor']  = ['_'.join(_) for _ in zip(subset['Modified sequence'].values, subset['Charge'].values.astype('str'))]
        protein = 'X'


        from alphapept.quantification import protein_profile

        profile, pre_lfq, experiment_ids, protein = protein_profile(subset, experiments, field_, protein)
        xx = pd.DataFrame([profile, pre_lfq], columns=experiment_ids).T
        xx.columns = ['lfq_ap', 'int_ap']

        all_points.append(xx[['lfq_ap']].T)
        protein_idx.append(i)
        species_.append(species)

    df = pd.concat(all_points)
    df.index = protein_idx
    df['Species'] = species_

    fig, axes = plt.subplots(1, 2, figsize=(14,7), sharex=True,sharey=True)

    id_ = f'{software_2} {test_id}'
    get_plot_df(ref, base_columns, ratio_columns, axes[0], id_)

    id_ = f'{software_1} on {software_2} {test_id}'
    get_plot_df(df, base_columns2, ratio_columns2, axes[1], id_)