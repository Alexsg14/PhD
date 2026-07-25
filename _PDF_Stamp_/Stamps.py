# Stamps.py

from pathlib import Path
import fitz  # PyMuPDF
import random
import subprocess


# ============================================================
# CONFIGURACIÓN FÁCIL
# ============================================================

# Nombre del PDF que está dentro de la carpeta "PDF"
INPUT_PDF_NAME = "____Tesis_V1_Traducida_ASG_RGF_ASG_CON_AGRADECIMIENTOS_con_paginas_en_blanco_CORREGIDA_CAPD_FINAL_12062026.pdf"

# Nombre del PDF de salida
# OUTPUT_PDF_NAME = "Tesis_test_stamped_3D_peptide.pdf"
OUTPUT_PDF_NAME = "STAMPED_MIRROR____Tesis_V1_Traducida_ASG_RGF_ASG_CON_AGRADECIMIENTOS_con_paginas_en_blanco_CORREGIDA_CAPD_FINAL_12062026.pdf"

# Página desde la que se empieza a aplicar el stamp.
# 1 = primera página, 2 = segunda página, etc.
START_PAGE = 36

# Página en la que se deja de aplicar el stamp (inclusive).
# None = hasta el final del PDF.
FINAL_PAGE = None

# ── Modo alterno ──────────────────────────────────────────────
# Si True, el stamp se aplica una página sí, la siguiente no
# (Grupo A: 1ª, 3ª, 5ª... relativas a START_PAGE).
# Si False, el stamp se aplica en todas las páginas (comportamiento original).
ALTERNATE_MODE = True

# Si True (solo tiene efecto cuando ALTERNATE_MODE = True),
# las páginas del Grupo B (2ª, 4ª, 6ª...) TAMBIÉN reciben stamp,
# pero con su propia configuración de posición (ver abajo).
ALTERNATE_ALSO_STAMP_B = True
# ──────────────────────────────────────────────────────────────

# Posición del stamp para el Grupo A (o para todas las páginas si ALTERNATE_MODE = False):
# "bottom_right", "bottom_left", "top_right", "top_left", "custom"
POSITION_MODE = "custom"

# Tamaño del stamp en puntos PDF.
# 1 cm aprox = 28.35 puntos.
STAMP_WIDTH = 85  #50
STAMP_HEIGHT = 85 #50

# Márgenes respecto al borde de la página.
# 20 puntos aprox = 0,7 cm.
MARGIN_X = 1      #10
MARGIN_Y = 1      #10

# Solo se usa si POSITION_MODE = "custom".
# Coordenadas desde la esquina superior izquierda (Grupo A).
CUSTOM_X = 520 #530
CUSTOM_Y = 745 #755

# ── Posición del Grupo B ──────────────────────────────────────
# Solo tiene efecto cuando ALTERNATE_MODE = True y ALTERNATE_ALSO_STAMP_B = True.
#
# Opciones para POSITION_MODE_B:
#   "mirror"  → espejo horizontal automático de las coordenadas del Grupo A
#               (misma Y, X calculada como: page_width - CUSTOM_X - STAMP_WIDTH)
#   "custom"  → coordenadas manuales definidas en CUSTOM_X_B / CUSTOM_Y_B
#   También acepta: "bottom_right", "bottom_left", "top_right", "top_left"
POSITION_MODE_B = "mirror"

# Solo se usa si POSITION_MODE_B = "custom".
CUSTOM_X_B = 10
CUSTOM_Y_B = 745
# ──────────────────────────────────────────────────────────────

# Extensiones aceptadas
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

# Número de páginas aleatorias a previsualizar al terminar.
# Pon 0 para desactivar la previsualización.
PREVIEW_PAGES = 4

# Resolución de la preview (72 = calidad baja/rápida, 150 = media, 300 = alta)
PREVIEW_DPI = 120


# ============================================================
# RUTAS AUTOMÁTICAS
# ============================================================

# Carpeta donde está este script
BASE_DIR = Path(__file__).resolve().parent

# Carpeta PDF
PDF_DIR = BASE_DIR / "PDF"

# Carpeta Stamps
STAMPS_DIR = BASE_DIR / "peptide_3D_CORRECTED_sin_alpha"

# Carpeta Preview
PREVIEW_DIR = BASE_DIR / "Preview"

# PDF de entrada y salida
INPUT_PDF = PDF_DIR / INPUT_PDF_NAME
OUTPUT_PDF = PDF_DIR / OUTPUT_PDF_NAME


# ============================================================
# FUNCIONES
# ============================================================

def get_images(images_folder: Path):
    """Lee las imágenes de la carpeta Stamps ordenadas alfabéticamente."""
    if not images_folder.exists():
        raise FileNotFoundError(f"No existe la carpeta: {images_folder}")

    images = [
        p for p in images_folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]

    images.sort(key=lambda p: p.name.lower())

    if not images:
        raise FileNotFoundError(
            f"No se encontraron imágenes PNG/JPG/WEBP en: {images_folder}"
        )

    return images


def get_stamp_rect(page, position_mode: str, custom_x=None, custom_y=None):
    """
    Calcula dónde poner el stamp.

    PyMuPDF usa coordenadas con origen arriba a la izquierda:
    - X crece hacia la derecha
    - Y crece hacia abajo

    custom_x / custom_y permiten pasar coordenadas externas (p. ej. para el Grupo B).
    Si no se pasan, se usan CUSTOM_X / CUSTOM_Y globales.
    """
    page_rect = page.rect
    page_width = page_rect.width
    page_height = page_rect.height

    if position_mode == "bottom_right":
        x0 = page_width - MARGIN_X - STAMP_WIDTH
        y0 = page_height - MARGIN_Y - STAMP_HEIGHT

    elif position_mode == "bottom_left":
        x0 = MARGIN_X
        y0 = page_height - MARGIN_Y - STAMP_HEIGHT

    elif position_mode == "top_right":
        x0 = page_width - MARGIN_X - STAMP_WIDTH
        y0 = MARGIN_Y

    elif position_mode == "top_left":
        x0 = MARGIN_X
        y0 = MARGIN_Y

    elif position_mode == "custom":
        x0 = custom_x if custom_x is not None else CUSTOM_X
        y0 = custom_y if custom_y is not None else CUSTOM_Y

    elif position_mode == "mirror":
        # Espejo horizontal del Grupo A: misma Y, X reflejada respecto al ancho de página.
        x0 = page_width - CUSTOM_X - STAMP_WIDTH
        y0 = CUSTOM_Y

    else:
        raise ValueError(
            "POSITION_MODE no válido. Usa: bottom_right, bottom_left, "
            "top_right, top_left, custom o mirror."
        )

    x1 = x0 + STAMP_WIDTH
    y1 = y0 + STAMP_HEIGHT

    return fitz.Rect(x0, y0, x1, y1)


def generate_preview(pdf_path: Path, n_pages: int = PREVIEW_PAGES, dpi: int = PREVIEW_DPI):
    """Renderiza n páginas aleatorias del PDF como PNG y las abre con el visor."""
    if n_pages <= 0:
        return

    PREVIEW_DIR.mkdir(exist_ok=True)

    # Borra previews anteriores
    for old in PREVIEW_DIR.glob("preview_*.png"):
        old.unlink()

    doc = fitz.open(pdf_path)
    total = len(doc)
    sample_count = min(n_pages, total)
    chosen = sorted(random.sample(range(total), sample_count))

    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    saved_paths = []

    print(f"\nGenerando preview de {sample_count} páginas aleatorias...")
    for page_index in chosen:
        page = doc[page_index]
        pix = page.get_pixmap(matrix=mat, alpha=False)
        out_path = PREVIEW_DIR / f"preview_pag{page_index + 1:04d}.png"
        pix.save(str(out_path))
        saved_paths.append(out_path)
        print(f"  → Página {page_index + 1} guardada en {out_path.name}")

    doc.close()

    # Abre las imágenes con el visor del sistema
    print("\nAbriendo previews...")
    for p in saved_paths:
        subprocess.Popen(["xdg-open", str(p)])

    print(f"Las previews están guardadas en: {PREVIEW_DIR}")


def stamp_pdf():
    if not INPUT_PDF.exists():
        raise FileNotFoundError(f"No se encontró el PDF: {INPUT_PDF}")

    if START_PAGE < 1:
        raise ValueError("START_PAGE debe ser 1 o mayor.")

    images = get_images(STAMPS_DIR)

    doc = fitz.open(INPUT_PDF)

    start_index = START_PAGE - 1
    end_index = len(doc) if FINAL_PAGE is None else min(FINAL_PAGE, len(doc))

    if start_index >= len(doc):
        raise ValueError(
            f"El PDF tiene {len(doc)} páginas, pero START_PAGE es {START_PAGE}."
        )

    if FINAL_PAGE is not None and FINAL_PAGE < START_PAGE:
        raise ValueError(
            f"FINAL_PAGE ({FINAL_PAGE}) debe ser mayor o igual que START_PAGE ({START_PAGE})."
        )

    image_index = 0

    for page_index in range(start_index, end_index):
        page = doc[page_index]

        # Determina si la página pertenece al Grupo A o al Grupo B
        # (0, 2, 4... → Grupo A | 1, 3, 5... → Grupo B, relativo a START_PAGE)
        relative = page_index - start_index
        is_group_a = (relative % 2 == 0)

        if ALTERNATE_MODE:
            if is_group_a:
                # ── Grupo A: stamp con posición principal ──
                image_path = images[image_index % len(images)]
                rect = get_stamp_rect(page, POSITION_MODE)
                page.insert_image(
                    rect,
                    filename=str(image_path),
                    keep_proportion=True,
                    overlay=True,
                )
                print(f"Página {page_index + 1} [Grupo A]: añadido {image_path.name}")
                image_index += 1
            else:
                if ALTERNATE_ALSO_STAMP_B:
                    # ── Grupo B: stamp con posición alternativa ──
                    image_path = images[image_index % len(images)]
                    rect = get_stamp_rect(
                        page,
                        POSITION_MODE_B,
                        custom_x=CUSTOM_X_B,
                        custom_y=CUSTOM_Y_B,
                    )
                    page.insert_image(
                        rect,
                        filename=str(image_path),
                        keep_proportion=True,
                        overlay=True,
                    )
                    print(f"Página {page_index + 1} [Grupo B]: añadido {image_path.name}")
                    image_index += 1
                else:
                    print(f"Página {page_index + 1} [Grupo B]: sin stamp (ALTERNATE_ALSO_STAMP_B = False)")
        else:
            # ── Modo normal: stamp en todas las páginas ──
            image_path = images[image_index % len(images)]
            rect = get_stamp_rect(page, POSITION_MODE)
            page.insert_image(
                rect,
                filename=str(image_path),
                keep_proportion=True,
                overlay=True,
            )
            print(f"Página {page_index + 1}: añadido {image_path.name}")
            image_index += 1

    doc.save(OUTPUT_PDF, garbage=4, deflate=True)
    doc.close()

    print()
    print("Listo.")
    print(f"PDF original: {INPUT_PDF}")
    print(f"PDF generado: {OUTPUT_PDF}")
    print(f"Stamps usados desde: {STAMPS_DIR}")
    print(f"Página inicial: {START_PAGE}")
    print(f"Página final: {FINAL_PAGE if FINAL_PAGE is not None else 'última (' + str(len(fitz.open(OUTPUT_PDF))) + ')'}")
    print(f"Posición: {POSITION_MODE}")

    generate_preview(OUTPUT_PDF)


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    stamp_pdf()