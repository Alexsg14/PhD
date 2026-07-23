#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script standalone: ejecuta únicamente la sección del Volcano Plot
extraída de analise.py y guarda los resultados en volcano_results/
"""

import numpy as np
import pandas as pd
import scipy
import matplotlib.pyplot as plt
import os

from adjustText import adjust_text


# ─────────────────────────────────────────────
#  CONFIGURACIÓN  (igual que en analise.py)
# ─────────────────────────────────────────────
sample_type = 'S'       # 'S' supernatant  |  'P' pellet
libreria    = '2024'    # '2022' o '2024'

PROJECT_ROUTE = './'

directories = {
    '2022': f'{PROJECT_ROUTE}22014_SWATH libreria COVID+SARS 2022/',
    '2024': f'{PROJECT_ROUTE}22014_SWATH libreria COVID+SARS Junio 2024/',
}
files_areas = {
    '2022': f'{directories[libreria]}24014_areas normalizadas nueva clisificacion Junio 2024.xls',
    '2024': f'{directories[libreria]}24014 areas normalizadas nueva libreria SARS 18062024.xls',
}

directory  = directories[libreria]
file_areas = files_areas[libreria]
data_route = f'{PROJECT_ROUTE}DATA/'

# Carpeta de salida dedicada al volcano
output_dir = f'{PROJECT_ROUTE}volcano_results/{libreria}_{sample_type}/'
os.makedirs(output_dir, exist_ok=True)
print(f'📁  Resultados en: {output_dir}')


# ─────────────────────────────────────────────
#  FUNCIONES  (copiadas de analise.py)
# ─────────────────────────────────────────────

def process_raw_areas(areas_raw, patient_indices, add=[]):
    areas_proc = areas_raw.transpose()
    areas_proc = areas_proc[[col for col in areas_proc.columns if not col.startswith('RRR')]]
    ig = [col.split('|')[2].split('_')[0] for col in areas_proc.columns if 'IG' in col]
    areas_proc.columns = [i.split('|')[2].split('_')[0] for i in areas_proc.columns.values]
    areas_proc = areas_proc.loc[patient_indices + [f'{i}_{sample_type}' for i in add]]
    return areas_proc, ig


def calculate_volcano(df, test='t', check=False):
    class0 = df[df['class'] == 0].index.values
    class1 = df[df['class'] == 1].index.values

    volcano_plot = df.groupby(by='class').mean().T
    volcano_plot.columns = ['mean0', 'mean1']

    df = df.drop('class', axis=1)

    alpha         = 0.05
    ambas_normais = (
        [scipy.stats.shapiro(areas_raw[protein].loc[class0]).pvalue > alpha for protein in areas_raw.columns.values]
        and
        [scipy.stats.shapiro(areas_raw[protein].loc[class1]).pvalue > alpha for protein in areas_raw.columns.values]
    )
    equal_var     = [scipy.stats.levene(areas_raw[protein].loc[class0], areas_raw[protein].loc[class1]).pvalue > alpha
                     for protein in areas_raw.columns.values]
    ningun_valido = [not(norm) and not(eqv) for norm, eqv in zip(ambas_normais, equal_var)]

    resumo_validez = pd.DataFrame(
        np.array([ambas_normais, equal_var, ningun_valido]).T,
        index=volcano_plot.index.values,
        columns=['norm', 'eqvar', 'ningunvalido']
    )

    valido_ttest = resumo_validez[resumo_validez['norm'] == True].index.values
    valido_MU    = resumo_validez[resumo_validez['eqvar'] == True].index.values

    if test == 't':
        if check:
            volcano_plot = volcano_plot.loc[valido_ttest]
            df           = df[valido_ttest]
        volcano_plot['p-values'] = [
            scipy.stats.ttest_ind(a=df[p].loc[class0], b=df[p].loc[class1]).pvalue
            for p in df.columns.values
        ]

    elif test == 'MU':
        if check:
            volcano_plot = volcano_plot.loc[valido_MU]
            df           = df[valido_MU]
        volcano_plot['p-values'] = [
            scipy.stats.mannwhitneyu(df[p].loc[class0], df[p].loc[class1]).pvalue
            for p in df.columns.values
        ]

    volcano_plot['FC'] = volcano_plot['mean1'] / volcano_plot['mean0']
    return volcano_plot, resumo_validez


def plot_volcano(volcano, title=None, ax=None):
    if ax is None:
        fig = plt.figure()
        ax  = fig.add_subplot()

    fontsize = 12; s = 12; alpha = 0.65
    red    = '#D44242'; green  = '#37CC93'
    yellow = '#E0B84D'; cyan   = '#80CBEA'; blue = '#090AFF'

    volcano_sig    = volcano[volcano['p-values'] <= 0.05]
    volcano_nonsig = volcano[volcano['p-values'] >  0.05]

    ax.scatter(np.log2(volcano_nonsig['FC']), -np.log10(volcano_nonsig['p-values']),
               edgecolor='k', linewidth=0.4, s=s, color='gray', alpha=alpha)

    volcano_over  = volcano_sig[volcano_sig['FC'] >= 1.5]
    ax.scatter(np.log2(volcano_over['FC']), -np.log10(volcano_over['p-values']),
               edgecolor='k', linewidth=0.4, s=s, color=red, alpha=alpha)

    volcano_sub = volcano_sig[volcano_sig['FC'] <= 1 / 1.5]
    ax.scatter(np.log2(volcano_sub['FC']), -np.log10(volcano_sub['p-values']),
               edgecolor='k', linewidth=0.4, s=s, color=green, alpha=alpha)

    volcano_below = volcano_sig[volcano_sig['FC'] < 1.5]
    volcano_below = volcano_below[volcano_below['FC'] > 1 / 1.5]
    ax.scatter(np.log2(volcano_below['FC']), -np.log10(volcano_below['p-values']),
               edgecolor='k', linewidth=0.4, s=s, color=yellow, alpha=alpha)

    ax.tick_params(direction='in', labelsize=fontsize)
    ax.set_xlabel('Log$_2$(FC)',          fontsize=fontsize)
    ax.set_ylabel('-Log$_{10}$(p-value)', fontsize=fontsize)

    x_limits = {'P': (-3, 3), 'S': (-4, 4)}
    xlim = x_limits[sample_type]
    ax.set_xlim(xlim)
    ylim = ax.get_ylim(); ax.set_ylim(ylim)
    ax.hlines(y=-np.log10(0.05),   xmin=xlim[0], xmax=xlim[1], linestyle='--',  color='gray')
    ax.vlines(x=np.log2(1.5),      ymin=ylim[0], ymax=ylim[1], linestyle='-.',  color=cyan)
    ax.vlines(x=np.log2(1 / 1.5),  ymin=ylim[0], ymax=ylim[1], linestyle='-.',  color=cyan)
    ax.vlines(x=0,                  ymin=ylim[0], ymax=ylim[1], linestyle='--',  color=blue)

    texts = [
        ax.text(
            x=np.log2(volcano_sig['FC'])[i],
            y=-np.log10(volcano_sig['p-values'])[i],
            s=volcano_sig.index.values[i],
            fontsize=6.5
        )
        for i in range(len(volcano_sig.index.values))
    ]

    ax.set_title(title, fontsize=16)
    adjust_text(texts=texts, ax=ax, force_explode=(0.3, 1))

    return ax


# ─────────────────────────────────────────────
#  CARGA DE DATOS
# ─────────────────────────────────────────────
print('📂  Cargando datos...')

areas_raw            = pd.read_excel(file_areas, index_col=0)
clinical             = pd.read_csv(f'{data_route}datos_clinicos_10.csv', index_col=0)
classification_prot1 = pd.read_csv(f'{data_route}clusters_S_proteomica1_v2020.csv', index_col=0)

classification_prot1.index = [i.astype(str) for i in classification_prot1.index.values]
clinical.index             = [i.astype(str) for i in clinical.index.values]
clinical                   = clinical.loc[classification_prot1.index.values]

patient_indices = [f'{i}_{sample_type}' for i in clinical.index.values]
classification_prot1.index = patient_indices

areas_raw, ig = process_raw_areas(areas_raw, patient_indices)
print(f'✅  Areas cargadas: {areas_raw.shape}')


# ─────────────────────────────────────────────
#  VOLCANO PLOT
# ─────────────────────────────────────────────
print('🌋  Calculando volcano plots...')

df = areas_raw.copy()
df['class'] = classification_prot1.values

volcano_plot          = calculate_volcano(df)[0]
volcano_plot_check    = calculate_volcano(df, check=True)[0]
volcano_plot_MU       = calculate_volcano(df, 'MU')[0]
volcano_plot_MU_check = calculate_volcano(df, 'MU', check=True)[0]

# Guardar CSV con los datos del volcano (t-test, todos)
csv_path = f'{output_dir}volcano_data_ttest.csv'
volcano_plot.to_csv(csv_path)
print(f'💾  CSV guardado: {csv_path}')

# Figura 2x2 con los 4 volcano plots
fig = plt.figure(figsize=(10, 10))
ax1 = fig.add_subplot(221); ax2 = fig.add_subplot(222)
ax3 = fig.add_subplot(223); ax4 = fig.add_subplot(224)

plot_volcano(volcano_plot,          title='T-test',                    ax=ax1)
plot_volcano(volcano_plot_MU,       title='Mann Whitney',               ax=ax2)
plot_volcano(volcano_plot_check,    title='T-test (only valid)',        ax=ax3)
plot_volcano(volcano_plot_MU_check, title='Mann Whitney (only valid)',  ax=ax4)

fig.suptitle(f'{sample_type}S to {sample_type}A', fontsize=20)
fig.tight_layout()

fig_path = f'{output_dir}statistics_volcano.png'
fig.savefig(fig_path, dpi=300)
plt.close(fig)
print(f'🖼️   Figura guardada: {fig_path}')


# ─────────────────────────────────────────────
#  PROTEÍNAS SOBRE/SUB EXPRESADAS
# ─────────────────────────────────────────────
lista_sub_sobre = pd.DataFrame(volcano_plot[['FC', 'p-values']])
lista_sub_sobre = lista_sub_sobre[lista_sub_sobre['p-values'] < 0.05]

sub  = lista_sub_sobre[lista_sub_sobre['FC'] <  1 / 1.5]
over = lista_sub_sobre[lista_sub_sobre['FC'] >  1.5]

print(f'\n📊  {sample_type}, librería {libreria}')
print(f'   Subexpressed proteins ({len(sub)}):  {sub.index.values}')
print(f'   Overexpressed proteins ({len(over)}): {over.index.values}')

# Guardar listas como CSV
sub.to_csv(f'{output_dir}subexpressed_proteins.csv')
over.to_csv(f'{output_dir}overexpressed_proteins.csv')

print(f'\n✅  Todo guardado en: {output_dir}')
