# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 12:01:47 2023

@author: usccqasg
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import numpy as np

sns.set(context='paper', rc={'figure.figsize':(20,12)})
# sns.set(context='paper')
# Cargar los archivos Excel y de texto
excel_path = 'LIPID-CHUS_Anonimizado_proteomica_para_analizar.xlsx'
df_excel = pd.read_excel(excel_path)

text_path = 'patient_severity.txt'
df_text = pd.read_csv(text_path, sep="\t")

# Limpiar el dataframe de texto para excluir filas con 'CONTROL' en el índice
df_text_clean = df_text[~df_text['index'].str.contains('CONTROL')]
df_text_clean['Patient_Number'] = df_text_clean['index'].str.extract('(\d+)').astype(int)

# Extraer la parte numérica de las columnas clave en ambos dataframes
df_excel['Patient_Number'] = df_excel['Código del paciente'].str.extract('(\d+)').astype(int)

# Combinar los dos dataframes en función del 'Patient_Number'
merged_df = pd.merge(df_excel, df_text_clean, on='Patient_Number', how='inner')

# Ordenar el dataframe combinado en función de 'Severity_Metric'
sorted_df = merged_df.sort_values(by='Severity_Metric', ascending=False)

# Filtrar las columnas para 'SI' o 'NO' hasta la columna 150
si_no_columns_limited = [col for col in sorted_df.columns[:135] if sorted_df[col].dropna().isin(['SI', 'NO']).all()]

# Crear un subconjunto del dataframe con solo las columnas relevantes (hasta la 150)
plot_data_limited = sorted_df[['Código del paciente'] + si_no_columns_limited]
plot_data_limited = plot_data_limited.replace({'SI': 1, 'NO': 0})
plot_data_limited.set_index('Código del paciente', inplace=True)

# Acortar los nombres de las columnas a un máximo de caracteres
max_chars = 31
shortened_columns = [col[:max_chars] for col in si_no_columns_limited]
plot_data_shortened = plot_data_limited.copy()
plot_data_shortened.columns = shortened_columns

sorted_df.set_index('Código del paciente', inplace=True)
plot_data_shortened.set_index(sorted_df.index, inplace=True)



# Crear el gráfico con los datos limitados

plt.xticks(fontsize=10)
sns.heatmap(plot_data_shortened, cmap=['#871950', '#FFCC00'], cbar=False, yticklabels=True, annot=False, linewidths=1, linecolor='k')#, annot_kws={"size": 12})
# plt.ylabel('Código')
# plt.xlabel('Variables (SI/NO)')
plt.title('Distribución de Respuestas SI/NO por Paciente', size = 17)
plt.tight_layout()
plt.savefig('aaa.png', dpi = 600)
# plt.show()

im = Image.open('aaa.png')
im.show()
