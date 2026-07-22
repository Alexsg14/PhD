#!/usr/bin/env python3
# python ../../hills_analysis.py HILLS PMF_FOLDER/
import sys
import os
import subprocess
import numpy as np
import matplotlib
matplotlib.use("Agg")  # para que funcione en servidores sin pantalla
import matplotlib.pyplot as plt
import matplotlib.cm as cm

import matplotlib as mpl

mpl.rcParams["axes.labelsize"] = 20
mpl.rcParams["axes.titlesize"] = 22
mpl.rcParams["xtick.labelsize"] = 18
mpl.rcParams["ytick.labelsize"] = 18
mpl.rcParams["legend.fontsize"] = 16
mpl.rcParams["figure.titlesize"] = 22
fontsize_legend = 12

# Colorbar
mpl.rcParams["font.size"] = 18

D="D" #Cambiar esto entre D.z y D para MEM y LPA

def read_fields(hills_file):
    fields = None
    with open(hills_file) as f:
        for line in f:
            if line.startswith("#! FIELDS"):
                fields = line.split()[2:]
                break
    if fields is None:
        raise RuntimeError("No se encontró la línea '#! FIELDS' en el HILLS")
    return fields


def compute_fes_profile(grid, D0, sigma, h, n_hills=None, norm_roi=(0, 7)):
    """
    Devuelve la FES acumulada hasta n_hills.
    Convención: Mínimo en 0 DENTRO de norm_roi.
    """
    if n_hills is None:
        n_hills = len(D0)
    
    F = np.zeros_like(grid)
    # Acumular gaussianas
    for Di, si, hi in zip(D0[:n_hills], sigma[:n_hills], h[:n_hills]):
        F += hi * np.exp(-(grid - Di) ** 2 / (2 * si * si))
    
    Fi = -F # Invertir para FES
    
    # --- Normalización basada en ROI ---
    if norm_roi is not None:
        xmin, xmax = norm_roi
        # Encontrar índices en la grilla que caen dentro del ROI
        roi_indices = np.where((grid >= xmin) & (grid <= xmax))
        
        if roi_indices[0].size > 0:
            # Encontrar el mínimo solo en esa región
            min_in_roi = Fi[roi_indices].min()
            # Restar ese mínimo a *toda* la curva
            Fi -= min_in_roi
        else:
            # Fallback si el ROI está fuera de la grilla (raro)
            Fi -= Fi.min()
    else:
        # Fallback si norm_roi es None (normalización global)
        Fi -= Fi.min()
    # ---
    
    return Fi

# --- REEMPLAZA LA FUNCIÓN ANTIGUA POR ESTA ---
def calculate_deltaG_from_areas(
    grid_x,            # D.z coordinates
    fes,               # Normalized FES (min at 0)
    offset_energy,     # Energy of the plateau (plateau_start_y_coord)
    occupied_start,    # Start of the "well" (e.g., 0.0)
    occupied_end,      # End of the "well" (plateau_start_x_coord)
    total_start,       # Start of total integration (e.g., 0.0)
    total_end,         # End of total integration (e.g., 7.0)
    T=298.0,
    R=8.314472/1000.0, # R in kJ/(mol·K)
    out_dir="."
):
    """
    Calcula K y DeltaG a partir del ratio de áreas de la probabilidad Z(X).
    Z(X) se calcula desde la FES(X) y se re-normaliza con un offset.
    Z_rel(X) = exp( (offset_energy - fes(X)) / RT )
    """
    RT = R * T
    
    # 1. Calcular la probabilidad relativa re-normalizada
    Z_rel = np.exp((offset_energy - fes) / RT)
    
    # 2. Definir límites
    a_oc, b_oc = (min(occupied_start, occupied_end), max(occupied_start, occupied_end))
    a_tot, b_tot = (min(total_start, total_end), max(total_start, total_end))

    # 3. Filtrar el dominio al rango total [a_tot, b_tot]
    mask_total = (grid_x >= a_tot) & (grid_x <= b_tot)
    if not np.any(mask_total):
        print("🛑 Dominio total de integración vacío: revisa total_start y total_end.")
        return np.nan, np.nan

    X_red = grid_x[mask_total]
    Z_red = Z_rel[mask_total]
    
    # --- MODIFICADO: Calcular áreas por integración directa ---

    # 4. Área Ocupada (el "pozo")
    mask_ocupado = (X_red >= a_oc) & (X_red <= b_oc)
    X_ocupado = X_red[mask_ocupado]
    Z_ocupado = Z_red[mask_ocupado]
    area_ocupado = np.trapz(Z_ocupado, X_ocupado) if np.any(mask_ocupado) else 0.0

    # 5. Área Libre (el "plateau")
    # El área libre es TODO lo que está en el rango total PERO NO en el rango ocupado.
    # En este script, asumimos que total_start = occupied_start,
    # por lo que el área libre es solo [occupied_end, total_end]
    mask_libre = (X_red > b_oc) & (X_red <= b_tot)
    X_libre = X_red[mask_libre]
    Z_libre = Z_red[mask_libre]
    area_libre = np.trapz(Z_libre, X_libre) if np.any(mask_libre) else 0.0
    
    # --- FIN DE LA MODIFICACIÓN ---

    # 6. Imprimir resultados
    print("-" * 50)
    print("📊 Análisis de DeltaG por Integración de Áreas")
    print(f'Offset Energy (Plateau): {offset_energy:.3f} kJ/mol')
    print(f'Rango Total (Integración): [{a_tot:.3f}, {b_tot:.3f}]')
    print(f'Rango Ocupado (Pozo):     [{a_oc:.3f}, {b_oc:.3f}]')
    print(f'Área Ocupada (Pozo): {area_ocupado:.6f}, Área Libre (Plateau): {area_libre:.6f}')

    # 7. Cálculo de K y DeltaG
    if area_libre <= 1e-12 or area_ocupado <= 1e-12:
        print("🛑 Áreas no positivas o numéricamente nulas → K/ΔG indefinidos.")
        K, DeltaG = np.nan, np.nan
    else:
        K = area_ocupado / area_libre
        DeltaG = -RT * np.log(K)
        print(f'K (Ocupado/Libre): {K:.6f}')
        print(f'DeltaG (calculado): {DeltaG:.3f} kJ/mol')
    print("-" * 50)

    # 8. Visualización
    plt.figure(figsize=(10, 5))
    plt.plot(X_red, Z_red, color='black', lw=2, label=f'Z_rel(X) (Offset={offset_energy:.1f} kJ/mol)')

    # Área ocupada
    plt.fill_between(X_ocupado, Z_ocupado, alpha=0.5, color='orange', label=f'Área Ocupada (Pozo)\nK = {K:.3f}')

    # Área libre
    plt.fill_between(X_libre, Z_libre, alpha=0.4, color='skyblue', label=f'Área Libre (Plateau)')

    # Límites
    plt.axvline(a_oc, color='red', ls='--', label=f'Límite Ocupado Inf. = {a_oc:.3f}')
    plt.axvline(b_oc, color='red', ls='--', label=f'Límite Ocupado Sup. = {b_oc:.3f}')

    plt.xlabel('D (nm)'); plt.ylabel('Z_rel(X) (Probabilidad relativa re-normalizada)');
    plt.title(f'Integración de Áreas para DeltaG (calculado = {DeltaG:.2f} kJ/mol)')
    plt.legend(fontsize=8); plt.grid(alpha=0.3); plt.tight_layout()
    
    out_path = os.path.join(out_dir, "Area_Offset_DeltaG.png")
    plt.savefig(out_path, dpi=300)
    plt.close() # Usar close() para script de servidor
    print(f"Guardado: {out_path}")

    return K, DeltaG
# --- NUEVA FUNCIÓN AÑADIDA ---
def calculate_deltaG_from_areas2(
    grid_x,            # D.z coordinates
    fes,               # Normalized FES (min at 0)
    offset_energy,     # Energy of the plateau (plateau_start_y_coord)
    occupied_start,    # Start of the "well" (e.g., 0.0)
    occupied_end,      # End of the "well" (plateau_start_x_coord)
    total_start,       # Start of total integration (e.g., 0.0)
    total_end,         # End of total integration (e.g., 7.0)
    T=298.0,
    R=8.314472/1000.0, # R in kJ/(mol·K)
    out_dir="."
):
    """
    Calcula K y DeltaG a partir del ratio de áreas de la probabilidad Z(X).
    Z(X) se calcula desde la FES(X) y se re-normaliza con un offset.
    Z_rel(X) = exp( (offset_energy - fes(X)) / RT )
    """
    RT = R * T
    
    # 1. Calcular la probabilidad relativa re-normalizada
    # Z_rel = exp( (offset_energy - fes) / RT )
    # Esto pone el "plateau" (donde fes ≈ offset_energy) en Z_rel ≈ exp(0) = 1
    # Y el "pozo" (donde fes = 0) en Z_rel ≈ exp(offset_energy / RT)
    Z_rel = np.exp((offset_energy - fes) / RT)
    
    # 2. Definir límites
    a_oc, b_oc = (min(occupied_start, occupied_end), max(occupied_start, occupied_end))
    a_tot, b_tot = (min(total_start, total_end), max(total_start, total_end))

    # 3. Filtrar el dominio al rango total [a_tot, b_tot]
    mask_total = (grid_x >= a_tot) & (grid_x <= b_tot)
    if not np.any(mask_total):
        print("🛑 Dominio total de integración vacío: revisa total_start y total_end.")
        return np.nan, np.nan

    X_red = grid_x[mask_total]
    Z_red = Z_rel[mask_total]

    # 4. Área Total (en el rango total)
    area_total = np.trapz(Z_red, X_red)

    # 5. Área Ocupada (el "pozo")
    mask_ocupado = (X_red >= a_oc) & (X_red <= b_oc)
    X_ocupado = X_red[mask_ocupado]
    Z_ocupado = Z_red[mask_ocupado]
    area_ocupado = np.trapz(Z_ocupado, X_ocupado) if np.any(mask_ocupado) else 0.0

    # 6. Área Libre (el "plateau")
    area_libre = area_total - area_ocupado

    # 7. Imprimir resultados
    print("-" * 50)
    print("📊 Análisis de DeltaG por Integración de Áreas")
    print(f'Offset Energy (Plateau): {offset_energy:.3f} kJ/mol')
    print(f'Rango Total (Integración): [{a_tot:.3f}, {b_tot:.3f}]')
    print(f'Rango Ocupado (Pozo):     [{a_oc:.3f}, {b_oc:.3f}]')
    print(f'Área Ocupada (Pozo): {area_ocupado:.6f}, Área Libre (Plateau): {area_libre:.6f}')

    # 8. Cálculo de K y DeltaG
    if area_libre <= 1e-12 or area_ocupado <= 1e-12:
        print("🛑 Áreas no positivas o numéricamente nulas → K/ΔG indefinidos.")
        K, DeltaG = np.nan, np.nan
    else:
        K = area_ocupado / area_libre
        DeltaG = -RT * np.log(K)
        print(f'K (Ocupado/Libre): {K:.6f}')
        print(f'DeltaG (calculado): {DeltaG:.3f} kJ/mol')
    print("-" * 50)

    # 9. Visualización
    plt.figure(figsize=(10, 5))
    plt.plot(X_red, Z_red, color='black', lw=2, label=f'Z_rel(X) (Offset={offset_energy:.1f} kJ/mol)')

    # Área ocupada
    plt.fill_between(X_ocupado, Z_ocupado, alpha=0.5, color='orange', label=f'Área Ocupada (Pozo)\nK = {K:.3f}')

    # Área libre
    mask_libre = (X_red >= a_tot) & (X_red <= b_tot) & ~mask_ocupado
    X_libre = X_red[mask_libre]
    Z_libre = Z_red[mask_libre]
    plt.fill_between(X_libre, Z_libre, alpha=0.4, color='skyblue', label='Área Libre (Plateau)')

    # Límites
    plt.axvline(a_oc, color='red', ls='--', label=f'Límite Ocupado Inf. = {a_oc:.3f}')
    plt.axvline(b_oc, color='red', ls='--', label=f'Límite Ocupado Sup. = {b_oc:.3f}')

    plt.xlabel('D (nm)'); plt.ylabel('Z_rel(X) (Probabilidad relativa re-normalizada)');
    plt.title(f'Integración de Áreas para DeltaG (calculado = {DeltaG:.2f} kJ/mol)')
    plt.legend(fontsize=8); plt.grid(alpha=0.3); plt.tight_layout()
    
    out_path = os.path.join(out_dir, "Area_Offset_DeltaG.png")
    plt.savefig(out_path, dpi=300)
    plt.close() # Usar close() para script de servidor
    print(f"Guardado: {out_path}")

    return K, DeltaG
# --- FIN DE LA NUEVA FUNCIÓN ---


def make_movie_og(hills_file, out_dir, fields, data, D0, sigma, h):
    """
    Genera un vídeo MP4 de la FES acumulada (solo la curva más reciente).
    (Esta función usa tiempo absoluto, 0 -> final)
    """
    try:
        idx_time = fields.index("time")
    except ValueError:
        print("No hay columna 'time' en el HILLS; no se puede hacer el vídeo.")
        return

    time_ps = data[:, idx_time]
    time_ns = time_ps / 1000.0
    
    total = len(D0)
    ROI_X = (0, 7) 
    Dmin, Dmax = D0.min() - 2 * sigma.max(), D0.max() + 2 * sigma.max()
    grid = np.linspace(Dmin, Dmax, 400)
    
    roi_indices = np.where((grid >= ROI_X[0]) & (grid <= ROI_X[1]))
    if roi_indices[0].size == 0:
        roi_indices = np.where((grid >= grid.min()) & (grid <= grid.max()))

    F_final = compute_fes_profile(grid, D0, sigma, h, n_hills=total, norm_roi=ROI_X)
    global_max = F_final[roi_indices].max() 

    N_FRAMES = min(200, total)
    frame_indices = np.linspace(0, total - 1, N_FRAMES, dtype=int)

    frames_dir = os.path.join(out_dir, "_frames_fes_movie")
    os.makedirs(frames_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(5, 5))
    line, = ax.plot([], [], lw=1)
    
    ax.set_xlim(ROI_X[0], ROI_X[1])
    ax.set_ylim(bottom=0, top=250)#global_max * 1.05)
    
    ax.set_xlabel("Distance (nm)")
    ax.set_ylabel("Energy (kJ/mol)")
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    title = ax.set_title("")

    print(f"Generando {N_FRAMES} frames en {frames_dir} ...")

    for k, i in enumerate(frame_indices):
        Fi = compute_fes_profile(grid, D0, sigma, h, n_hills=i + 1, norm_roi=ROI_X)
        line.set_data(grid, Fi)
        title.set_text(f"HILLS – hill {i+1}/{total} (time = {time_ns[i]:.1f} ns)")
        frame_path = os.path.join(frames_dir, f"frame_{k:05d}.png")
        fig.savefig(frame_path, dpi=250)

    plt.close(fig)
    
    out_movie = os.path.join(out_dir, "fes_movie.mp4")
    cmd = [
        "ffmpeg", "-y", "-framerate", "15",
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-qscale:v", "1", out_movie,
    ]
    print("Llamando a ffmpeg para crear el vídeo...")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Vídeo creado: {out_movie}")
    except subprocess.CalledProcessError as e:
        print("⚠ ffmpeg ha fallado; se conservan los PNG en", frames_dir)
        print(e.stderr)


def make_movie(hills_file, out_dir, fields, data, D0, sigma, h):
    """
    Genera un vídeo de la FES acumulada (estilo gradiente)
    CON BARRA DE COLOR en ns (tiempo absoluto, 0 -> final)
    """
    try:
        idx_time = fields.index("time")
    except ValueError:
        print("No hay columna 'time' en el HILLS; no se puede hacer el vídeo de gradiente.")
        return

    time_ps = data[:, idx_time]
    time_ns = time_ps / 1000.0
    total = len(D0)
    
    t_min_val = time_ns[0]
    t_max_val = time_ns[-1]
    cbar_label = "Time (ns)"
    
    ROI_X = (0, 7) 
    Dmin, Dmax = D0.min() - 2 * sigma.max(), D0.max() + 2 * sigma.max()
    grid = np.linspace(Dmin, Dmax, 400)
    
    roi_indices = np.where((grid >= ROI_X[0]) & (grid <= ROI_X[1]))
    if roi_indices[0].size == 0:
        roi_indices = np.where((grid >= grid.min()) & (grid <= grid.max()))

    N_FRAMES = min(200, total)
    frame_indices = np.linspace(0, total - 1, N_FRAMES, dtype=int)

    profiles = []
    for i in frame_indices:
        Fi = compute_fes_profile(grid, D0, sigma, h, n_hills=i + 1, norm_roi=ROI_X)
        profiles.append(Fi)
    profiles = np.array(profiles)

    global_max = profiles[:, roi_indices[0]].max()

    frames_dir = os.path.join(out_dir, "_frames_fes_movie_grad")
    os.makedirs(frames_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 5), dpi=200)
    cmap = plt.get_cmap("Blues")
    
    norm = plt.Normalize(vmin=t_min_val, vmax=t_max_val)
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    print(f"Generando {N_FRAMES} frames en {frames_dir} ...")

    for k in range(N_FRAMES):
        ax.clear()
        ax.set_xlim(ROI_X[0], ROI_X[1])
        ax.set_ylim(bottom=0, top=250)#global_max * 1.05)
        ax.set_xlabel("Distance (nm)")
        ax.set_ylabel("Energy (kJ/mol)")
        i_hill = frame_indices[k]
        ax.set_title(f"HILLS – hill {i+hill+1}/{total} (time = {time_ns[i_hill]:.1f} ns)")

        for j in range(k + 1):
            Fi = profiles[j]
            current_hill_index = frame_indices[j]
            current_time = time_ns[current_hill_index]
            color = cmap(norm(current_time))
            alpha_frac = j / (N_FRAMES - 1) 
            alpha = 0.2 + 0.8 * alpha_frac
            rgba = list(color)
            rgba[-1] = alpha
            ax.plot(grid, Fi, color=rgba, linewidth=1)

        cbar = fig.colorbar(sm, ax=ax, label=cbar_label)
        frame_path = os.path.join(frames_dir, f"frame_{k:05d}.png")
        fig.savefig(frame_path, dpi=fig.dpi)
        cbar.remove()

    plt.close(fig)

    out_movie_mp4 = os.path.join(out_dir, "fes_movie_gradient.mp4")
    cmd_mp4 = [
        "ffmpeg", "-y", "-framerate", "15",
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-qscale:v", "1", out_movie_mp4,
    ]
    print("Llamando a ffmpeg para crear el vídeo MP4...")
    try:
        subprocess.run(cmd_mp4, check=True, capture_output=True, text=True)
        print(f"Vídeo MP4 creado: {out_movie_mp4}")
    except subprocess.CalledProcessError as e:
        print("⚠ ffmpeg ha fallado al crear MP4.")
        print(e.stderr)


def main():
    if not (3 <= len(sys.argv) <= 4):
        print("Uso: python hills_fes.py /ruta/al/HILLS /ruta/salida [movie]")
        sys.exit(1)

    hills_file = sys.argv[1]
    out_dir = sys.argv[2]
    make_movie_flag = len(sys.argv) == 4 and sys.argv[3].lower() in ("movie", "--movie")

    if not os.path.isfile(hills_file):
        print(f"ERROR: no existe el archivo HILLS: {hills_file}")
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)
    
    ROI_X = (0, 7) # Region Of Interest
    
    # --- MODIFICADO: Límite inferior para la integración del "pozo" ---
    # Este es el valor "que elige el usuario"
    OCCUPIED_START_X = 1.81 # <-- ¡Elige el inicio del "pozo" (ocupado) aquí!
    # ---

    # ---- leer HILLS ----
    fields = read_fields(hills_file)
    data = np.loadtxt(hills_file)

    try:
        idx_Dz = fields.index(D) #D.z si es membrana; D si es LPA
        idx_sigma = fields.index(f"sigma_{D}") #sigma_D.z si es membrana; D si es LPA
        idx_h = fields.index("height")
    except ValueError as e:
        raise RuntimeError(f"Faltan columnas necesarias en HILLS: {e}")

    D0 = data[:, idx_Dz]
    sigma = data[:, idx_sigma]
    h = data[:, idx_h]

    # ---- grilla en D.z ----
    Dmin, Dmax = D0.min() - 2 * sigma.max(), D0.max() + 2 * sigma.max()
    grid = np.linspace(Dmin, Dmax, 400)
    
    roi_indices = np.where((grid >= ROI_X[0]) & (grid <= ROI_X[1]))
    if roi_indices[0].size == 0:
        plot_indices = np.arange(len(grid))
    else:
        # Asegurarnos que plot_indices es un array simple
        plot_indices = roi_indices[0] 

    # ---- FES acumulada y snapshots ----
    
    # --- Lógica para la "cuenta atrás" de 100 ns ---
    total = len(D0)
    try:
        idx_time = fields.index("time")
        time_ps = data[:, idx_time]
        time_ns = time_ps / 1000.0 
        
        time_total_ns = time_ns[-1]
        time_start_window_ns = time_total_ns - 100.0 # 100 ns
        
        start_index_100ns = np.searchsorted(time_ns, time_start_window_ns)
        start_index_100ns = max(0, start_index_100ns)
        
        t_min_cbar = -100.0  # El más antiguo (claro)
        t_max_cbar = 0.0     # El más reciente (oscuro)
        cbar_label = "Time before end (ns)"
        
        N_HILLS_100NS = total - start_index_100ns
        print(f"Detectados {N_HILLS_100NS} hills en los últimos 100 ns.")
        START_IDX_SNAPSHOTS = start_index_100ns
        TITLE_FIG_2 = "PMF"
        OUT_FIG_2 = "fes_convergence_100ns.png"

    except (ValueError, IndexError):
        # Fallback (cuenta atrás de Hill Index)
        print("No se encontró 'time', usando N_LAST=20000 hills por defecto.")
        N_LAST_FALLBACK = 20000
        if N_LAST_FALLBACK > total:
            N_LAST_FALLBACK = total
            
        START_IDX_SNAPSHOTS = total - N_LAST_FALLBACK
        
        t_min_cbar = -N_LAST_FALLBACK # El más antiguo (claro)
        t_max_cbar = 0                 # El más reciente (oscuro)
        cbar_label = "Hills before end"
        
        TITLE_FIG_2 = f"PMF"
        OUT_FIG_2 = f"fes_convergence_last_{N_LAST_FALLBACK}.png"
    # ---

    F = np.zeros_like(grid) 
    snapshots = [] 

    for i, (Di, si, hi) in enumerate(zip(D0, sigma, h)):
        F += hi * np.exp(-(grid - Di) ** 2 / (2 * si * si))
        if i >= START_IDX_SNAPSHOTS:
            snapshots.append(F.copy())

    # ---- Análisis de la FES Final (para líneas) ----
    F_final_raw = -F 
    min_val_in_roi = F_final_raw[plot_indices].min()
    F_final_norm = F_final_raw - min_val_in_roi

    # --- Lógica de derivadas para encontrar líneas ---
    
    # 1. Encontrar el Mínimo Global (dentro del ROI)
    min_idx_local = F_final_norm[plot_indices].argmin()
    min_idx_global = plot_indices[min_idx_local]
    min_x_coord = grid[min_idx_global]
    min_y_coord = F_final_norm[min_idx_global]

    # 2. Calcular derivada
    grid_roi = grid[plot_indices]
    fes_roi = F_final_norm[plot_indices]
    dF_roi = np.gradient(fes_roi, grid_roi[1] - grid_roi[0])
    
    plateau_start_x_coord = None
    plateau_start_y_coord = None

    # 3. Buscar el punto de inflexión (pendiente máxima) DESPUÉS del mínimo
    search_range_after_min = np.arange(min_idx_local, len(dF_roi))
    
    if search_range_after_min.size > 0:
        dF_after_min = dF_roi[search_range_after_min]
        positive_slopes_after_min_idx = np.where(dF_after_min > 0)[0]

        if positive_slopes_after_min_idx.size > 0:
            inflection_idx_local_in_range = positive_slopes_after_min_idx[dF_after_min[positive_slopes_after_min_idx].argmax()]
            inflection_idx_local_roi = search_range_after_min[inflection_idx_local_in_range]
            max_slope = dF_roi[inflection_idx_local_roi]
            
            # 4. Buscar el inicio del plateau DESPUÉS del p. de inflexión
            threshold_slope = max_slope * 0.05 
            search_range_for_plateau = np.arange(inflection_idx_local_roi, len(dF_roi))
            
            if search_range_for_plateau.size > 0:
                dF_in_plateau_range = dF_roi[search_range_for_plateau]
                plateau_start_local_indices = np.where(dF_in_plateau_range < threshold_slope)[0]
                
                if plateau_start_local_indices.size > 0:
                    plateau_start_idx_local_in_range = plateau_start_local_indices[0]
                    plateau_start_idx_local_roi = search_range_for_plateau[plateau_start_idx_local_in_range]
                    plateau_start_global_idx = plot_indices[plateau_start_idx_local_roi]
                    
                    plateau_start_x_coord = grid[plateau_start_global_idx]
                    plateau_start_y_coord = F_final_norm[plateau_start_global_idx]

    # Imprimir resultados
    print(f"Mínimo encontrado en D.z = {min_x_coord:.2f} (E = {min_y_coord:.1f})")
    if plateau_start_x_coord is not None:
        print(f"Inicio del plateau (pendiente < 5% max) en D.z = {plateau_start_x_coord:.2f} (E = {plateau_start_y_coord:.1f})")
    else:
        print("No se pudo detectar el inicio del plateau con la lógica de derivadas.")
    # ---
# =====================================
# 
#     # ---- figura 1: FES final ----
# 
# =====================================

    
    import matplotlib.gridspec as gridspec
    from matplotlib.lines import Line2D

    fig = plt.figure(figsize=(10, 6))
    gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1])

    # --- Subplot principal ---
    ax = fig.add_subplot(gs[0])
    ax.plot(grid, F_final_norm, color='black')
    ax.set_xlabel("Distance (nm)")
    ax.set_ylabel("Energy (kJ/mol)")
    ax.set_title("HILLS - Final FES")
    ax.set_xlim(ROI_X[0], ROI_X[1])
    plot_max = fes_roi.max()
    ax.set_ylim(bottom=0, top=250)#plot_max*1.05)

    # --- Draw lines (but NO text here) ---
    ax.axvline(x=min_x_coord, color='red', linestyle='--', linewidth=1)
    if plateau_start_y_coord is not None:
        ax.axhline(y=plateau_start_y_coord, color='black', linestyle='--', linewidth=1)
        ax.axvline(x=plateau_start_x_coord, color='orange', linestyle='--', linewidth=1)

    # --- Subplot inferior as a legend panel ---
    ax_leg = fig.add_subplot(gs[1])
    ax_leg.axis("off")

    # Legend entries with color patches
    legend_elements = [
        Line2D([0], [0], color='red', linestyle='--', lw=2, label=f"Minimum Distance = {min_x_coord:.2f} nm"),
        Line2D([0], [0], color='black', linestyle='--', lw=2, label=f"Plateau Energy = {plateau_start_y_coord:.1f} kJ/mol"),
        Line2D([0], [0], color='orange', linestyle='--', lw=2, label=f"Plateau Start = {plateau_start_x_coord:.2f} nm"),
    ]

    ax_leg.legend(
        handles=legend_elements,
        loc='center',
        ncol=3,
        frameon=False,
        fontsize=10
    )

    fig.tight_layout()
    out_fes = os.path.join(out_dir, "fes.png")
    fig.savefig(out_fes, dpi=600)
    plt.close(fig)
    print(f"Guardado: {out_fes}")

# =====================================
# 
#     # ---- figura 2: "Stride" de los últimos N (100 ns) ----
# 
# =====================================

    
    N_IN_SNAPSHOT = len(snapshots)
    
    if N_IN_SNAPSHOT == 0:
        print("No hay snapshots para la figura 2, saltando.")
    else:
        N_STRIDES = 100 
        if N_IN_SNAPSHOT < N_STRIDES:
            N_STRIDES = N_IN_SNAPSHOT
            
        indices_to_plot = np.linspace(0, N_IN_SNAPSHOT - 1, N_STRIDES, dtype=int)
        
        cmap = cm.get_cmap("Blues") 
        fig, ax = plt.subplots(figsize=(10, 5))

        all_snaps_norm = []
        for snap_idx in indices_to_plot:
            Fi_raw = -snapshots[snap_idx]
            min_in_roi = Fi_raw[plot_indices].min()
            Fi_norm = Fi_raw - min_in_roi
            all_snaps_norm.append(Fi_norm)
        
        if not all_snaps_norm:
             global_max_fig2 = 1.0 
        else:
            global_max_fig2 = max(f[plot_indices].max() for f in all_snaps_norm)

        for i, Fi_norm in enumerate(all_snaps_norm):
            frac = i / (N_STRIDES - 1) 
            color = cmap(frac)
            alpha = 0.2 + 0.8 * frac
            rgba = list(color)
            rgba[-1] = alpha
            ax.plot(grid, Fi_norm, color=rgba, linewidth=1)

        ax.set_xlabel("Distance (nm)")
        ax.set_ylabel("Energy (kJ/mol)")
        ax.set_title(TITLE_FIG_2)
        ax.set_xlim(ROI_X[0], ROI_X[1])
        ax.set_ylim(bottom=0, top=250)#global_max_fig2 * 1.05)
        
    # ---- figura 2: HILLS últimos 100 ns ----

    import matplotlib.gridspec as gridspec

    fig = plt.figure(figsize=(10, 6))
    gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1])

    ax = fig.add_subplot(gs[0])

    for i, Fi_norm in enumerate(all_snaps_norm):
        frac = i / (N_STRIDES - 1)
        color = cmap(frac)
        alpha = 0.2 + 0.8 * frac
        rgba = list(color)
        rgba[-1] = alpha
        ax.plot(grid, Fi_norm, color=rgba, linewidth=1)

    ax.set_xlabel("Distance (nm)")
    ax.set_ylabel("Energy (kJ/mol)")
    ax.set_title(TITLE_FIG_2)
    ax.set_xlim(ROI_X[0], ROI_X[1])
    ax.set_ylim(bottom=0, top=250)#global_max_fig2 * 1.05)

    # Líneas sin texto
    ax.axvline(x=min_x_coord, color='r', linestyle='--', linewidth=1.5)
    ax.axhline(y=plateau_start_y_coord, color='k', linestyle='--', linewidth=1.5)
    ax.axvline(x=plateau_start_x_coord, color='orange', linestyle='--', linewidth=1.5)

    # Colorbar
    norm = plt.Normalize(vmin=t_min_cbar, vmax=t_max_cbar)
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    fig.colorbar(sm, ax=ax, label=cbar_label)

    # --- SUBPLOT INFERIOR COMO LEYENDA ---
    ax_leg = fig.add_subplot(gs[1])
    ax_leg.axis("off")

    legend_elements = [
        Line2D([0], [0], color='red', linestyle='--', lw=2, label=f"Minimum Distance = {min_x_coord:.2f} nm"),
        Line2D([0], [0], color='black', linestyle='--', lw=2, label=f"Plateau Energy = {plateau_start_y_coord:.1f} kJ/mol"),
        Line2D([0], [0], color='orange', linestyle='--', lw=2, label=f"Plateau Start = {plateau_start_x_coord:.2f} nm"),
    ]

    ax_leg.legend(
        handles=legend_elements,
        loc='center',
        ncol=3,
        frameon=False,
        fontsize=fontsize_legend
    )


    fig.tight_layout()
    out_last = os.path.join(out_dir, OUT_FIG_2)
    fig.savefig(out_last, dpi=600)
    plt.close(fig)
    print(f"Guardado: {out_last}")



    # ---- vídeo opcional ----
    if make_movie_flag:
        print("\n--- Creando vídeo (estilo gradiente con colorbar) ---")
        make_movie(hills_file, out_dir, fields, data, D0, sigma, h)
        print("\n--- Creando vídeo (estilo simple) ---")
        make_movie_og(hills_file, out_dir, fields, data, D0, sigma, h)


    # --- NUEVO: Cálculo de DeltaG con dos elecciones de OCCUPIED_START_X ---
    if plateau_start_x_coord is not None and plateau_start_y_coord is not None:
        print("\n--- Calculando DeltaG por integración de áreas ---")

        # Caso 1: OCCUPIED_START_X = 0.0
        print("\n>>> Caso 1: occupied_start = 0.0 nm")
        K0, DeltaG0 = calculate_deltaG_from_areas(
            grid_x=grid,
            fes=F_final_norm,
            offset_energy=plateau_start_y_coord,
            occupied_start=0.0,                 # pozo desde 0.0 nm
            occupied_end=plateau_start_x_coord, # hasta el inicio del plateau
            total_start=0.0,                    # integración total desde 0.0
            total_end=ROI_X[1],                 # hasta 7.0 nm
            out_dir=out_dir
        )

        # Caso 2: OCCUPIED_START_X = x_min (mínimo de la FES)
        print(f"\n>>> Caso 2: occupied_start = x_min = {min_x_coord:.3f} nm")
        Kmin, DeltaGmin = calculate_deltaG_from_areas(
            grid_x=grid,
            fes=F_final_norm,
            offset_energy=plateau_start_y_coord,
            occupied_start=min_x_coord,         # pozo desde el mínimo de la FES
            occupied_end=plateau_start_x_coord, # hasta el inicio del plateau
            total_start=min_x_coord,            # integración total desde el mínimo
            total_end=ROI_X[1],                 # hasta 7.0 nm
            out_dir=out_dir
        )

        # Resumen limpio en pantalla
        print("\n=== Resumen ΔG (por integración de áreas) ===")
        if not np.isnan(DeltaG0):
            print(f"ΔG (occupied_start = 0.0 nm)              = {DeltaG0:.3f} kJ/mol")
        else:
            print("ΔG (occupied_start = 0.0 nm)              = indefinido (problemas numéricos).")

        if not np.isnan(DeltaGmin):
            print(f"ΔG (occupied_start = x_min = {min_x_coord:.3f} nm) = {DeltaGmin:.3f} kJ/mol")
        else:
            print(f"ΔG (occupied_start = x_min = {min_x_coord:.3f} nm) = indefinido (problemas numéricos).")
        print("=============================================\n")

    else:
        print("\nNo se pudo calcular DeltaG por integración, faltan datos del plateau.")


if __name__ == "__main__":
    main()