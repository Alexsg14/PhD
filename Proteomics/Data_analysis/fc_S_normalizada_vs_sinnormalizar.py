#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cálculo de Fold Change (FC) para pacientes _S (supernatant) usando datos
normalizados y sin normalizar de la librería 2024 (Junio 2024).

Replica la lógica de calculate_volcano de analise_Julio26.py:
    FC = mean_class1 / mean_class0

Se aplica a:
  1. Áreas normalizadas   → FC_norm
  2. Áreas sin normalizar → FC_sin_norm
  3. Diferencia:  log2(FC_norm) - log2(FC_sin_norm)

NO modifica ningún archivo original.
"""

import numpy as np
import pandas as pd
import scipy.stats

# ─────────────────────────────────────────────────────
# 1. RUTAS
# ─────────────────────────────────────────────────────
PROJECT_ROUTE = './'
junio_dir = f'{PROJECT_ROUTE}22014_SWATH libreria COVID+SARS Junio 2024/'
data_route = f'{PROJECT_ROUTE}DATA/'

file_norm    = f'{junio_dir}24014 areas normalizadas nueva libreria SARS 18062024.xls'
file_sinnorm = f'{junio_dir}24014 areas sin normalizar nueva libreria SARS 18062024.xls'

sample_type = 'S'

# ─────────────────────────────────────────────────────
# 2. LEER DATOS CRUDOS
# ─────────────────────────────────────────────────────
areas_norm_raw    = pd.read_excel(file_norm, index_col=0)
areas_sinnorm_raw = pd.read_excel(file_sinnorm, index_col=0)

# El archivo sin normalizar puede tener filas extra (Sample ID, Group)
# Eliminarlas si existen
for extra_row in ['Sample ID', 'Group']:
    if extra_row in areas_sinnorm_raw.index:
        areas_sinnorm_raw = areas_sinnorm_raw.drop(extra_row)

# ─────────────────────────────────────────────────────
# 3. LEER CLASIFICACIÓN (class 0 / class 1)
# ─────────────────────────────────────────────────────
classification_prot1 = pd.read_csv(f'{data_route}clusters_S_proteomica1_v2020.csv', index_col=0)
classification_prot1.index = [str(int(i)) for i in classification_prot1.index.values]

# ─────────────────────────────────────────────────────
# 4. FUNCIÓN process_raw_areas (adaptada del script original)
#    - Transponer
#    - Eliminar proteínas RRR
#    - Extraer código Uniprot
#    - Seleccionar solo pacientes _S
# ─────────────────────────────────────────────────────
def process_raw_areas(areas_raw, patient_indices):
    """Replica la lógica de process_raw_areas de analise_Julio26.py."""
    areas_proc = areas_raw.transpose()
    
    # Eliminar columnas que empiezan por RRR
    areas_proc = areas_proc[[col for col in areas_proc.columns if not col.startswith('RRR')]]
    
    # Guardar inmunoglobulinas
    ig = [col.split('|')[2].split('_')[0] for col in areas_proc.columns if 'IG' in col]
    
    # Renombrar columnas: quedarse solo con el código Uniprot
    areas_proc.columns = [i.split('|')[2].split('_')[0] for i in areas_proc.columns.values]
    
    # Seleccionar solo los pacientes indicados
    areas_proc = areas_proc.loc[patient_indices]
    
    return areas_proc, ig


# Construir la lista de pacientes _S que están en la clasificación
patient_indices = [f'{i}_{sample_type}' for i in classification_prot1.index.values]

# Verificar qué pacientes están disponibles en los datos
available_norm    = [p for p in patient_indices if p in areas_norm_raw.columns]
available_sinnorm = [p for p in patient_indices if p in areas_sinnorm_raw.columns]

# Usar solo pacientes que estén en AMBOS archivos
available_common = sorted(set(available_norm) & set(available_sinnorm), 
                          key=lambda x: int(x.split('_')[0]))

print(f"Pacientes _S en clasificación: {len(patient_indices)}")
print(f"Pacientes _S disponibles en normalizada: {len(available_norm)}")
print(f"Pacientes _S disponibles en sin normalizar: {len(available_sinnorm)}")
print(f"Pacientes _S comunes (usados): {len(available_common)}")

# Procesar ambos archivos
areas_norm, ig_norm       = process_raw_areas(areas_norm_raw, available_common)
areas_sinnorm, ig_sinnorm = process_raw_areas(areas_sinnorm_raw, available_common)

# Asegurar que todos los valores son numéricos
areas_norm    = areas_norm.apply(pd.to_numeric, errors='coerce')
areas_sinnorm = areas_sinnorm.apply(pd.to_numeric, errors='coerce')

print(f"\nShape áreas normalizadas (procesadas): {areas_norm.shape}")
print(f"Shape áreas sin normalizar (procesadas): {areas_sinnorm.shape}")

# ─────────────────────────────────────────────────────
# 5. ASIGNAR CLASES (class 0 / class 1)
# ─────────────────────────────────────────────────────
# Actualizar índices de la clasificación para que sean X_S
classification_S = classification_prot1.copy()
classification_S.index = [f'{i}_{sample_type}' for i in classification_prot1.index.values]

# Solo pacientes comunes
classification_S = classification_S.loc[available_common]

class0 = classification_S[classification_S['cluster'] == 0].index.values
class1 = classification_S[classification_S['cluster'] == 1].index.values

print(f"\nClass 0 (asintomáticos) - {len(class0)} pacientes: {[c.replace('_S','') for c in class0]}")
print(f"Class 1 (sintomáticos) - {len(class1)} pacientes: {[c.replace('_S','') for c in class1]}")

# ─────────────────────────────────────────────────────
# 6. CALCULAR FC (replica calculate_volcano del script original)
#    FC = mean_class1 / mean_class0
# ─────────────────────────────────────────────────────
def calculate_fc(areas_df, class0_idx, class1_idx):
    """
    Calcula FC = mean(class1) / mean(class0) para cada proteína.
    También calcula p-values con T-test.
    Retorna un DataFrame con mean0, mean1, FC, p-values.
    """
    df = areas_df.copy()
    df['class'] = 0
    df.loc[class1_idx, 'class'] = 1
    
    volcano = df.groupby(by='class').mean().T
    volcano.columns = ['mean0', 'mean1']
    
    df_noclass = df.drop('class', axis=1)
    
    volcano['p-values'] = [
        scipy.stats.ttest_ind(
            a=df_noclass[protein].loc[class0_idx],
            b=df_noclass[protein].loc[class1_idx]
        ).pvalue
        for protein in df_noclass.columns.values
    ]
    
    volcano['FC'] = volcano['mean1'] / volcano['mean0']
    
    return volcano


print("\n" + "="*70)
print("CALCULANDO FOLD CHANGE PARA DATOS NORMALIZADOS...")
print("="*70)
fc_norm = calculate_fc(areas_norm, class0, class1)
print(f"  Proteínas analizadas: {len(fc_norm)}")
print(f"  FC > 1.5 (significativas): {len(fc_norm[(fc_norm['FC'] > 1.5) & (fc_norm['p-values'] < 0.05)])}")
print(f"  FC < 1/1.5 (significativas): {len(fc_norm[(fc_norm['FC'] < 1/1.5) & (fc_norm['p-values'] < 0.05)])}")

print("\n" + "="*70)
print("CALCULANDO FOLD CHANGE PARA DATOS SIN NORMALIZAR...")
print("="*70)
fc_sinnorm = calculate_fc(areas_sinnorm, class0, class1)
print(f"  Proteínas analizadas: {len(fc_sinnorm)}")
print(f"  FC > 1.5 (significativas): {len(fc_sinnorm[(fc_sinnorm['FC'] > 1.5) & (fc_sinnorm['p-values'] < 0.05)])}")
print(f"  FC < 1/1.5 (significativas): {len(fc_sinnorm[(fc_sinnorm['FC'] < 1/1.5) & (fc_sinnorm['p-values'] < 0.05)])}")

# ─────────────────────────────────────────────────────
# 7. CALCULAR log2(FC) Y LA DIFERENCIA
#    diff = log2(FC_norm) - log2(FC_sin_norm)
# ─────────────────────────────────────────────────────
# Asegurar que las proteínas son las mismas y están en el mismo orden
common_proteins = fc_norm.index.intersection(fc_sinnorm.index)
fc_norm    = fc_norm.loc[common_proteins]
fc_sinnorm = fc_sinnorm.loc[common_proteins]

print(f"\nProteínas comunes entre ambos datasets: {len(common_proteins)}")

# Construir el DataFrame de resultados
results = pd.DataFrame(index=common_proteins)
results['FC_normalizada']     = fc_norm['FC']
results['FC_sin_normalizar']  = fc_sinnorm['FC']
results['log2FC_normalizada']     = np.log2(fc_norm['FC'])
results['log2FC_sin_normalizar']  = np.log2(fc_sinnorm['FC'])
results['diff_log2FC (norm - sin_norm)'] = results['log2FC_normalizada'] - results['log2FC_sin_normalizar']
results['pvalue_normalizada']     = fc_norm['p-values']
results['pvalue_sin_normalizar']  = fc_sinnorm['p-values']

# Ordenar por valor absoluto de la diferencia
results_sorted = results.sort_values(by='diff_log2FC (norm - sin_norm)', key=abs, ascending=False)

print("\n" + "="*70)
print("RESULTADOS: log2(FC_normalizada) - log2(FC_sin_normalizar)")
print("="*70)
print(f"\n{'Proteína':<20} {'log2FC_norm':>12} {'log2FC_sinN':>12} {'Diferencia':>12}")
print("-" * 60)
for protein in results_sorted.index:
    row = results_sorted.loc[protein]
    print(f"{protein:<20} {row['log2FC_normalizada']:>12.4f} {row['log2FC_sin_normalizar']:>12.4f} {row['diff_log2FC (norm - sin_norm)']:>12.4f}")

# ─────────────────────────────────────────────────────
# 8. GUARDAR RESULTADOS (sin modificar archivos originales)
# ─────────────────────────────────────────────────────
output_file = f'{PROJECT_ROUTE}resultados_FC_S_norm_vs_sinnorm.csv'
results_sorted.to_csv(output_file)
print(f"\n✅ Resultados guardados en: {output_file}")

# ─────────────────────────────────────────────────────
# 9. RESUMEN ESTADÍSTICO
# ─────────────────────────────────────────────────────
print("\n" + "="*70)
print("RESUMEN ESTADÍSTICO DE LA DIFERENCIA")
print("="*70)
diff_col = results['diff_log2FC (norm - sin_norm)']
print(f"  Media de la diferencia:    {diff_col.mean():.6f}")
print(f"  Mediana de la diferencia:  {diff_col.median():.6f}")
print(f"  Desv. estándar:           {diff_col.std():.6f}")
print(f"  Mínimo:                   {diff_col.min():.6f} ({diff_col.idxmin()})")
print(f"  Máximo:                   {diff_col.max():.6f} ({diff_col.idxmax()})")
print(f"  Proteínas con |diff| > 0.1: {len(diff_col[abs(diff_col) > 0.1])}")
print(f"  Proteínas con |diff| > 0.5: {len(diff_col[abs(diff_col) > 0.5])}")
