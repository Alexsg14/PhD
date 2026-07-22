#!/usr/bin/env bash

: <<'DOCSTRING'
===============================================================================
 Master Script for HILLS / FES / PMF Analysis
===============================================================================

This master script wraps the Python analysis tool and adds convenient flags
to control which outputs are generated. It can compute FES curves, create
movies, apply restricted plotting limits, and perform PMF analysis including
plateau detection and ΔG estimation by integration.

-------------------------------------------
 Available Flags
-------------------------------------------

  --movie
      Generates both video types:
        • fes_movie.mp4               – simple curve evolution
        • fes_movie_gradient.mp4      – cumulative gradient-style movie
      If not used, no videos are produced.

  --limits
      Activates restricted X-range plotting (ROI) during FES figure generation.
      Output filenames receive a "_fit" suffix to avoid overwriting standard ones.
         Examples:
            fes.png            →   fes_fit.png
            fes_last_2000.png  →   fes_last_2000_fit.png

      Works only for the static FES figures, not for PMF.

  --pmf
      Runs the PMF analysis module:
         • Detects minimum and plateau regions
         • Creates PMF.png
         • Creates PMF_last_<N>.png
         • Computes ΔG via area integration with detailed printed output
           (two definitions of "occupied region": from 0 nm and from the FES minimum)

      If plateau cannot be detected, the script continues normally and
      only prints a warning (ΔG not evaluated).

  --help
      Displays this help description.

-------------------------------------------
 Basic Usage
-------------------------------------------

  ./myscript.sh HILLS output_folder
  ./myscript.sh HILLS output_folder --movie
  ./myscript.sh HILLS output_folder --limits
  ./myscript.sh HILLS output_folder --pmf
  ./myscript.sh HILLS output_folder --movie --pmf --limits

-------------------------------------------
 Flag Combination Rules
-------------------------------------------

  * --movie + --limits  
        Movies are generated normally. Plots use ROI-only if --limits is set.

  * --pmf + --limits  
        PMF analysis ignores the FES-limits ROI (PMF uses its own logic).  
        Only the FES-* images get the "_fit" suffix.

  * --pmf only  
        Generates PMF images and ΔG but does **not** modify FES images.

  * --colvar $COLVAR_NAME only 
        Plots the COLVAR document

  * No flags  
        Only standard FES images (fes.png, fes_last_*.png) are produced.


-------------------------------------------
 Notes
-------------------------------------------

  - No output is ever overwritten unless explicitly intended.
  - If a plateau cannot be reliably detected, PMF runs safely and provides
    clean results without raising errors.
  - Time handling is automatic: uses "time" column if present, otherwise
    falls back to hill index.

===============================================================================
DOCSTRING

# =====================================
# 
# kappa menor a la habitual (walls sin pbc)
# 
# =====================================

# ------------------------> NO

path="${PMF_BASE_PATH:-/mnt/netapp1/RES_SuPepMem/ALEX/_PMF_Peptidomica}"

folder="kappa1000_POPC" 

f="${path}/${folder}"
h="HILLS_WT"
output="${f}/TODO_PMF"


# python hills_video.py $f/$h $output #--movie
# python hills_video.py $f/$h $output --limits #--movie
# python meta_diagnose.py $f/COLVAR_WT --cv-name D.z --roi-min 0.0 --roi-max 7.0 --lower-wall -1.0 --upper-wall 9.0
# python hills_video.py $f/$h $output --colvar $f/COLVAR_WT --no-hills
# # python hills_video.py $f/$h $output --pmf ---------> CUANDO TENGA PLATEAU


# ------------------------> NO
path="${PMF_BASE_PATH:-/mnt/netapp1/RES_SuPepMem/ALEX/_PMF_Peptidomica}"

folder="kappa2000_POPC" 

f="${path}/${folder}"
h="HILLS_WT"
output="${f}/TODO_PMF"


# python hills_video.py $f/$h $output #--movie
# python hills_video.py $f/$h $output --limits #--movie
# python meta_diagnose.py $f/COLVAR_WT --cv-name D.z --roi-min 0.0 --roi-max 7.0 --lower-wall -1.0 --upper-wall 9.0
# python hills_video.py $f/$h $output --colvar $f/COLVAR_WT --no-hills
# # python hills_video.py $f/$h $output --pmf ---------> CUANDO TENGA PLATEAU

# --------------------

path="${PMF_BASE_PATH:-/mnt/netapp1/RES_SuPepMem/ALEX/_PMF_Peptidomica}"

folder="kappa1000_COV" 

f="${path}/${folder}"
h="HILLS_WT"
output="${f}/TODO_PMF"


# python hills_video.py $f/$h $output #--movie
# python hills_video.py $f/$h $output --limits #--movie
# python meta_diagnose.py $f/COLVAR_WT --cv-name D.z --roi-min 0.0 --roi-max 7.0 --lower-wall -1.0 --upper-wall 9.0
# python hills_video.py $f/$h $output --colvar $f/COLVAR_WT --no-hills
# python hills_video.py $f/$h $output --pmf #---------> CUANDO TENGA PLATEAU



path="${PMF_BASE_PATH:-/mnt/netapp1/RES_SuPepMem/ALEX/_PMF_Peptidomica}"

folder="kappa2000_COV" 

f="${path}/${folder}"
h="HILLS_WT"
c="COLVAR_WT"
output="${f}/TODO_PMF"


# python hills_video.py $f/$h $output --movie
# python hills_video.py $f/$h $output --limits #--movie
# python meta_diagnose.py $f/COLVAR_WT --cv-name D.z --roi-min 0.0 --roi-max 7.0 --lower-wall -1.0 --upper-wall 9.0
# python hills_video.py $f/$h $output --colvar $f/$c --no-hills
#python hills_video.py $f/$h $output --pmf #---------> CUANDO TENGA PLATEAU

# # =====================================
# # 
# # =====================================
# # 
# # TEST_WALLS (nopbc)
# # 
# # ===================================== 
# # 
# # =====================================


# # =====================================
# # 
# # WELL TEMPERED
# # 
# # =====================================

path="${PMF_BASE_PATH:-/mnt/netapp1/RES_SuPepMem/ALEX/_PMF_Peptidomica}"

folder="TEST_WALLS_POPC" 

f="${path}/${folder}"
h="HILLS_WT"
c="COLVAR_WT"
output="${f}/TODO_PMF"


# python hills_video.py $f/$h $output #--movie
# python hills_video.py $f/$h $output --limits #--movie
# python meta_diagnose.py $f/COLVAR_WT --cv-name D.z --roi-min 0.0 --roi-max 7.0 --lower-wall -1.0 --upper-wall 9.0
# python hills_video.py $f/$h $output --colvar $f/$c --no-hills
#python hills_video.py $f/$h $output --pmf #---------> CUANDO TENGA PLATEAU


path="${PMF_BASE_PATH:-/mnt/netapp1/RES_SuPepMem/ALEX/_PMF_Peptidomica}"

folder="TEST_WALLS_COV"

f="${path}/${folder}"
h="HILLS_030226"
c="COLVAR_WT"
output="${f}/TODO_PMF_030226_v2"

# python hills_video.py $f/$h $output #--movie
# python hills_video.py $f/$h $output --limits #--movie
# python meta_diagnose.py $f/COLVAR_WT --cv-name D.z --roi-min 0.0 --roi-max 7.0 --lower-wall -1.0 --upper-wall 9.0
# python hills_video.py $f/$h $output --colvar $f/$c --no-hills
python hills_video.py $f/$h $output --pmf #---------> CUANDO TENGA PLATEAU



# =====================================
# 
# =====================================
# 
# los que no eran tests
# 
# ===================================== 
# 
# =====================================
path="${PMF_BASE_PATH:-/mnt/netapp1/RES_SuPepMem/ALEX/_PMF_Peptidomica}"

folder="Par_COV"

f="${path}/${folder}"
h="HILLS"
output="${f}/TODO_PMF"

# python hills_video.py $f/$h $output #--movie
# python hills_video.py $f/$h $output --limits #--movie

# python meta_diagnose.py $f/COLVAR --cv-name D.z --roi-min 0.0 --roi-max 7.0 --lower-wall -1.0 --upper-wall 9.0
# python hills_video.py $f/$h $output --colvar $f/COLVAR --no-hills
# python hills_video.py $f/$h $output --pmf #---------> CUANDO TENGA PLATEAU


# =====================================
# 
# Este no me vale vvvv porque habria que multiplicar por -1
# 
# ===================================== 

# python hills_video.py $f/$h $output --pmf #---------> CUANDO TENGA PLATEAU


path="${PMF_BASE_PATH:-/mnt/netapp1/RES_SuPepMem/ALEX/_PMF_Peptidomica}"

folder="Par_POPC"

f="${path}/${folder}"
h="HILLS"
c="COLVAR"
output="${f}/TODO_PMF_030226"

# python hills_video.py $f/$h $output #--movie
# python hills_video.py $f/$h $output --limits #--movie

# python meta_diagnose.py $f/COLVAR --cv-name D.z --roi-min 0.0 --roi-max 7.0 --lower-wall -1.0 --upper-wall 9.0
# python hills_video.py $f/$h $output --colvar $f/$c --no-hills

#python hills_video.py $f/$h $output --pmf #---------> CUANDO TENGA PLATEAU


