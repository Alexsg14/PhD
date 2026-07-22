#!/usr/bin/env bash

path="${PMF_BASE_PATH:-/mnt/netapp1/RES_SuPepMem/ALEX/_PMF_Peptidomica}"

folder="POPC_lowWALLS_test"

f="${path}/${folder}"
h="HILLS_WT"
c="COLVAR_WT"
output="${f}/TODO_PMF"

python hills_video.py $f/$h $output #--movie
# python hills_video.py $f/$h $output --limits #--movie

# python meta_diagnose.py $f/COLVAR --cv-name D.z --roi-min 0.0 --roi-max 7.0 --lower-wall -1.0 --upper-wall 9.0
python hills_video.py $f/$h $output --colvar $f/$c --no-hills

# python hills_video.py $f/$h $output --pmf #---------> CUANDO TENGA PLATEAU
