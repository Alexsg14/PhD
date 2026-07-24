#!/bin/bash


# Formato de columnas definido en squeue:
# %.18i -> JOBID
# %.9P  -> PARTITION
# %.40j -> NAME (nombre del job)
# %.12u -> USER (usuario)
# %.8T  -> STATE (RUNNING, PENDING, etc.)
# %.10M -> TIME (tiempo usado)
# %.10l -> TIME_LIMIT (límite de tiempo)
# %.6D  -> NODES (número de nodos)
# %R    -> REASON (motivo si está pendiente)

squeue --format="%.18i %.9P %.40j %.12u %.8T %.10M %.10l %.6D %.19S %R" --me --sort=+j | \
awk '
{
  # $1 -> JOBID
  # $2 -> PARTITION
  # $3 -> NAME
  # $4 -> USER
  # $5 -> STATE
  # $6 -> TIME
  # $7 -> TIME_LIMIT
  # $8 -> NODES
  # $9 -> START_TIME
  # $10 -> REASON

  if ($5=="RUNNING") {
    # Verde para RUNNING
    printf "\033[32;1m" "%-12s %-20s %-35s %-15s %-12s %-12s %-12s %-20s \n", $1,$2,$3,$4,$5,$6,$7,$9
  } else if ($5=="PENDING") {
    # Rojo para PENDING
    printf "\033[31;1m" "%-12s %-20s %-35s %-15s %-12s %-12s %-12s %-20s %-45s\n", $1,$2,$3,$4,$5,$6,$7,$9,$10
  } else if ($5=="STATE") {
    # Amarillo para encabezado o estado general
    printf "\033[33;1m" "%-12s %-20s %-35s %-15s %-12s %-12s %-12s %-20s \n", $1,$2,$3,$4,$5,$6,$7,$9
  }
}'


tit=1

#echo -e "\033[5mCalculando bro..." | awk '{print"\033[37m" $1" "$2" "$3 " "$4}'
echo -e "\033[0m"

echo ''
echo -e "\033[1;37mTOTAL JOBS\033[m"

tot_job=`squeue --me | wc -l`
real_tot=$((tot_job - tit))
echo $real_tot
echo ''

echo -e "\033[1;91mPENDING JOBS\033[m"

cola=`squeue --me -t PENDING | wc -l`
real_cola=$((cola - tit))
echo $real_cola
echo ''

echo -e "\033[1;92mRUNNING JOBS\033[0m"
running=`squeue --me -t RUNNING | wc -l`
real_run=$((running - tit))
echo $real_run



star="\e[5;33m*\e[0m\e[1;32m"
dot="\e[5;37m.\e[0m\e[1;32m"
o="\e[0m\e[1;31mo\e[0m\e[1;32m"

echo -e ""


echo -e "\033[0m"


current_date_time="`date +%H:%M:%S`";
echo $current_date_time;

