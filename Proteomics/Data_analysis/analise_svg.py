#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 11:56:16 2024

@author: paulaanteloriveiro
"""


''' 
This program performs the analysis of proteomics data for the following data sets:
- plasma with library v2024
- pellet with library v2024
- plasma with library v2022
- pellet with library v2022
The most general protocol consists of a scaling of the data, PCA, clustering and 
association metrics between clusters and clinical data
'''




import numpy as np
import pandas as pd
import scipy
import matplotlib.pyplot as plt
import matplotlib.cm     as cm
import os
import seaborn as sns

from adjustText import adjust_text


from sklearn.preprocessing import PowerTransformer
from sklearn.cluster import KMeans

from sklearn.feature_selection import VarianceThreshold

from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, jaccard_score, confusion_matrix



'''  
BEGINNING OF FUNCTIONS DEFINITION
'''


def process_raw_areas(areas_raw, patient_indices, add = []):
    '''
    Modify the raw data file to update the format
    - delete those proteins that start with RRR
    - select only the appropriate sample type
    - save inmunoglobulins proteins in a list (proteins with IG in the name)
    - update the proteins name to keep only the uniprot code
    Params:
        areas_raw:       pd.DataFrame, containing the peak areas of the proteins for each sample
        patient_indices: list, list of patient indices for the data frame
        add:             list, list of patients to add, if given. Used if additional patients are provided
    Returns:
        areas_proc: pd.DataFrame, containing the peak areas in the right format
        ig:         list, containing the protein codes that are inmunoglobulins
    '''

    areas_proc = areas_raw.transpose()
    
    areas_proc = areas_proc[[col for col in areas_proc.columns if not col.startswith('RRR')]]
    ig = [col.split('|')[2].split('_')[0] for col in areas_proc.columns if 'IG' in col]
    
    areas_proc.columns = [i.split('|')[2].split('_')[0] for i in areas_proc.columns.values]
    
    areas_proc = areas_proc.loc[patient_indices + [f'{i}_{sample_type}' for i in add]]

    return areas_proc, ig





def calculate_volcano(df, test = 't', check = False):
    '''
    Calculates the necessary data to build the volcano plot: log2FC, log10 p-value.
    Fold Change is calculate as the ratio between the means of each group.
            FC_prot = mean_prot_class1 / mean_prot_class0
    The statistical test used is by default T-test, but can be changed to Mann-Whitney.
    An analysis of the validity of each test can also be provided.
    Params:
        df:    pd.DataFrame, containing the areas data plus a columnd indicating the class 
                of each patient for the volcano
        test:  string, options are t (T-test) or MU (Mann-Whithney)
        check: bool, whether to check if the tests are being applied correctly, ensuring
                all asumptions are fulfilled. If true, only proteins that fulfill the test
                hypothesis are considered
    Returns:

    '''
    class0, class1 = df[df['class'] == 0].index.values, df[df['class'] == 1].index.values

    volcano_plot = df.groupby(by = 'class').mean().T
    volcano_plot.columns = ['mean0', 'mean1']
    
    df = df.drop('class', axis = 1)

    alpha          = 0.05
    ambas_normais  = ([scipy.stats.shapiro(areas_raw[protein].loc[class0]).pvalue > alpha for protein in areas_raw.columns.values]) and ([scipy.stats.shapiro(areas_raw[protein].loc[class1]).pvalue > alpha for protein in areas_raw.columns.values])
    equal_var      = [scipy.stats.levene(areas_raw[protein].loc[class0], areas_raw[protein].loc[class1]).pvalue > alpha for protein in areas_raw.columns.values]
    ningun_valido  = [not(norm) and not(eqv) for norm, eqv in zip(ambas_normais, equal_var)]
    resumo_validez = pd.DataFrame(np.array([ambas_normais, equal_var, ningun_valido]).T, index = volcano_plot.index.values, columns = ['norm', 'eqvar', 'ningunvalido'])
    
    valido_ttest   = resumo_validez[resumo_validez['norm'] == True].index.values
    valido_MU      = resumo_validez[resumo_validez['eqvar'] == True].index.values
    
    
    if test == 't':
        
        if check == True:
            
            volcano_plot = volcano_plot.loc[valido_ttest]
            df           = df[valido_ttest]
        
        volcano_plot['p-values'] = [scipy.stats.ttest_ind(a = df[protein].loc[class0], b = df[protein].loc[class1]).pvalue for protein in df.columns.values]
    
    
    elif test == 'MU':
        
        if check == True:
            
            volcano_plot = volcano_plot.loc[valido_MU]
            df           = df[valido_MU]
        
        volcano_plot['p-values'] = [scipy.stats.mannwhitneyu(df[protein].loc[class0], df[protein].loc[class1]).pvalue for protein in df.columns.values]
    
    volcano_plot['FC'] = volcano_plot['mean1'] / volcano_plot['mean0']
    
    return volcano_plot, resumo_validez






def plot_volcano(volcano, title = None, ax = None):
    '''
    Plot de volcano data from the volcano file
    Params:
        volcano: pd.DataFrame, with FC and pvalue results ready to plot
        title:   string, title to used for the figure
        ax:      matplotlib axes, optional, to use for the plot
    Returns:
        ax:      matplotlib axes, axis with the volcano plot
    '''
    
    if ax is None: 
        
        fig = plt.figure(); ax = fig.add_subplot()

    fontsize = 12; s = 12; alpha = 0.65
    red = '#D44242'; green = '#37CC93'; yellow = '#E0B84D'; cyan = '#80CBEA'; blue = '#090AFF'
    
    
    volcano_sig = volcano[volcano['p-values'] <= 0.05]
    volcano_nonsig = volcano[volcano['p-values'] > 0.05]
    ax.scatter(np.log2(volcano_nonsig['FC']), -np.log10(volcano_nonsig['p-values']), 
               edgecolor = 'k', linewidth = 0.4, s = s, color = 'gray', alpha = alpha)
    
    volcano_over = volcano_sig[volcano_sig['FC'] >= 1.5]
    ax.scatter(np.log2(volcano_over['FC']), -np.log10(volcano_over['p-values']), 
               edgecolor = 'k', linewidth = 0.4, s = s, color = red, alpha = alpha)
    
    volcano_sub = volcano_sig[volcano_sig['FC'] <= 1 / 1.5]
    ax.scatter(np.log2(volcano_sub['FC']), -np.log10(volcano_sub['p-values']), 
               edgecolor = 'k', linewidth = 0.4, s = s, color = green, alpha = alpha)
    
    volcano_below = volcano_sig[volcano_sig['FC'] < 1.5]
    volcano_below = volcano_below[volcano_below['FC'] > 1 / 1.5 ]
    ax.scatter(np.log2(volcano_below['FC']), -np.log10(volcano_below['p-values']), 
               edgecolor = 'k', linewidth = 0.4, s = s, color = yellow, alpha = alpha)
    
    
    ax.tick_params(direction = 'in', labelsize = fontsize)
    ax.set_xlabel('Log$_2$(FC)', fontsize = fontsize)
    ax.set_ylabel('-Log$_{10}$(p-value)', fontsize = fontsize)
    
    x_limits = {'P': (-3,3), 'S': (-4,4)}
    xlim = x_limits[sample_type]
    ax.set_xlim(xlim)
    ylim = ax.get_ylim(); ax.set_ylim(ylim)
    ax.hlines(y = -np.log10(0.05), xmin = xlim[0], xmax = xlim[1], linestyle = '--', color = 'gray')
    ax.vlines(x = np.log2(1.5), ymin = ylim[0], ymax = ylim[1], linestyle = '-.', color = cyan)
    ax.vlines(x = np.log2(1/1.5), ymin = ylim[0], ymax = ylim[1], linestyle = '-.', color = cyan)
    ax.vlines(x = 0, ymin = ylim[0], ymax = ylim[1], linestyle = '--', color = blue)
    
    texts = [ax.text(x = np.log2(volcano_sig['FC'])[i], y = -np.log10(volcano_sig['p-values'])[i], 
             s = volcano_sig.index.values[i], fontsize = 6.5) for i in range(len(volcano_sig.index.values))]

    ax.set_title(title, fontsize = 16)
    
    adjust_text(texts = texts, ax = ax, force_explode = (0.3, 1))
    
    return ax





def evaluate_col(areas_old, col):
    '''
    Calculate the Jaccard score after the PCA-clustering protocol to 
    evaluate the association between clusters and symptoms
    Params:
        areas_old: pd.DataFrame, containing the areas por each protein and patient
        col:       string, name of the column to delete from areas_old before PCA-clustering+Jaccard
    Returns:
        clusters_new: np.array, containing the clusters identification
        areas_new:    pd.DataFrame, areas file without the col column
        pca_new:      sklearn.PCA(), PCA method training with the areas data
        jaccard_new:  float, evaluation of the Jaccard score comparing clusters identification
                        and symptoms classification
    '''
    
    areas_new = areas_old.drop([col], axis = 1)
    
    pca_new       = PCA().fit(areas_new)
    areas_pca_new = pca_new.transform(areas_new)
    
    if scipy.stats.linregress(areas_pca_new[:,0], clinical_classifications['all'].values).slope < 0:   # cluster 0 o de menos síntomas
        
        areas_pca_new[:,0] = - areas_pca_new[:,0]
        
    clusters_new = KMeans(n_clusters = 2, n_init = 300, max_iter = 200, random_state = 45).fit(areas_pca_new).labels_
    clusters_new = order_clusters(clusters_new)
    
    jaccard_new = jaccard_score(clusters_new, compare_clinical)
    
    return clusters_new, areas_new, pca_new, jaccard_new




def find_max_jaccard(areas):
    '''
    Delete proteins recursively from the areas data frame
    At each step, select the protein to delete that favors the most the Jaccard score
    Keep the selection of proteins that raise the highest Jaccard score
    Params:
        areas: pd.DataFrame, containing areas data for each patient and protein
    Returns: 
        use_columns: list, containing the protein names that raise the highest Jaccard score
    '''
    print('\nStart recursive elimination of proteins to select the highest Jaccard score')
    areas_old     = areas.copy()
    pca_old       = PCA().fit(areas_old)
    areas_pca_old = pca_old.transform(areas_old)
    
    # make sure that PC1 goes with increasing symptomatology so the Jaccard score is well defined
    # jaccard score depend on the exact 0-1 value of the clusters
    if scipy.stats.linregress(areas_pca_old[:,0], clinical_classifications['ext'].values).slope < 0:   # cluster 0 o de menos síntomas
        areas_pca_old[:,0] = - areas_pca_old[:,0]
    
    clusters_old = KMeans(n_clusters = 2, n_init = 10).fit(areas_pca_old).labels_
    jaccard_old  = jaccard_score(clusters_old, compare_clinical)
    
    removed_cols     = ['None']
    jaccard_new      = 0
    list_jaccard_new = [jaccard_old]
    
    while np.shape(areas_old)[1] > 1:

        # evaluate jaccard removing individually and independentely each protein
        # select the protein (to be deleted) that favors the most de Jaccard score
        jaccards_news = [evaluate_col(areas_old, col)[3] for col in areas_old.columns.values]
                
        col_optimal = areas_old.columns.values[np.argmax(jaccards_news)]
        
        clusters_new, areas_new, pca_new, jaccard_new = evaluate_col(areas_old, col_optimal)
        print(f'{col_optimal:15}: {jaccard_old:.3f} -> {jaccard_new:.3f}')
        
        list_jaccard_new.append(jaccard_new)
    
        clusters_old = clusters_new
        areas_old    = areas_new
        pca_old      = pca_new
        jaccard_old  = jaccard_new
    
        removed_cols.append(col_optimal)
    
    delete_cols = removed_cols[:np.where(list_jaccard_new == np.max(list_jaccard_new))[0][-1] + 1]
    use_columns = [i for i in areas.columns.values if i not in delete_cols]
    
    # plot a summary of the analysis
    fig = plt.figure(); ax = fig.add_subplot()
    ax.scatter(removed_cols, list_jaccard_new)
    ax.set_ylabel('Jaccard score')
    ax.tick_params(labelrotation = 90)
    fig.tight_layout()
    fig.savefig(f'{directory2}jaccard_featselection.svg', dpi = 300)
                    
    return use_columns



def severidade_angel(X, clusters, pesos_comp = None):
    '''
    Severity metric used in the first proteomics paper, see reference
    Params:
        X:          pd.DataFrame, containing the normalized areas
        clusters:   np.array, containing the identification of clusters for each patient
        pesos_comp: np.array, weight for each protein
    Returns:
        severity_score: np.array, containing the severity score for each patient
        cluster_means:  np.array, containing the mean value of each protein for each cluster
        pesos_comp:     np.array, weight for each protein
    '''
    
    df = X.copy()   # xa escalado
    columnas = df.columns
    df.insert(0, 'cluster', clusters)
    
    # Calculo os centros de cada cluster
    cluster_means = df.groupby(by = 'cluster').mean()
    
    if pesos_comp is None:
        # Calculo a importancia de cada compoñente na separación dos clusteres (2)
        pesos_comp = (cluster_means.loc[0] - cluster_means.loc[1]).abs() 
        pesos_comp *= np.sign(cluster_means.loc[0])    # ENGADIDO CL1: valores baixos PCs, Cl2: valores altos PCs
        pesos_comp = pesos_comp / np.sum(abs(pesos_comp)) 
        
    def individual_severity(row): 
        
        # Calculo a severidade para cada compoñente e suma sobre todas as compoñentes
        severity_scores = (cluster_means.loc[0] - row[columnas]) + (cluster_means.loc[1] - row[columnas])
        severity_scores *= pesos_comp
        severity_score  = severity_scores.sum()
        
        return severity_score

    
    # Calculo o valor de severidade para cada paciente
    S = df.apply(individual_severity, axis = 1)
    
    if scipy.stats.linregress(S, clinical_classifications['all'].values).slope < 0:
        
        S = -S
    
    return S, cluster_means, pesos_comp



def dividir_sintomas(x, limit = 1):
    ''' 
    Returns 1 if x >= limit and 0 if x < limit
    Params:
        x:     int, value to copare or recode
        limit: int, limit value to distinguish between groups
    Returns: 
        r:     int, value 0 or 1 depending on x and limit
    '''
    r = 0
    if x >= limit:
        r = 1
        
    return r



def violin(data, color, ax, positions = None):
    ''' 
    Create a customized violin plot 
    Params:
        data:      list of arrays, list containing the data for the distribution of values in each violin
        color:     string or RGB color, used for the violin
        ax:        matplotlib axis, where to plot the violins
        positions: list, x positions where to center each violin
    '''
    
    try:
        quartile1, medians, quartile3 = np.percentile(data, [25, 50, 75], axis=0)
        means   = np.mean(data)
        minimos = np.min(data)
        maximos = np.max(data)
        iqr     = quartile3 - quartile1
      
    except ValueError:
        quartile1 = np.array([np.percentile(dat, 25) for dat in data])
        means     = np.array([np.mean(dat) for dat in data])
        quartile3 = np.array([np.percentile(dat, 75) for dat in data])
        minimos   = np.array([np.min(dat) for dat in data])
        maximos   = np.array([np.max(dat) for dat in data])
        iqr       = quartile3 - quartile1
        
        positions = np.arange(1, len(means) + 1)
        
    parts = ax.violinplot(data, showmeans = False, showmedians = False, showextrema = False, positions = positions)
        
    whiskers_min = np.clip(quartile1 - 1.5*iqr, minimos, quartile1)
    whiskers_max = np.clip(quartile3 + 1.5*iqr, quartile3, maximos)
    
    for pc in parts['bodies']:
            
        pc.set(facecolor = color, edgecolor = 'black', alpha = 0.4)
        
    ax.vlines(positions, whiskers_min, whiskers_max, color = color, alpha = 0.8)
    ax.vlines(positions, quartile1, quartile3, color = color, linestyle = '-', lw = 4, alpha = 0.6, edgecolor = 'k')
    ax.scatter(positions, means, marker = 'o', color = 'w', alpha = 1, s = 50, edgecolor = color)
    ax.hlines(maximos, positions - 0.1, positions + 0.1, color = color)
    ax.hlines(minimos, positions - 0.1, positions + 0.1, color = color)
        
    return 



def violin_s_classifications(classification_name, S, binary = False, limit = 1):
    '''
    Build a violin plot of the severity metric distribution for each symptomatology criterion
    Params:
        classification_name: string, can take the values ext, 90d, 9m, all. The symptoms criterion to plot
        S:                   pd.DataFrame, containing severity metric values for all patients
        binary:              bool, use a limit (int number) to divide the patients into only two groups (two violins)
        limit:               int, number of symptoms to separate the two gorups of patients 
                                Group A: zero or one symptons; Group B: more than 1 symptom
    Returns:
        fig: matplotlib figure, containing the violin plot and a title that shows the p-value (MU test)
    '''

    classification_use = clinical_classifications[classification_name] # select the symptoms column in the clinical classifications data frame
    name = f'{directory2}violin_S_{classification_name}.svg'           # file name to save
    
    # create the figure
    fig = plt.figure(); ax = fig.add_subplot()
    ax.tick_params(direction = 'in')
    
    if binary: 
        # use the dividir_sintomas function to recode the data for each patient
        classification_use = classification_use.apply(lambda x: dividir_sintomas(x, limit)) 
        ax.set_xticks(ticks = [1,2], labels = clusternames) # set xticklabels to clusternames
        name = f'{directory2}violin_S_{classification_name}_01.svg' # change the file name
        
    classification_use = classification_use.values # take the values as a np.array
    # build a pd.DataFrame with the S values and the classification label
    df_severidade_sintomas = pd.DataFrame(np.array([np.array(S.values), classification_use]).T,
                                          columns = ['S', classification_name], index = S.index.values)
    # make a list with two elements: two array containing the S values of patients in each symptom group
    boxplot_suma = [np.array(df_severidade_sintomas.groupby(by = classification_name).get_group(i)['S']) for i in set(classification_use)]
    
    if binary: # apply the Mann Whitney U test if there only two groups
        
        if scipy.stats.mannwhitneyu(boxplot_suma[0], boxplot_suma[1]).pvalue < 0.005:
            
            ax.set_title(f'p-value (Mann-Whitney U) < 0.005')
            
        else:
            
            ax.set_title(f'p-value (Mann-Whitney U) = {scipy.stats.mannwhitneyu(boxplot_suma[0], boxplot_suma[1]).pvalue:.3f}')
    
    if limit > 1: # update xtick labels
        
        ax.set_xticks(ticks = np.array([1,2]), labels = [f'{clusternames[0]}\n(<{limit} symptoms)', f'{clusternames[1]}\n($\\geq${limit} symptoms)'])

    # use the violin function to plot the boxplot_suma list in two violins or more
    violin(boxplot_suma, 'purple', ax)
    ax.set_ylabel('Severity metric distribution')
    ax.set_xlabel(f'{classification_name} symptoms considered')
    fig.tight_layout()
    
    fig.savefig(name, dpi = 400) # save the figure and close
    plt.close(fig)
    
    return fig



def order_clusters(clusters):
    '''
    Force clusters to be 0 for asymptomatic patients and 1 for symptomatic patients
    Params:
        clusters: np.array, containing the cluster identification for each patient
    Returns:
        clusters_out: np.array, containing the cluster identification for each patient (updated)
    '''
    # if there is a positive slope between clusters and symptoms, do not update
    if scipy.stats.linregress(clusters, clinical_classifications['all'].values).slope > 0:   
        
        clusters_out = np.copy(clusters)
        
    else: # else change 0-1
        
        clusters_out = abs(clusters- 1)  
    
    return clusters_out



def mapacores_sintomasS(df_imshow, S):
    '''
    Plot the heatmap for clinical variables
    Params:
        df_imshow: pd.DataFrame, containing the 0-1 clinical variables of each patient
        S:         np.array, severity metric to sort the patients
    Returns:
        fig: matplotlib figure, containing the heatmap
        ax:  matplotlib axis, the axis in the figure that contains the heatmap
    '''
    df_plot           = df_imshow.copy()
    df_plot['ordear'] = np.copy(S)  # include a ordear column that has the S values
    df_plot           = df_plot.sort_values(by='ordear')
    # normalize the total number of symptoms by its maximum value
    df_plot['Num_SI_sintomas'] /= max(df_plot['Num_SI_sintomas']) 

    # convert the columns of the data frame that will appear in the heatmap into a np.array
    sintomas_analizar = [col for col in df_plot.columns if col != 'Num_SI_sintomas' and col != 'ordear']
    imshow = np.array(df_plot[sintomas_analizar + ['Num_SI_sintomas']])
    
    # create the figure
    fig = plt.figure(figsize = (9,7)); ax  = fig.add_subplot()
    ax.pcolor(imshow, cmap = 'summer', edgecolors = 'k', linewidths = 0.2, alpha = 0.95)    
    # update xticks, yticks
    ax.set_xticks(np.arange(len(sintomas_analizar) + 1),  labels=sintomas_analizar + ['Percentage of symptoms'], fontsize = 6)
    ax.set_yticks(np.arange(len(df_plot.index.values)) + 0.5, labels=df_plot.index.values, fontsize = 5)
    ax.tick_params(bottom = False, left = False)

    plt.setp(ax.get_xticklabels(), rotation = 90, ha="right", rotation_mode="anchor")
    ax.set_ylabel('Patients ordered by Severity Metric')
    
    # get xticklabels, yticklabels and change weight so some of them are bold
    x_labels = ax.get_xticklabels()
    [x_labels[i].set_weight('bold') for i in range(len(x_labels)) if i%2 == 0]
    ax.set_xticklabels(x_labels)
    y_labels = ax.get_yticklabels()
    [y_labels[i].set_weight('bold') for i in range(len(y_labels)) if i%2 == 0]
    ax.set_yticklabels(y_labels)

    fig.tight_layout()

    return fig, ax



def feature_selection_analysis(areas_sorted):
    '''
    Recursive removal of proteins with lower contribution to PC1
    NOT USED IN THIS WORK
    '''
    
    limit = 5
    compare_clinical = clinical_classifications['all'].apply(lambda x: dividir_sintomas(x, limit = limit))
    
    silhouette_sorted = [np.max(silhouette_list)]
    jaccard_sorted    = [jaccard_score(compare_clinical, clusters['cluster'])]
    r2_sorted         = [scipy.stats.linregress(areas_pca[:,0], clinical_classifications['all'].values).rvalue**2]
    areas_sorted_rem  = areas_sorted.copy()
    
    clusters_old = np.copy(clusters['cluster'].values)

    for i,col in enumerate(np.flip(areas_sorted.columns.values)):
        
        if i != len(areas_sorted.columns.values) - 1:
            
            areas_sorted_rem = areas_sorted_rem.drop([col], axis = 1)
            print(f'Removing {col}, {np.shape(areas_sorted_rem)[1]} proteins remaining')
            
            pca_sorted = PCA().fit(areas_sorted_rem)
            print(pca_sorted.n_components_)
            pca_sorted = pca_sorted.transform(areas_sorted_rem)
            clusters_new = KMeans(n_clusters = 2, n_init = 100).fit(pca_sorted).labels_
            clusters_new = order_clusters(clusters_new)
            
            if all(clusters_new == clusters_old):
                
                print('same clusters')
        
            silhouette_sorted.append(silhouette_score(pca_sorted, clusters_new))
            jaccard_sorted.append(jaccard_score(compare_clinical, clusters_new))
            r2_sorted.append(scipy.stats.linregress(pca_sorted[:,0], clinical_classifications['all'].values).rvalue**2)
            
            try:
                os.mkdir(f'{directory2}removingproteins/')
            except FileExistsError:
                pass
            
            
            if scipy.stats.linregress(pca_sorted[:,0], clinical_classifications['all'].values).slope < 0:   # cluster 0 o de menos síntomas
                
                pca_sorted[:,0] = - pca_sorted[:,0]
            
            if np.shape(pca_sorted)[1] > 1:
                    
                fig = plt.figure(); ax = fig.add_subplot()
                ax.scatter(pca_sorted[:,0], pca_sorted[:,1], 
                           color = [clustercolors[cl] for cl in clusters['cluster']], edgecolor = 'k')
                ax.set_xlabel('PC1'); ax.set_ylabel('PC2')
                ax.set_title(f"({i} removed proteins)")
                fig.savefig(f'{directory2}removingproteins/pc1pc2_removing{i}proteins.svg', dpi = 300)
                plt.close(fig)
            
            fig = plt.figure(); ax = fig.add_subplot()
            ax.scatter(pca_sorted[:,0], clinical_classifications['all'].values, 
                       color = [clustercolors[cl] for cl in clusters['cluster']], edgecolor = 'k')
            ax.set_xlabel('PC1'); ax.set_ylabel('Sum of symptoms (all)')
            ax.set_title(f"({i} removed proteins, r$^2$ = {scipy.stats.linregress(pca_sorted[:,0], clinical_classifications['all'].values).rvalue**2:.3f})")
            fig.savefig(f'{directory2}removingproteins/pc1allsymptoms_removing{i}proteins.svg', dpi = 300)
            plt.close(fig)
            
            clusters_old = np.copy(clusters_new)
        
    fig = plt.figure(); ax = fig.add_subplot()
    ax.scatter(np.arange(0, len(areas_sorted.columns.values), 1), silhouette_sorted, label = 'Silhouette', marker = '.')
    ax.scatter(np.arange(0, len(areas_sorted.columns.values), 1), jaccard_sorted, label = 'Jaccard', marker = '.')
    ax.scatter(np.arange(0, len(areas_sorted.columns.values), 1), r2_sorted, label = 'r$^2$', marker = '.')
    ax.set_xlabel('Removed proteins')
    
    ax.legend(loc = 'best')
    
    ax.set_xticks(ticks = np.arange(0, np.shape(areas_sorted)[1], 1), labels = ['None'] + list(np.flip(areas_sorted.columns.values)[:-1]), 
                  rotation = 90, fontsize = 5)
    x_labels = ax.get_xticklabels()
    [x_labels[i].set_weight('bold') for i in range(len(x_labels)) if i % 2 == 0]
    ax.set_xticklabels(x_labels)
    
    fig.tight_layout()
    
    return silhouette_sorted, jaccard_sorted, r2_sorted, fig


'''  
END OF FUNCTIONS DEFINITION
'''






''' 
select:
- the type of sample to analyze (P: pellet, S: supernatant)
- the library name (2022, 2024)
- the reduced variable (True: keep only selected proteins, False: use all proteins)
- colors for clusters
- cluster names
'''
sample_type   = 'S'
libreria      = '2024'
reduced       = True

clustercolors = ['steelblue', 'peru', 'green', 'purple']
clusternames  = ['asymp', 'symp']



'''
DEFINE NECESSARY VARIABLES
define the routes for the v2022 and v2024 libraries that contain the areas files (directory)
areas file names must also be defined (file_areas)
data directory is defined as a directory named DATA in the project route
a second directory (directory2) is created or the output of the analysis inside the library directory
'''
PROJECT_ROUTE = './'

directories = {'2022': f'{PROJECT_ROUTE}22014_SWATH libreria COVID+SARS 2022/',
               '2024': f'{PROJECT_ROUTE}22014_SWATH libreria COVID+SARS Junio 2024/'}

files_areas = {'2022': f'{directories[libreria]}24014_areas normalizadas nueva clisificacion Junio 2024.xls',
               '2024': f'{directories[libreria]}24014 areas normalizadas nueva libreria SARS 18062024.xls'}

directory  = directories[libreria]
file_areas = files_areas[libreria]

data_route = f'{PROJECT_ROUTE}DATA/'
directory2 = f'{PROJECT_ROUTE}_TESIS_plots_svg/plots_{libreria}_{sample_type}_reduced/' if reduced else f'{PROJECT_ROUTE}_TESIS_plots_svg/plots_{libreria}_{sample_type}/'

os.makedirs(directory2, exist_ok=True)



''' 
READ THE DATA FILES 
- areas file: areas_raw
- clinical data file: sergas
- clinical data file (with 0,1): clinical
- clasification from previous work file: classification_prot1
- vaccination data file (if patients were vaccinated at blood extraction): vaccination_01 (0: not vaccinated, 1: vaccinated)
Then update indices to have them in the same format and order.
'''

areas_raw            = pd.read_excel(file_areas, index_col = 0)
clinical             = pd.read_csv(f'{data_route}datos_clinicos_10.csv', index_col = 0)
classification_prot1 = pd.read_csv(f'{data_route}clusters_S_proteomica1_v2020.csv', index_col = 0)
sergas               = pd.read_excel(f'{data_route}LIPID-CHUS_Anonimizado.xlsx')
vaccination_01       = pd.read_csv(f'{data_route}vaccination_01.csv', index_col = 0)

classification_prot1.index = [i.astype(str) for i in classification_prot1.index.values]

sgs_paciente = np.array([str(int((ts.split(sep='_')[-1]))) for ts in sergas['Patient code']])
sergas.index = sgs_paciente
sergas       = sergas.loc[classification_prot1.index.values]

clinical.index = [i.astype(str) for i in clinical.index.values]
clinical = clinical.loc[classification_prot1.index.values]

patient_indices = [f'{i}_{sample_type}' for i in clinical.index.values]

for file in [clinical, sergas, classification_prot1]:
    file.index = patient_indices

# add a vaccination column to the clinical data
clinical['Vaccination'] = vaccination_01['state'].values 


# define two lists for class 0 and 1 from classification v2020
class0 = list(classification_prot1[classification_prot1['cluster'] == 0].index.values)
class1 = list(classification_prot1[classification_prot1['cluster'] == 1].index.values)


''' 
MODIFY THE AREAS FORMAT
Edit the format of the raw areas file using the process_raw_areas function
Print the area data shape before and after reformating
'''
print(f'Shape areas file (raw): {np.shape(areas_raw.T)}')
areas_raw, ig = process_raw_areas(areas_raw, patient_indices)
print(f'Shape areas file (deleted RRR and selecting patients with clinical symptoms): {np.shape(areas_raw)}')



'''
VOLCANO PLOT
Make a copy of the processed data and add a class column
this new data frame is subjected to the calculate_volcano function
calculate the volcano imposing T-test, MU and analyze the results
at the end we save the volcano plot forcing to use the T-test
'''
df = areas_raw.copy()
df['class'] = classification_prot1.values
volcano_plot          = calculate_volcano(df)[0]
volcano_plot_check    = calculate_volcano(df, check = True)[0]
volcano_plot_MU       = calculate_volcano(df, 'MU')[0]
volcano_plot_MU_check = calculate_volcano(df, 'MU', check = True)[0]
volcano_plot.to_csv(f'{directory2}volcano_plot.csv')



'''
build a general plot comparing the four volcano plots created, using the 
two statistical tests
'''
fig = plt.figure(figsize = (10,10))
ax1 = fig.add_subplot(221); ax2 = fig.add_subplot(222)
ax3 = fig.add_subplot(223); ax4 = fig.add_subplot(224)

plot_volcano(volcano_plot, title = 'T-test', ax = ax1)
plot_volcano(volcano_plot_MU, title = 'Mann Whitney', ax = ax2)
plot_volcano(volcano_plot_check, title = 'T-test (only valid)', ax = ax3)
plot_volcano(volcano_plot_MU_check, title = 'Mann Whitney (only valid)', ax = ax4)

fig.suptitle(f'{sample_type}S to {sample_type}A', fontsize = 20)
fig.tight_layout()
fig.savefig(f'{directory2}statistics_volcano.svg', dpi = 300)



'''
OVEREXPRESSED AND SUBEXPRESSED PROTEINS
build a list of the overexpress and subexpressed proteins in class 1 (S) compared to class 0 (A)
'''
lista_sub_sobre = pd.DataFrame(volcano_plot[['FC', 'p-values']])
lista_sub_sobre = lista_sub_sobre[lista_sub_sobre['p-values'] < 0.05]

sub  = lista_sub_sobre.loc[lista_sub_sobre['FC'][lista_sub_sobre['FC'] < 1/1.5].index.values]
over = lista_sub_sobre.loc[lista_sub_sobre['FC'][lista_sub_sobre['FC'] > 1.5].index.values]

print(f'{sample_type}, libería {libreria}')
print(f'Subexpressed proteins: {sub.index.values}')
print(f'Overexpressed proteins: {over.index.values}')




'''
SCALE THE DATA
- Use a Variance Threshold of 0 to delete those proteins with 0 variance 
    (proteins that give the same value for all samples)
- Use a Power Transformer to make the proteins distribution more likely to be a normal distribution
Build a function that uses the variance threshold and power transformer trained with this dataset
to scale other independant data set (new patients) with the same proteins. 
'''
var_thres = VarianceThreshold(threshold = 0).fit(areas_raw)
areas     = pd.DataFrame(var_thres.transform(areas_raw), index = areas_raw.index.values, 
                                columns = var_thres.get_feature_names_out())
pt        = PowerTransformer().fit(areas)
areas     = pd.DataFrame(pt.transform(areas), columns = areas.columns, index = areas.index.values)

print(f'Shape areas file (after scaling and variance threshold): {np.shape(areas)}')

def escalar_datos(areas_raw):
    
    areas = pd.DataFrame(var_thres.transform(areas_raw), index = areas_raw.index.values,
                         columns = var_thres.get_feature_names_out())
    areas = pd.DataFrame(pt.transform(areas), columns = areas.columns, index = areas.index.values)
    
    return areas



'''
Build a data frame with the clinical classifications according to
- symptoms on the extraction day
- symptoms 90 days after the extraction
- symptoms 9 months after the extraction
'''
ext = [i for i in clinical.columns if i.endswith('_ext')]
d90 = [i for i in clinical.columns if i.endswith('_90d')]
m9  = [i for i in clinical.columns if i.endswith('_9m')]

clinical_classifications = pd.DataFrame(np.array([clinical[ext].T.sum(), clinical[d90].T.sum(), clinical[m9].T.sum(), clinical.T.sum()]).T, 
                                        columns = ['ext', '90d', '9m', 'all'], index = areas_raw.index.values)

# we use symptoms in the moment of the blood extraction for comparison and performance evaluation
compare_clinical = clinical_classifications['ext'].apply(lambda x: dividir_sintomas(x, limit = 1))




'''
PRINCIPAL COMPONENT ANALYSIS
if reduced, try to reduce the number of dimensions by feature selection
instead of principal component analysis
the criterion to follow is: delete recursively the protein that its absence
raises the best Jaccard score between clusters and symptoms (ext)
Then, after feature selection, do PCA and save PC1 in an independant data frame
'''

if reduced == True:
  
    if sample_type == 'S':
    
        # use_columns = find_max_jaccard(areas)
        # use_columns = ['Q8N5F4']
        # in this case keeping all proteins raise better results
        # order proteins by higher contribution to PC1
        pca = PCA().fit(areas)
        higher_contribution_protein = areas.columns[np.argmax(pca.components_[0])]
        areas = pd.DataFrame(areas[higher_contribution_protein])
        
    elif sample_type == 'P':
        
        # use_columns = find_max_jaccard(areas)
        # usando o mas_jaccard obtense: ['A0A0U1WHG0', 'G1SG72', 'A0A7R6WCE7', 'A0A5C2G2G8']
        # observando "a man" as áreas destas proteinas e os sintomas identificamos que G1SG72 ten 
        # unha clara asociación cos síntomas
        if 'G1SG72' in areas.columns:
            use_columns = ['G1SG72']
        else:
            use_columns = find_max_jaccard(areas)
        areas = areas[use_columns]

pca            = PCA().fit(areas)
areas_pca      = pca.transform(areas)
pca_components = pca.components_[0]
pc1            = pd.DataFrame(areas_pca[:,0], index = areas.index.values, columns = ['PC1'])



''' PLOT: explained variance ratio '''
fig = plt.figure(); ax = fig.add_subplot()
ax.scatter(np.arange(1, len(pca.explained_variance_ratio_) + 1, 1), 
           np.cumsum(pca.explained_variance_ratio_), 
           edgecolor = 'k', linewidth = 0.3, color = 'purple', alpha = 0.7)
ax.set_xlabel('Number of principal components')
ax.set_ylabel('Explained variance ratio')
ax.grid(True, alpha = 0.1)
fig.savefig(f'{directory2}explainedvariance.svg', dpi = 400)
plt.close(fig)


''' PLOT: contribution to PC1 '''
fig = plt.figure(); ax = fig.add_subplot()
sns.barplot(pca.components_[0], ax = ax, edgecolor = 'k', linewidth = 0.5, color = 'purple', alpha = 0.7)
ax.set_xlim(-0.5, np.shape(pca.components_)[1] - 0.5)
ax.set_xticks(ticks = np.arange(0, np.shape(pca.components_)[1], 1), labels = areas.columns.values, rotation = 90, fontsize = 7)
ax.set_ylabel('Contribution to PC1')
x_labels = ax.get_xticklabels()
[x_labels[i].set_weight('bold') for i in range(len(x_labels)) if i%2 == 0]
ax.set_xticklabels(x_labels)
ax.grid(True, alpha = 0.1)
fig.tight_layout()
fig.savefig(f'{directory2}contributionPC1.svg', dpi = 300)




'''
CLUSTERING
Use the KMeans algorithm to identify two clusters within the PCs space
Use all PC components is safe because most of them are negligible 
(very small explained variance contribution)
Evaluate the Silhouette score using 2,3,4,5 clusters, to find the optimal number
Repeat the KMeans clustering with the optimal number of clusters
Save the clusters identification in a CSV file
Build a list (clusters_01) containing the list of samples in cluster 0 and 1, respectively
'''
n_clusters_list    = np.arange(2, 5, 1)
silhouette_list    = [silhouette_score(areas_pca, KMeans(n_clusters = n_clusters, n_init = 1000, max_iter = 500, random_state = 44).fit(areas_pca).labels_) for n_clusters in n_clusters_list]
n_clusters_optimal = n_clusters_list[np.argmax(silhouette_list)]

km = KMeans(n_clusters = 2, n_init = 1000, max_iter = 3000, random_state = 44).fit(areas)

clusters = order_clusters(km.labels_)
clusters = pd.DataFrame(clusters, columns = ['cluster'])
clusters.index = areas.index.values
clusters.to_csv(f'{directory2}clusters.csv')

# build a list with two elements, containing the list of samples
# in cluster 0 and 1, respectively
clusters_01 = [clusters[clusters['cluster'] == cl].index.values for cl in set(clusters.squeeze().values)]



''' PLOT: silhouette scores '''
fig = plt.figure(); ax = fig.add_subplot()
ax.scatter(n_clusters_list, silhouette_list)
ax.set_ylabel('Silhouette score')
ax.set_xlabel('Number of clusters')
fig.savefig(f'{directory2}silhouette.svg', dpi = 400)
plt.close(fig)
print(f'Optimal number of clusters is {n_clusters_optimal} with a silhouette coeff of {np.max(silhouette_list):.3f}')




''' 
BUILD THE SCATTER PLOT PC1 - PC2 
Use a try-except method in case no PCA was performed (for pellet v2022, G1SG72)
'''

try: # PC1 - PC2
    
    ' PLOT: scatter plot PC1-PC2 simplified '
    font = 30
    fig = plt.figure(); ax = fig.add_subplot()
    ax.scatter(areas_pca[:,0], areas_pca[:,1], 
               color = [clustercolors[cl] for cl in clusters['cluster'].values], 
               edgecolor = 'k', linewidths = 0.4, s = 100)
    ax.set_xlabel('PC1', fontsize = font); ax.set_ylabel('PC2', fontsize = font)
    ax.set_xticks([]); ax.set_yticks([])
    fig.savefig(f'{directory2}scatterpc1pc2_simplified.svg', dpi = 700)

    ' PLOT: scatter plot PC1-PC2 detailed '
    fig = plt.figure(); ax = fig.add_subplot()
    ax.scatter(areas_pca[:,0], areas_pca[:,1], color = [clustercolors[cl] for cl in clusters['cluster'].values], edgecolor = 'k', linewidths = 0.4)
    texts = [ax.text(x = pc1['PC1'].iloc[i], y = areas_pca[:,1][i] + 0.02, s = pc1.index.values[i], fontsize = 8) for i in range(len(pc1))]
    adjust_text(texts, arrowprops = dict(arrowstyle='-', color = 'k'))
    ax.set_xlabel('PC1'); ax.set_ylabel('PC2')
    fig.savefig(f'{directory2}scatterpc1pc2.svg', dpi = 300)
    
    ' PLOT: scatter plot PC1-PC2 more detailed '
    fig = plt.figure(figsize = (8, 4)); ax = fig.add_subplot()
    ax.scatter(areas_pca[:,0], areas_pca[:,1], color = [cm.summer(value) for value in clinical['Num_SI_sintomas'].values / np.max(clinical['Num_SI_sintomas'].values)], 
               edgecolor = 'k', linewidths = 0.5, s = 30)
    xlim = ax.get_xlim(); ylim = ax.get_ylim()
    ax.fill_betweenx(y = np.linspace(ylim[0], ylim[1], 10), x1 = xlim[0], x2 = (xlim[1] + xlim[0]) / 2,
                    color = clustercolors[1], alpha = 0.15)
    ax.fill_betweenx(y = np.linspace(ylim[0], ylim[1], 10), x2 = xlim[1], x1 = (xlim[1] + xlim[0]) / 2,
                    color = clustercolors[0], alpha = 0.15)
    ax.set_xlim(xlim); ax.set_ylim(ylim)
    ax.scatter(areas_pca[:,0], areas_pca[:,1], color = [cm.summer(value) for value in clinical['Num_SI_sintomas'].values / np.max(clinical['Num_SI_sintomas'].values)], 
               edgecolor = 'k', linewidths = 0.5, s = 30)
    plt.colorbar(mappable = cm.ScalarMappable(cmap = cm.summer), ax = ax, fraction = 0.05, label = 'Number of clinical variables (ascending)', ticks = [])
    texts = [ax.text(x = pc1['PC1'].iloc[i], y = areas_pca[:,1][i] + 0.02, s = pc1.index.values[i], fontsize = 8) for i in range(len(pc1))]
    adjust_text(texts, arrowprops = dict(arrowstyle='-', color = 'k'))
    ax.set_xlabel('PC1'); ax.set_ylabel('PC2')
    ax.set_title('Mostly symptomatic                       Mostly asymptomatic')
    fig.tight_layout()
    fig.savefig(f'{directory2}scatterpc1pc2_.svg', dpi = 300)

    
except: # if no PC1-PC2: take the protein area directly
    
    ' PLOT: scatter plot using the protein area '
    fig = plt.figure(figsize = (10, 2.5)); ax = fig.add_subplot()
    
    ax.scatter(areas[areas.columns.values[0]].values, 
               areas[areas.columns.values[0]].values*0, 
               color = [clustercolors[cl] for cl in clusters['cluster'].values], edgecolor = 'k', linewidths = 0.4)
    
    texts = [ax.text(x = areas[areas.columns.values[0]].iloc[i], y = areas[areas.columns.values[0]].values[i]*0, s = areas.index.values[i], fontsize = 8) for i in range(len(areas))]
    adjust_text(texts, arrowprops = dict(arrowstyle='-', color = 'k'))
    ax.set_yticks([], [])
    ax.spines[['top', 'left', 'right']].set_visible(False)
    ax.spines[['bottom']].set_position('center')
    ax.set_xlabel(f'{areas.columns.values[0]} area', weight = 'bold')
    ax.tick_params(length = 20, which = 'major')
    ax.tick_params(length = 8, which = 'minor')
    ax.tick_params(width = 1.5, direction = 'inout', pad = 10, which = 'both')
    ax.minorticks_on()
    fig.tight_layout()
    fig.savefig(f'{directory2}scatterpc1pc2.svg', dpi = 300)




''' 
SEVERITY METRIC CALCULATION 
Calculate first Angel definition of the severity metric.
Then check the linear correlation between S and PC1, if R2 > 0.99,
then use PC1 for easier interpretability.
Check S has the correct sign: higher S, higher number of symptoms
'''
S, cluster_means, pesos_comp = severidade_angel(areas, clusters, pesos_comp = None)
dfresults = clinical_classifications.copy()
dfresults['S'] = S
dfresults['PC1'] = areas_pca[:,0]
dfresults.to_csv(f'{directory2}results_{sample_type}.csv')

# check linear correlation S-PC1
if scipy.stats.linregress(S.values, pc1['PC1'].values).rvalue**2 > 0.99:   # se PC1 se pode tomar como S
    
    pesos_comp = pca_components
    
    for patient in S.index.values:
        
        S.loc[patient] = pc1['PC1'].loc[patient]

# check S sign
if scipy.stats.linregress(S, clinical_classifications['all'].values).slope < 0:   # cluster 0 o de menos síntomas
    
     S = - S
     pesos_comp = - pesos_comp




' PLOT: violin for symptoms groups (ext, 90d, 9m, all) '
for column in clinical_classifications.columns:
    
    if column == 'all':
        limit = 5
        
    else:
        limit = 1
    
    violin_s_classifications(column, S) # not binary
    violin_s_classifications(column, S, binary = True, limit = limit)


' PLOT: relation between PC1 and severity metric '
fig = plt.figure(); ax = fig.add_subplot()
ax.scatter(areas_pca[:,0], S, color = [clustercolors[cl] for cl in clusters['cluster'].values], edgecolor = 'k', linewidths = 0.4)
ax.set_xlabel('PC1'); ax.set_ylabel('S')
texts = [ax.text(x = pc1['PC1'].iloc[i], y = S.iloc[i] + 0.02, s = pc1.index.values[i], fontsize = 8) for i in range(len(pc1))]
adjust_text(texts, arrowprops = dict(arrowstyle='-', color = 'k'), avoid_self = True)
ax.set_title(f"Linear correlation between PC1 and S (r$^2$={scipy.stats.linregress(S.values, pc1['PC1'].values).rvalue**2:.3f})")
fig.savefig(f'{directory2}PC1_S.svg', dpi = 400)


' PLOT: clinical variables heatmap sorted by S ' 
fig, ax = mapacores_sintomasS(clinical, S)
fig.savefig(f'{directory2}colormap.svg', dpi = 400)



'''
PLOT: BUILD THE SUBPLOT FIGURES CONTAINING:
- normalized areas heatmap (center axis, heatmap, ax)
- protein contribution to S (top axis, line, ax3)
- Fold Change values for each protein (top axis, dots, ax3)
- average protein area over all patients (right axis, bars, ax2)
- S values for each patient (right axis, dots, ax2twinx)
- Color bar for normalized protein concentration (small right axis, ax4)
'''
# build a data frame with the areas sroted by protein contribution to S
areas_sorted = areas[areas.columns.values[np.flip(np.argsort(abs(pesos_comp)))]]
areas_sorted.to_csv(f'{directory2}proteins_sortedby_contribution.csv')

if not reduced: # complete and detailed figure with subplots
    
    # Create figure and axes
    fig = plt.figure(figsize = (7, 7))
    ax  = fig.add_subplot(4, 4, (5, 15))
    ax2 = fig.add_subplot(4, 4, (8, 16), sharey = ax); ax2twin = ax2.twiny()
    ax3 = fig.add_subplot(4, 4, (1, 3), sharex = ax); ax3twin = ax3.twinx()
    ax4 = fig.add_subplot(4, 55, (55*2, 55*4))
    

    ' PLOT: center axis, areas heatmap sorting pateints by S and proteins by contribution to S '
    ax.pcolor(areas_sorted.loc[S.sort_values(ascending = True).index.values], cmap = 'Purples')
    
    ax.set_xticks(ticks = np.arange(0.5, np.shape(areas_sorted)[1] + 0.5, 1), labels = areas_sorted.columns, rotation = 90, fontsize = 5)
    x_labels = ax.get_xticklabels()
    [x_labels[i].set_weight('bold') for i in range(len(x_labels)) if i % 2 == 0]
    ax.set_xticklabels(x_labels)
    
    ax.set_yticks(ticks = np.arange(0.5, np.shape(areas_sorted)[0] + 0.5, 1), labels = S.sort_values(ascending = True).index.values, fontsize = 5)
    y_labels = ax.get_yticklabels()
    [y_labels[i].set_weight('bold') for i in range(len(y_labels)) if i % 2 == 0]
    ax.set_yticklabels(y_labels)
    
    ax.set_ylabel('Patient code (ordered ascending by S)\n(Asymptomatic)                      (Symptomatic)')
    ax.set_xlabel('Proteins (ordered by descending contribution to S)')
    
    ' PLOT: right axis, average protein concentration over all patients and S values '
    # normalize the average protein values by its minimum value, all positive values
    mean_proteins        = np.flip(areas_sorted.loc[S.sort_values(ascending = False).index.values].T.mean().values)
    minimo_mean_proteins = np.min(mean_proteins)
    maximo_mean_proteins = np.max(mean_proteins)
    mean_proteins        = mean_proteins - minimo_mean_proteins
    
    ax2.barh(y = np.arange(0, np.shape(areas_sorted)[0], 1) + 0.5, 
             width = mean_proteins,
             color = cm.Purples(mean_proteins), edgecolor = 'midnightblue', linewidth = 0.5, alpha = 0.9)
    
    edgecolors = ['white', 'k']
    ax2twin.scatter(S.loc[S.sort_values(ascending = True).index.values], np.arange(np.shape(areas_sorted)[0]) + 0.5,
                    color = 'lightblue', marker = '.', label = 'S', 
                    edgecolor = [edgecolors[int(t)] for t in np.sign(S.loc[S.sort_values(ascending = True).index.values]).replace(-1, 0).values], 
                    linewidth = 0.4, s = 50)
    
    ax2.set_xticks(ticks = [0.04, abs(minimo_mean_proteins), np.max(mean_proteins)])
    ax2.set_xticklabels(labels = [f'{minimo_mean_proteins:.2f}', '0', f'{maximo_mean_proteins:.2f}'], 
                        rotation = 90, fontsize = 3.5, horizontalalignment = 'left')
    
    ax2.spines[['top', 'bottom', 'right']].set_visible(False)
    ax2.yaxis.set_visible(False)
    ax2.set_ylim(0, len(areas_sorted.index.values))
    ax2.set_xlabel('Average protein\narea for each patient\n(normalized values)')    
    ax2.tick_params(labelsize = 6.5, size = 4)
    ax2.set_xlim(ax2.get_xlim()[0], ax2.get_xlim()[1]*1.1)

    ax2twin.set_xlabel('S', fontsize = 8)
    ax2twin.legend(loc = 'upper center')
    ax2twin.spines[['top', 'bottom', 'right']].set_visible(False)
    ax2twin.tick_params(labelsize = 7, size = 4, rotation = 0)
    ax2twin.set_ylim(0, len(areas_sorted.index.values))
    ax2twin.set_xlim(ax2twin.get_xlim()[0], ax2twin.get_xlim()[1]*1.35)
    
    
    ' PLOT: top axis, protein contribution to S and Fold Change value '
    ax3.fill_between(x = np.arange(0.5, len(pesos_comp) + 0.5, 1), 
                     y1 = pca_components*0, 
                     y2 = np.flip(np.sort(abs(pesos_comp))) * np.sign(pesos_comp[np.flip(np.argsort(abs(pesos_comp)))]), 
                     color = 'lightblue')
    
    ax3.plot(np.arange(0.5, len(pesos_comp) + 0.5, 1), 
             np.flip(np.sort(abs(pesos_comp))) * np.sign(pesos_comp[np.flip(np.argsort(abs(pesos_comp)))]), 
             color = 'midnightblue', alpha = 0.7)
    
    ax3.set_xlim(0.5, len(pesos_comp))
    ax3.spines[['top',  'bottom', 'left', 'right']].set_visible(False)
    ax3.set_ylabel('  Contribution to S')
    ax3.xaxis.set_visible(False)
    ax3.set_xlim(0, len(areas_sorted.index.values))
    
    ax3twin.scatter(np.arange(0.5, len(pesos_comp) + 0.5, 1), 
                    volcano_plot['FC'].loc[areas.columns.values[np.flip(np.argsort(abs(pesos_comp)))]],
                    marker = '.', color = 'midnightblue', label = 'FC')
    
    ax3twin.legend(loc = 'upper center')
    ax3twin.xaxis.set_visible(False)
    ax3twin.set_xlim(0, len(areas_sorted.index.values))
    ax3twin.spines[['top',  'bottom', 'left', 'right']].set_visible(False)
    ax3twin.tick_params(labelsize = 7, size = 4)
    ax3twin.set_ylabel('Fold Change\n(Symp/Asymp)', fontsize = 8)
    
    ' PLOT: Right small axis, color bar ' 
    plt.colorbar(mappable = cm.ScalarMappable(cmap = cm.Purples), ax = ax, cax = ax4)
    ax4.set_ylabel('Protein area')
    ax4.set_yticks(ticks = [], labels = [])
    
    fig.tight_layout()
    fig.subplots_adjust(top=0.985,bottom=0.12,left=0.115,right=0.97,hspace=0.02,wspace=0.005)
    ax.set_xlim(0, len(pesos_comp) )
    fig.savefig(f'{directory2}protein_colormap_option2.svg', dpi = 500)



else: # simplified figure for one single protein
    
    fig = plt.figure(figsize = (3, 7))
    ax2 = fig.add_subplot(1, 6, (1, 5))
    ax4 = fig.add_subplot(1, 6, 6)
    
    ' PLOT: right axis, average protein concentration over all patients and S values '
    mean_proteins = np.flip(areas_sorted.loc[S.sort_values(ascending = False).index.values].T.mean().values)
    minimo_mean_proteins = np.min(mean_proteins)
    maximo_mean_proteins = np.max(mean_proteins)
    mean_proteins = mean_proteins - minimo_mean_proteins

    ax2.set_ylabel('Patient code (ordered ascending by S)\n(Asymptomatic)                      (Symptomatic)')
    
    ax2.barh(y = np.arange(0, np.shape(areas_sorted)[0], 1) + 0.5, 
             width = mean_proteins,
             color = cm.Purples(mean_proteins), edgecolor = 'midnightblue', linewidth = 0.5, alpha = 0.9)
    
    edgecolors = ['white', 'k']
    
    ax2.scatter(S.loc[S.sort_values(ascending = True).index.values] - minimo_mean_proteins, 
                    np.arange(np.shape(areas_sorted)[0]) + 0.5,
                    color = 'lightblue', marker = '.', label = 'S', 
                    edgecolor = [edgecolors[int(t)] for t in np.sign(S.loc[S.sort_values(ascending = True).index.values]).replace(-1, 0).values], 
                    linewidth = 0.4, s = 50)

    ax2.set_xticks(ticks = [0.04, abs(minimo_mean_proteins), np.max(mean_proteins)])
    ax2.set_xticklabels(labels = [f'{minimo_mean_proteins:.2f}', '0', f'{maximo_mean_proteins:.2f}'], 
                        rotation = 90, fontsize = 3.5, horizontalalignment = 'left')
    
    ax2.spines[['top', 'bottom', 'right']].set_visible(False)
    ax2.yaxis.set_visible(False)
    ax2.set_ylim(0, len(areas_sorted.index.values))
    ax2.set_xlabel(f'{areas.columns.values[0]}')    
    ax2.tick_params(labelsize = 6.5, size = 4)
    ax2.set_xlim(ax2.get_xlim()[0], ax2.get_xlim()[1]*1.1)
    ax2.legend(loc = 'lower right')

    ' PLOT: Right small axis, color bar ' 
    plt.colorbar(mappable = cm.ScalarMappable(cmap = cm.Purples), ax = ax2, cax = ax4)
    ax4.set_ylabel('Protein area')
    ax4.set_yticks(ticks = [], labels = [])
    
    fig.tight_layout()
    fig.savefig(f'{directory2}protein_colormap_option2.svg', dpi = 500)


 
'''
PLOT: Average protein area for each cluster and proteins sorted by contribution to S
'''
fig = plt.figure(); ax = fig.add_subplot()

[ax.bar(np.arange(0, np.shape(areas_sorted)[1], 1), areas_sorted.loc[clusters_01[cl]].mean(), color = clustercolors[cl], alpha = 0.2) for cl in set(clusters['cluster'])]
[ax.scatter(np.arange(0, np.shape(areas_sorted)[1], 1), areas_sorted.loc[clusters_01[cl]].mean(), color = clustercolors[cl], linewidth = 0.5, edgecolor = 'k') 
 for cl in set(clusters['cluster'])]
ax.set_ylabel('Average protein area for each cluster\n(scaled values)')

ax.set_xticks(ticks = np.arange(0, np.shape(areas_sorted)[1], 1), labels = areas_sorted.columns, rotation = 90, fontsize = 5)
x_labels = ax.get_xticklabels()
[x_labels[i].set_weight('bold') for i in range(len(x_labels)) if i % 2 == 0]
ax.set_xticklabels(x_labels)
ax.set_xlim(-0.5, len(areas_sorted.columns) - 0.5)
ax.set_xlabel('Proteins (ordered by contribution to S)')

fig.tight_layout()
fig.savefig(f'{directory2}average_protarea.svg', dpi = 400)



'''
PLOT: scatter plot for sum of symptoms (in clinical classification) and PC1 / S
'''    
for classification in clinical_classifications.columns.values:
        
    ' PLOT: scatter plot for sum of symptoms (in clinical classification) and PC1 '
    fig = plt.figure(); ax = fig.add_subplot()
    ax.scatter(pc1, clinical_classifications[classification], color = [clustercolors[cl] for cl in clusters['cluster']], edgecolor = 'k')
    texts = [ax.text(x = pc1['PC1'].iloc[i], y = clinical_classifications[classification].iloc[i] + 0.02, s = pc1.index.values[i], fontsize = 7) for i in range(len(pc1))]
    adjust_text(texts, arrowprops = dict(arrowstyle='-', color = 'k'), avoid_self = True)
    ax.set_title(f"r$^2$={scipy.stats.linregress(pc1['PC1'].values, clinical_classifications[classification].values).rvalue**2:.3f}")
    ax.set_xlabel('PC1'); ax.set_ylabel(f'Sum of Symptoms ({classification})')
    fig.savefig(f'{directory2}PC1_symptoms_{classification}.svg', dpi = 300)

    ' PLOT: scatter plot for sum of symptoms (in clinical classification) and S '
    fig = plt.figure(); ax = fig.add_subplot()
    ax.scatter(S.values, clinical_classifications[classification], color = [clustercolors[cl] for cl in clusters['cluster']], edgecolor = 'k')
    texts = [ax.text(x = S.iloc[i], y = clinical_classifications[classification].iloc[i] + 0.02, s = S.index.values[i], fontsize = 7) for i in range(len(pc1))]
    adjust_text(texts, arrowprops = dict(arrowstyle='-', color = 'k'), avoid_self = True)
    ax.set_title(f"r$^2$={scipy.stats.linregress(S.values, clinical_classifications[classification].values).rvalue**2:.3f}")
    ax.set_xlabel('S'); ax.set_ylabel(f'Sum of Symptoms ({classification})')
    fig.savefig(f'{directory2}S_symptoms_{classification}.svg', dpi = 300)

    



'''
PLOT: violin plot using different columns for hue:
sex, hospitalization, etc
'''
for hue_name in ['Sex', 'Hospitalization', 'Smoking', 'Severity scale', 
                 'Blood group (ABO system)', 'Blood group (Rh factor)', 'Clinical frailty scale', 
                 'Charlson Comorbidity Index', 'Age (years)']:
    
    hue = sergas[hue_name]

    if hue_name == 'Age (years)':
                
        fig = plt.figure(); ax = fig.add_subplot()
        ax.scatter(hue.values, pc1.values, 
                    color = cm.summer(clinical['Num_SI_sintomas'] / np.max(clinical['Num_SI_sintomas'])),
                    edgecolor = 'k', linewidth = 0.5)
        ax.set_xlabel(hue_name); ax.set_ylabel('PC1')
        fig.savefig(f"{directory2}{hue_name.replace(' ', '')}.svg")
        
    else:

        pc1_copy = pc1.copy()
        pc1_copy[hue_name] = hue.values

        order = set(sergas[hue_name])
        
        if hue_name == 'Severity scale':
            
            order = ['Asintomático', 'Leve', 'Moderado', 'Grave']

        fig = plt.figure(); ax = fig.add_subplot()
        sns.violinplot(data = pc1_copy, y = 'PC1', hue = hue_name, ax = ax, hue_order = order, palette = sns.color_palette("Set2"))
        ax.set_xticks([]); ax.legend(title = hue_name)
        fig.savefig(f"{directory2}{hue_name.replace(' ', '')}.svg")



'''
PLOT: 3D plot for linear regression protein - S
only for S samples not reduced
'''
if reduced == False and sample_type == 'S':
    
    # LATERAL VIEW
    from mpl_toolkits.mplot3d import Axes3D
    elev = 40; azim = -65; fontsize = 4
    
    fig = plt.figure(figsize = (10,10))
    ax = fig.add_subplot(projection = '3d')
    ax.view_init(elev = elev, azim = azim)
    ax.get_proj = lambda: np.dot(Axes3D.get_proj(ax), np.diag([0.6, 1.3, 0.6, 1]))
    ax.set_xlabel('Severity Metric (S)'); ax.set_zlabel('Protein area')
    
    for i in range(len(areas_sorted.columns)):
        
        regresion = scipy.stats.linregress(S.values, areas_sorted[areas_sorted.columns[i]].values)
        
        ax.plot(S.values, np.array([i]*len(S.values)), S.values * regresion.slope + regresion.intercept,
                color = cm.plasma(regresion.rvalue ** 2))
        
        ax.scatter(S.values, np.array([i]*len(S.values)), areas_sorted[areas_sorted.columns[i]].values, 
                   marker = '.', color = cm.plasma(regresion.rvalue ** 2),
                   alpha = 0.2, edgecolor = 'k', linewidth = 0.05)
    
    ax.tick_params(axis = 'x', direction = 'in', labelsize = 7, labelrotation = 90 - elev)
    ax.tick_params(axis = 'z', direction = 'in', labelsize = 7, labelrotation = 0)
    ax.set_ylim(0, i)

    lista_proteinas = [str(i) for i in np.copy(areas_sorted.columns.values)]
    ax.set_yticks(np.arange(i + 1), lista_proteinas[:i + 1], 
                  fontsize = fontsize, rotation = 0)
    
    ylabels = ax.get_yticklabels()
    [ylabels[i].set_weight('bold') for i in range(len(ylabels)) if i % 2 == 0]
    ax.set_yticklabels(ylabels, horizontalalignment = 'left')
    ax.grid(False)
    
    fig.savefig(f'{directory2}proteins_individually_lateral.svg', dpi = 700)
    
    
    # FRONT VIEW
    elev = 0.1; azim = -90; fontsize = 4
    
    fig = plt.figure(figsize = (10, 10))
    ax = fig.add_subplot(projection = '3d')
    ax.view_init(elev = elev, azim = azim)
    ax.get_proj = lambda: np.dot(Axes3D.get_proj(ax), np.diag([0.6, 1.3, 0.6, 1]))
    ax.set_xlabel('Severity Metric (S)', labelpad = 30); ax.set_zlabel('Protein area', labelpad = 10)
    
    for i in range(len(areas_sorted.columns)):
        
        regresion = scipy.stats.linregress(S.values, areas_sorted[areas_sorted.columns[i]].values)
        
        ax.plot(S.values, np.array([i]*len(S.values)), S.values * regresion.slope + regresion.intercept,
                color = cm.plasma(regresion.rvalue ** 2))
        
        ax.scatter(S.values, np.array([i]*len(S.values)), areas_sorted[areas_sorted.columns[i]].values, 
                   marker = '.', color = cm.plasma(regresion.rvalue ** 2),
                   alpha = 0.2, edgecolor = 'k', linewidth = 0.05)
        
    ax.tick_params(axis = 'x', direction = 'out', labelsize = 7, labelrotation = 90)
    ax.tick_params(axis = 'z', direction = 'in', labelsize = 7, labelrotation = 0)

    ax.set_yticks([], [])
    
    ax.grid(False)
    
    plt.colorbar(mappable = cm.ScalarMappable(cmap = cm.plasma), ax = ax, 
                  fraction = 0.02,
                  location = 'bottom', label = 'R$^2$ (linear regression)')

    fig.savefig(f'{directory2}proteins_individually_frente.svg', dpi = 1200)
    
    

'''
PLOT: scatter plot with linear regression protein - S
only for S samples not reduced
'''
if reduced == False and sample_type == 'S':
    
    fig = plt.figure(); ax = fig.add_subplot()
    
    for i in range(3): # for only first three proteins
        
        ax.set_xlabel('Severity Metric (S)'); ax.set_ylabel('Normalized protein area')
        
        regresion = scipy.stats.linregress(S.values, areas_sorted[areas_sorted.columns[i]].values)
        
        ax.plot(S.values, S.values * regresion.slope + regresion.intercept, linestyle = 'solid')
        
        ax.scatter(S.values, areas_sorted[areas_sorted.columns[i]].values, 
                   marker = 'o', label = f'{areas_sorted.columns[i]} (R$^2$={regresion.rvalue**2:.3f})',
                   alpha = 0.7, edgecolor = 'k', linewidth = 0.05, s = 40)
        
    ax.legend(loc = 'best', title = 'Protein')
    fig.savefig(f'{directory2}regression_S_individualproteins.svg', dpi = 300)
    
    rvalues = []
    
    for i in range(len(areas_sorted.columns)):
        
        regresion = scipy.stats.linregress(S.values, areas_sorted[areas_sorted.columns[i]].values)
        
        rvalues.append(regresion.rvalue ** 2)
        
    
    fig = plt.figure(figsize = (7,5)); ax = fig.add_subplot()
    
    ax.set_xlabel('Proteins (sorted by descending absolute contribution to S)'); ax.set_ylabel('R$^2$ (linear regression)')
    
    ax.bar(np.arange(len(areas_sorted.columns)), rvalues, color = 'olive', 
           align = 'center', edgecolor = 'k', linewidth = 0.3, alpha = 0.9)
    
    for i in range(len(areas_sorted.columns)):
        
        ax.text(x = np.array([i]), y = np.array([rvalues[i]]) + 0.01, s = f'{rvalues[i]:.3f}', 
                rotation = 90, fontsize = 7, horizontalalignment = 'center')
    
    ax.set_xticks(ticks = np.arange(len(areas_sorted.columns)), labels = areas_sorted.columns, 
                  rotation = 90, fontsize = 7)

    xticklabels = ax.get_xticklabels()
    
    [xticklabels[j].set_weight('bold') for j in range(len(xticklabels)) if j % 2 == 0]
    
    ax.set_xticklabels(xticklabels)
    
    ax.spines[["top", "right"]].set_visible(False)
    
    ax.set_xlim(-0.5, len(areas_sorted.columns)-0.5)
    ax.set_ylim(0, 1)

    fig.tight_layout()
    fig.savefig(f'{directory2}rvalues_S_individualproteins.svg', dpi = 300)


