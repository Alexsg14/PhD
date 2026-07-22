# PMF & FES Analysis Toolkit

Este módulo contiene scripts en Bash y Python diseñados para el análisis de simulaciones de Metadinámica (Well-Tempered y estándar) en 1D y 2D a partir de archivos de salida de PLUMED (`HILLS`, `COLVAR`).

---

## 📂 Contenido del Directorio

### 1. Master Scripts (Bash)
*   **[hills.sh](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/hills.sh)**: Script principal para análisis 1D. Controla la generación de FES, límites ROI, curvas PMF, vídeos y cálculo de $\Delta G$ mediante integración de áreas.
*   **[hills_2D.sh](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/hills_2D.sh)**: Script principal adaptado para reconstrucciones bidimensionales (FES 2D).
*   **[blocks_analysis.sh](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/blocks_analysis.sh)**: Facilita la ejecución automatizada y comparativa de análisis por bloques.
*   **[manual_hills.sh](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/manual_hills.sh)**: Script de ejecución rápida para pruebas manuales o depuración.

### 2. Motores de Procesamiento (Python)
*   **[hills_video.py](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/hills_video.py)**: Núcleo gráfico en 1D. Permite representar perfiles FES históricos, crear animaciones con degradados de color (Blues) mediante `ffmpeg` e integrar áreas bajo la curva.
*   **[2D_hills.py](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/2D_hills.py)**: Renderiza superficies 2D de energía libre a partir de colinas de dos variables colectivas.
*   **[block_analysis_hills.py](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/block_analysis_hills.py)**: Realiza el análisis estadístico por bloques para la diferencia de energía libre ($\Delta F(t)$), permitiendo estimar el error estándar de la media (SEM).
*   **[compare_last_hills.py](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/compare_last_hills.py)**: Evalúa y compara el comportamiento del SEM frente al tamaño de bloque para diferentes conjuntos finales de colinas.
*   **[meta_diagnose.py](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/meta_diagnose.py)**: Diagnostica la calidad y convergencia de la metadinámica leyendo el `COLVAR`. Analiza transiciones entre pozos, tiempo en los muros artificiales y sugiere ajustes cualitativos para el parámetro `HEIGHT`.
*   **[hills_live.py](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/hills_live.py)**: Script auxiliar para visualización y monitorización en tiempo real del progreso de la FES.

### 3. Código Obsoleto / Depreciado
*   **`hills_alicia.py`**: Antecesor directo de `hills_video.py`. Se mantiene únicamente por compatibilidad histórica/archivo.

---

## ⚙️ Configuración y Portabilidad

Los scripts de Bash están diseñados con **rutas relativas y variables de entorno** para garantizar que funcionen tanto en clústeres de computación de alto rendimiento (HPC) como en local:

### Definición de Ruta Base
Por defecto, los scripts buscan los datos en la ruta del clúster:
`/mnt/netapp1/RES_SuPepMem/ALEX/_PMF_Peptidomica`

Si necesitas ejecutar los análisis en una ruta diferente, define la variable de entorno `PMF_BASE_PATH` en tu terminal antes de arrancar los scripts:
```bash
export PMF_BASE_PATH="/home/usuario/mis_simulaciones"
./hills.sh
```

---

## 🚀 Ejemplos de Uso

### Generar FES y animación 1D
```bash
./hills.sh HILLS_WT output_folder --movie --limits
```

### Diagnosticar convergencia desde COLVAR
```bash
python meta_diagnose.py COLVAR_WT --cv-name D.z --roi-min 0.0 --roi-max 7.0 --lower-wall -1.0 --upper-wall 9.0
```

### Comparación por bloques
```bash
./blocks_analysis.sh $PMF_BASE_PATH kappa2000_COV COMPART_BLOCKS 2.3 2.9 5.0 7.0 "10000 20000 40000 80000"
```
