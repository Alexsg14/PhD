#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificaciones de la normalización MLR:
1. Factor MLR por paciente y comparación entre grupos
2. Señal total antes de normalizar vs grupo
3. Regresión log2(FC_norm) vs log2(FC_sin_norm)
NO modifica archivos originales.
"""

import numpy as np
import pandas as pd
import scipy.stats
import matplotlib.pyplot as plt
import os

# ── Rutas ──
PROJECT = './'
junio = f'{PROJECT}22014_SWATH libreria COVID+SARS Junio 2024/'
data   = f'{PROJECT}DATA/'
outdir = f'{PROJECT}verificacion_MLR/'
os.makedirs(outdir, exist_ok=True)

sample_type = 'S'

# ── Leer datos ──
norm_raw    = pd.read_excel(f'{junio}24014 areas normalizadas nueva libreria SARS 18062024.xls', index_col=0)
sinnorm_raw = pd.read_excel(f'{junio}24014 areas sin normalizar nueva libreria SARS 18062024.xls', index_col=0)
for r in ['Sample ID', 'Group']:
    if r in sinnorm_raw.index:
        sinnorm_raw = sinnorm_raw.drop(r)

classification = pd.read_csv(f'{data}clusters_S_proteomica1_v2020.csv', index_col=0)
classification.index = [str(int(i)) for i in classification.index.values]
sergas = pd.read_excel(f'{data}LIPID-CHUS_Anonimizado.xlsx')

# ── Pacientes _S ──
patient_ids = [f'{i}_{sample_type}' for i in classification.index.values]
patient_ids = [p for p in patient_ids if p in norm_raw.columns and p in sinnorm_raw.columns]

# Seleccionar solo columnas _S de pacientes (no controles)
cols_S_norm    = norm_raw[patient_ids]
cols_S_sinnorm = sinnorm_raw[patient_ids]

# Asegurar numéricos y mismas proteínas
common_proteins = cols_S_norm.index.intersection(cols_S_sinnorm.index)
cols_S_norm    = cols_S_norm.loc[common_proteins].apply(pd.to_numeric, errors='coerce')
cols_S_sinnorm = cols_S_sinnorm.loc[common_proteins].apply(pd.to_numeric, errors='coerce')

# Grupo de cada paciente
classif_S = classification.copy()
classif_S.index = [f'{i}_{sample_type}' for i in classification.index.values]
classif_S = classif_S.loc[patient_ids]
class0 = classif_S[classif_S['cluster'] == 0].index.values
class1 = classif_S[classif_S['cluster'] == 1].index.values
group_labels = classif_S['cluster'].map({0: 'Asintomático', 1: 'Sintomático'})

print(f"Pacientes: {len(patient_ids)} (class0={len(class0)}, class1={len(class1)})")
print(f"Proteínas comunes: {len(common_proteins)}")

# ══════════════════════════════════════════════════════
# 1. FACTOR MLR POR PACIENTE
# ══════════════════════════════════════════════════════
print("\n" + "="*60)
print("1. FACTOR MLR POR PACIENTE")
print("="*60)

# Factor = log2(norm / sinnorm) por proteína y paciente; mediana por paciente
with np.errstate(divide='ignore', invalid='ignore'):
    ratio = cols_S_norm.values / cols_S_sinnorm.values
    log2_ratio = np.log2(ratio)

log2_ratio_df = pd.DataFrame(log2_ratio, index=common_proteins, columns=patient_ids)
# Mediana por paciente (columnas)
mlr_factor = log2_ratio_df.median(axis=0)
mlr_factor_df = pd.DataFrame({
    'patient': patient_ids,
    'log2_factor_MLR': mlr_factor.values,
    'grupo': group_labels.values
})

# Stats por grupo
for g in ['Asintomático', 'Sintomático']:
    vals = mlr_factor_df[mlr_factor_df['grupo'] == g]['log2_factor_MLR']
    print(f"  {g}: media={vals.mean():.4f}, SD={vals.std():.4f}, n={len(vals)}")

# Test
f0 = mlr_factor_df[mlr_factor_df['grupo'] == 'Asintomático']['log2_factor_MLR']
f1 = mlr_factor_df[mlr_factor_df['grupo'] == 'Sintomático']['log2_factor_MLR']
mu_p = scipy.stats.mannwhitneyu(f0, f1).pvalue
tt_p = scipy.stats.ttest_ind(f0, f1).pvalue
print(f"  Mann-Whitney p = {mu_p:.2e}")
print(f"  T-test p = {tt_p:.2e}")
print(f"  Diferencia de medias = {f1.mean() - f0.mean():.4f}")

# Boxplot
fig, ax = plt.subplots(figsize=(6, 5))
bp = ax.boxplot([f0.values, f1.values], labels=['Asintomático\n(class 0)', 'Sintomático\n(class 1)'],
                patch_artist=True, widths=0.5)
colors = ['steelblue', 'peru']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)
ax.scatter(np.ones(len(f0)), f0.values, color='steelblue', edgecolor='k', linewidth=0.5, zorder=3, alpha=0.7)
ax.scatter(np.ones(len(f1))*2, f1.values, color='peru', edgecolor='k', linewidth=0.5, zorder=3, alpha=0.7)
ax.set_ylabel('log₂(factor MLR)', fontsize=12)
ax.set_title(f'Factor MLR por grupo\nMann-Whitney p = {mu_p:.2e} | T-test p = {tt_p:.2e}', fontsize=11)
ax.axhline(y=0, linestyle='--', color='gray', alpha=0.5)
ax.tick_params(direction='in')
fig.tight_layout()
fig.savefig(f'{outdir}1_boxplot_factor_MLR.png', dpi=300)
plt.close(fig)
print(f"  → Guardado: {outdir}1_boxplot_factor_MLR.png")

# ══════════════════════════════════════════════════════
# 2. SEÑAL TOTAL ANTES DE NORMALIZAR vs GRUPO
# ══════════════════════════════════════════════════════
print("\n" + "="*60)
print("2. SEÑAL TOTAL ANTES DE NORMALIZAR")
print("="*60)

# Mediana de log2(intensidad) por paciente
with np.errstate(divide='ignore', invalid='ignore'):
    log2_sinnorm = np.log2(cols_S_sinnorm.apply(pd.to_numeric, errors='coerce'))
median_signal = log2_sinnorm.median(axis=0)
total_signal  = cols_S_sinnorm.sum(axis=0)

signal_df = pd.DataFrame({
    'patient': patient_ids,
    'median_log2_signal': median_signal.values,
    'total_signal': total_signal.values,
    'grupo': group_labels.values
})

for g in ['Asintomático', 'Sintomático']:
    m = signal_df[signal_df['grupo'] == g]['median_log2_signal']
    t = signal_df[signal_df['grupo'] == g]['total_signal']
    print(f"  {g}: median_log2={m.mean():.3f}±{m.std():.3f}, total={t.mean():.1f}±{t.std():.1f}")

s0_med = signal_df[signal_df['grupo'] == 'Asintomático']['median_log2_signal']
s1_med = signal_df[signal_df['grupo'] == 'Sintomático']['median_log2_signal']
s0_tot = signal_df[signal_df['grupo'] == 'Asintomático']['total_signal']
s1_tot = signal_df[signal_df['grupo'] == 'Sintomático']['total_signal']

print(f"  Mediana log2 signal: MWU p = {scipy.stats.mannwhitneyu(s0_med, s1_med).pvalue:.2e}")
print(f"  Total signal: MWU p = {scipy.stats.mannwhitneyu(s0_tot, s1_tot).pvalue:.2e}")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))

# Boxplot mediana log2
bp1 = ax1.boxplot([s0_med.values, s1_med.values], labels=['Asintomático', 'Sintomático'],
                  patch_artist=True, widths=0.5)
for patch, color in zip(bp1['boxes'], colors):
    patch.set_facecolor(color); patch.set_alpha(0.6)
ax1.scatter(np.ones(len(s0_med)), s0_med.values, color='steelblue', edgecolor='k', linewidth=0.5, zorder=3, alpha=0.7)
ax1.scatter(np.ones(len(s1_med))*2, s1_med.values, color='peru', edgecolor='k', linewidth=0.5, zorder=3, alpha=0.7)
ax1.set_ylabel('Mediana log₂(intensidad sin normalizar)', fontsize=10)
ax1.set_title(f'Señal mediana por grupo\np = {scipy.stats.mannwhitneyu(s0_med, s1_med).pvalue:.2e}')
ax1.tick_params(direction='in')

# Boxplot total
bp2 = ax2.boxplot([s0_tot.values, s1_tot.values], labels=['Asintomático', 'Sintomático'],
                  patch_artist=True, widths=0.5)
for patch, color in zip(bp2['boxes'], colors):
    patch.set_facecolor(color); patch.set_alpha(0.6)
ax2.scatter(np.ones(len(s0_tot)), s0_tot.values, color='steelblue', edgecolor='k', linewidth=0.5, zorder=3, alpha=0.7)
ax2.scatter(np.ones(len(s1_tot))*2, s1_tot.values, color='peru', edgecolor='k', linewidth=0.5, zorder=3, alpha=0.7)
ax2.set_ylabel('Σ intensidades (sin normalizar)', fontsize=10)
ax2.set_title(f'Señal total por grupo\np = {scipy.stats.mannwhitneyu(s0_tot, s1_tot).pvalue:.2e}')
ax2.tick_params(direction='in')

fig.tight_layout()
fig.savefig(f'{outdir}2_signal_total_por_grupo.png', dpi=300)
plt.close(fig)
print(f"  → Guardado: {outdir}2_signal_total_por_grupo.png")

# Correlación factor MLR vs señal total
corr_factor_signal = scipy.stats.pearsonr(mlr_factor.values, median_signal.values)
print(f"  Correlación factor_MLR vs median_log2_signal: r={corr_factor_signal[0]:.4f}, p={corr_factor_signal[1]:.2e}")

fig, ax = plt.subplots(figsize=(6, 5))
for g, c, lbl in [('Asintomático', 'steelblue', 'Class 0'), ('Sintomático', 'peru', 'Class 1')]:
    mask = mlr_factor_df['grupo'] == g
    ax.scatter(signal_df[mask.values]['median_log2_signal'], mlr_factor_df[mask]['log2_factor_MLR'],
               color=c, edgecolor='k', linewidth=0.5, label=lbl, alpha=0.7, s=50)
ax.set_xlabel('Mediana log₂(intensidad sin normalizar)')
ax.set_ylabel('log₂(factor MLR)')
ax.set_title(f'Factor MLR vs Señal pre-normalización\nr = {corr_factor_signal[0]:.3f}, p = {corr_factor_signal[1]:.2e}')
ax.legend()
ax.tick_params(direction='in')
fig.tight_layout()
fig.savefig(f'{outdir}2b_factor_MLR_vs_signal.png', dpi=300)
plt.close(fig)

# ══════════════════════════════════════════════════════
# 3. REGRESIÓN log2(FC_norm) vs log2(FC_sin_norm)
# ══════════════════════════════════════════════════════
print("\n" + "="*60)
print("3. REGRESIÓN log2(FC_norm) vs log2(FC_sin_norm)")
print("="*60)

# Leer resultados previos
results = pd.read_csv(f'{PROJECT}resultados_FC_S_norm_vs_sinnorm.csv', index_col=0)
x = results['log2FC_sin_normalizar'].values
y = results['log2FC_normalizada'].values

reg = scipy.stats.linregress(x, y)
print(f"  y = {reg.intercept:.4f} + {reg.slope:.4f} * x")
print(f"  R² = {reg.rvalue**2:.6f}")
print(f"  Intercepto ≈ {reg.intercept:.4f} (esperado ≈ -2.68)")
print(f"  Pendiente ≈ {reg.slope:.4f} (esperado ≈ 1.0)")

fig, ax = plt.subplots(figsize=(7, 6))
ax.scatter(x, y, color='purple', edgecolor='k', linewidth=0.5, alpha=0.7, s=40)
x_line = np.linspace(min(x)-0.3, max(x)+0.3, 100)
ax.plot(x_line, reg.intercept + reg.slope * x_line, 'r-', linewidth=2,
        label=f'y = {reg.intercept:.3f} + {reg.slope:.3f}x\nR² = {reg.rvalue**2:.4f}')
ax.plot(x_line, x_line, '--', color='gray', alpha=0.5, label='y = x (identidad)')
ax.set_xlabel('log₂(FC sin normalizar)', fontsize=12)
ax.set_ylabel('log₂(FC normalizada)', fontsize=12)
ax.set_title('Regresión: FC normalizado vs sin normalizar', fontsize=13)
ax.legend(fontsize=10)
ax.tick_params(direction='in')
ax.axhline(0, color='gray', alpha=0.3, linewidth=0.5)
ax.axvline(0, color='gray', alpha=0.3, linewidth=0.5)

# Anotar proteínas con mayor residuo
residuals = y - (reg.intercept + reg.slope * x)
top_res = np.argsort(np.abs(residuals))[-5:]
for idx in top_res:
    ax.annotate(results.index[idx], (x[idx], y[idx]), fontsize=7,
                xytext=(5, 5), textcoords='offset points')

fig.tight_layout()
fig.savefig(f'{outdir}3_regresion_FC_norm_vs_sinnorm.png', dpi=300)
plt.close(fig)
print(f"  → Guardado: {outdir}3_regresion_FC_norm_vs_sinnorm.png")

# ══════════════════════════════════════════════════════
# 4. FACTOR MLR vs VARIABLES CLÍNICAS/TÉCNICAS
# ══════════════════════════════════════════════════════
print("\n" + "="*60)
print("4. FACTOR MLR vs VARIABLES CLÍNICAS")
print("="*60)

# Preparar sergas con índices correctos
sgs_paciente = np.array([str(int(ts.split(sep='_')[-1])) for ts in sergas['Patient code']])
sergas_indexed = sergas.copy()
sergas_indexed.index = sgs_paciente
sergas_indexed = sergas_indexed.loc[[p.split('_')[0] for p in patient_ids if p.split('_')[0] in sgs_paciente]]

# Alinear factor MLR con sergas
mlr_for_sergas = mlr_factor_df.copy()
mlr_for_sergas['patient_num'] = [p.replace(f'_{sample_type}', '') for p in mlr_for_sergas['patient']]
mlr_for_sergas = mlr_for_sergas.set_index('patient_num')

common_patients = mlr_for_sergas.index.intersection(sergas_indexed.index)
mlr_aligned = mlr_for_sergas.loc[common_patients]
sergas_aligned = sergas_indexed.loc[common_patients]

vars_to_check = ['Age (years)', 'Sex', 'Hospitalization', 'Severity scale',
                 'Charlson Comorbidity Index', 'Clinical frailty scale', 'Smoking']

fig, axes = plt.subplots(2, 4, figsize=(18, 9))
axes = axes.flatten()

for i, var in enumerate(vars_to_check):
    ax = axes[i]
    if var in sergas_aligned.columns:
        valid = sergas_aligned[var].dropna()
        common_v = valid.index.intersection(mlr_aligned.index)
        if len(common_v) < 5:
            ax.set_title(f'{var}\n(insuf. datos)', fontsize=9)
            continue
        vals = sergas_aligned.loc[common_v, var]
        factors = mlr_aligned.loc[common_v, 'log2_factor_MLR']

        if vals.dtype in ['float64', 'int64'] and vals.nunique() > 5:
            # Scatter + correlación
            ax.scatter(vals, factors, color='purple', edgecolor='k', linewidth=0.4, alpha=0.6, s=30)
            try:
                r, p = scipy.stats.pearsonr(vals.astype(float), factors.astype(float))
                ax.set_title(f'{var}\nr={r:.3f}, p={p:.2e}', fontsize=9)
            except:
                ax.set_title(var, fontsize=9)
        else:
            # Boxplot por categoría
            categories = sorted(vals.unique())
            data_by_cat = [factors[vals == cat].values for cat in categories]
            data_by_cat = [d for d in data_by_cat if len(d) > 0]
            categories = [str(c) for c, d in zip(categories, [factors[vals == cat].values for cat in sorted(vals.unique())]) if len(d) > 0]
            if len(data_by_cat) > 1:
                bp = ax.boxplot(data_by_cat, labels=categories, patch_artist=True, widths=0.5)
                for patch in bp['boxes']:
                    patch.set_facecolor('mediumpurple'); patch.set_alpha(0.5)
            ax.set_title(var, fontsize=9)
        ax.set_ylabel('log₂(factor MLR)', fontsize=8)
        ax.tick_params(labelsize=7, direction='in')

# Vaciar el último subplot si sobra
if len(vars_to_check) < len(axes):
    for j in range(len(vars_to_check), len(axes)):
        axes[j].axis('off')

fig.suptitle('Factor MLR vs Variables Clínicas', fontsize=14)
fig.tight_layout()
fig.savefig(f'{outdir}4_factor_MLR_vs_clinicas.png', dpi=300)
plt.close(fig)
print(f"  → Guardado: {outdir}4_factor_MLR_vs_clinicas.png")

# ══════════════════════════════════════════════════════
# 5. HISTOGRAMA de la diferencia log2FC
# ══════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 5))
diff = results['diff_log2FC (norm - sin_norm)'].values
ax.hist(diff, bins=20, color='mediumpurple', edgecolor='k', alpha=0.7)
ax.axvline(np.mean(diff), color='red', linestyle='--', linewidth=2, label=f'Media = {np.mean(diff):.3f}')
ax.set_xlabel('Δ = log₂(FC_norm) − log₂(FC_sin_norm)')
ax.set_ylabel('Número de proteínas')
ax.set_title('Distribución de Δᵢ (desplazamiento por proteína)')
ax.legend()
ax.tick_params(direction='in')
fig.tight_layout()
fig.savefig(f'{outdir}5_histograma_delta.png', dpi=300)
plt.close(fig)

# ══════════════════════════════════════════════════════
# 6. GUARDAR TABLA RESUMEN
# ══════════════════════════════════════════════════════
mlr_factor_df.to_csv(f'{outdir}factor_MLR_por_paciente.csv', index=False)
signal_df.to_csv(f'{outdir}signal_total_por_paciente.csv', index=False)

print(f"\n✅ Todos los resultados guardados en: {outdir}")
print("  - 1_boxplot_factor_MLR.png")
print("  - 2_signal_total_por_grupo.png")
print("  - 2b_factor_MLR_vs_signal.png")
print("  - 3_regresion_FC_norm_vs_sinnorm.png")
print("  - 4_factor_MLR_vs_clinicas.png")
print("  - 5_histograma_delta.png")
print("  - factor_MLR_por_paciente.csv")
print("  - signal_total_por_paciente.csv")
