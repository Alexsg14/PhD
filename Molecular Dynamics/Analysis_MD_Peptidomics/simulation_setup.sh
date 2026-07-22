#!/bin/bash

'''
README NOTE: THERE IS A DETAILED README IN THIS DIRECTORY!!!

GUIDE ON HOW TO RUN PEPTIDOMICS SIMULATIONS
'''
#Peptide creation with Vermouth, applying Martini3 forcefield.

module load cesga/system miniconda3/22.11.1-1

#Poniendo asi ya se activa el entorno de python con vermouth (no es de conda). Para desactivarlo simplemente poner deactivate
#sin poner -ff martini3001, ya coge directamente martini3 por defecto
martinize2 -f ../AP00485_Z.pdb -x AP00485_CG_Z.pdb -o AP00485_CG_Z.top -ss HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH -maxwarn 1
#Parasin-I
martinize2 -f ParasinI_Z.pdb -x ParasinI_CG_Z.pdb -o ParasinI_CG_Z.top -ss HHHHHHHHHHHHHHHHHHH -maxwarn 1



# This is a script to prepare and run a Martini simulation of a peptide in a membrane environment.

# For the peptide simulation in water

gmx insert-molecules -ci ../*.pdb -box 12 12 12 -nmol 1 -radius 0.21 -try 500 -o peptide.gro;

cp ../molecule_0.itp . ;

gmx solvate -cp peptide.gro -cs water.gro  -o peptide_solv.gro -radius 0.21;

cat > "${1:-system_m3.top}" << 'EOF'
#include "toppar_m3_TC4_0/martini_v3.0.0.itp"
#include "molecule_0.itp"
#include "toppar_m3_TC4_0/martini_v3.0.0_nucleobases_v1.itp"
#include "toppar_m3_TC4_0/martini_v3.0.0_phospholipids_v1.itp"
#include "toppar_m3_TC4_0/martini_v3.0.0_small_molecules_v1.itp"
#include "toppar_m3_TC4_0/martini_v3.0.0_solvents_v1.itp"
#include "toppar_m3_TC4_0/martini_v3.0.0_ions_v1.itp"
#include "toppar_m3_TC4_0/martini_v3.0.0_sugars_v1.itp"
#include "toppar_m3_TC4_0/martini_v3.0_sterols_v1.0.itp"


[ system ]
; name
Martini system

[ molecules ]
; name        number
molecule_0 1
EOF

echo "W $(grep -c W peptide_solv.gro)" >> system_m3.top;



gmx grompp -f minimization.mdp -c peptide_solv.gro -p system_m3.top -o mini.tpr;

#compute -c 4 --mem 2

gmx mdrun -v -deffnm mini -ntmpi 2;

gmx grompp -f minimization.mdp -c mini.gro -p system_m3.top -o ions.tpr;
 
echo -e 13 | gmx genion -s ions.tpr -neutral -p system_m3.top -o mini_ions.gro;

gmx grompp -f minimization.mdp -c mini_ions.gro -p system_m3.top -o mini_2.tpr;

gmx mdrun -v -deffnm mini_2 -ntmpi 2;

gmx select -s mini_2.tpr -f mini_2.gro -select 'group "System"; group "Protein"; group "W"; group "ION"; group "W" or group "ION"' -on index.ndx;\
 sed -i 's/^\[ group_"W"_or_group_"ION" \]/[ W_ION ]/' index.ndx


#echo -e "13|14\n\nq" | gmx make_ndx -f mini_2.gro ;

gmx grompp -f martini_eq.mdp -c mini_2.gro -p system_m3.top -o eq.tpr -n index.ndx -maxwarn 1;

gmx mdrun -v -deffnm eq -ntmpi 2;

gmx grompp -f martini_md.mdp -c eq.gro -p system_m3.top -n index.ndx -o md.tpr;

#sbatch run_pep.sh 

#Para luego insertarlo correctamente en la membrana
echo -e "1\n1\n" | gmx trjconv -f md.cpt -o pep_dry.gro -n index.ndx -s md.tpr -center -pbc mol;

# =====================================
# 
# 
# 
# =====================================

#La membrana esta sin agua en covid pero no en POPC. Para seguir este protocolo igual es mejor hacerlo tambien en POPC
# Now prepare the membrane with the peptide

gmx insert-molecules -f mem_noW.gro -ci pep_dry.gro -radius 0.21 -nmol 1 -try 500 -o MEM_PEP_DRY.gro

gmx solvate -cp MEM_PEP_DRY.gro -cs water.gro -o MEM_PEP_W.gro -radius 0.21 -scale 1 #0.57 por defecto

#Abrir el MEM_PEP_W.gro y cambiar el orden de peptido y agua. Ponemos el peptido de ultimo

#Vamos al MEM_PEP_W.gro con vim borramos los dos espacios que quedan vacios a la izquierda de cada linea del peptido y guardamos como MEM_PEP_W.gro

'''
> vim MEM_PEP_W.gro
> ctrl+v
> Hasta el final del agua
> x
'''

cat > system_m3.top <<EOF
#include "toppar_m3_TC4_0/martini_v3.0.0.itp"
#include "toppar_m3_TC4_0/martini_v3.0.0_ions_v1.itp"
#include "toppar_m3_TC4_0/martini_v3.0.0_nucleobases_v1.itp"
#include "toppar_m3_TC4_0/martini_v3.0.0_phospholipids_v1.itp"
#include "toppar_m3_TC4_0/martini_v3.0.0_small_molecules_v1.itp"
#include "toppar_m3_TC4_0/martini_v3.0.0_solvents_v1.itp"
#include "toppar_m3_TC4_0/martini_v3.0.0_sugars_v1.itp"
#include "toppar_m3_TC4_0/martini_v3.0_sterols_v1.0.itp"

#include "molecule_0.itp"


[ system ]
; name
Martini system

[ molecules ]
; name        number
POPC 274
POPE 126
POPS 10
TBPI 50
CHOL 30
CARD 10
W $(grep -c W MEM_PEP_W.gro)
molecule_0 1
EOF


gmx editconf -f MEM_PEP_W.gro -o MEM_PEP_W_ordered.gro -resnr 1;

gmx grompp -f minimization.mdp -c MEM_PEP_W_ordered.gro -p system_m3.top -o ions.tpr -maxwarn 1;

echo -e 8 | gmx genion -s ions.tpr -o MEM_PEP_IONS.gro -p system_m3.top -neutral;

#Hay que hacer resnr 1 porque los iones hacen que cambie la numeracion y POPC no empieza en 1

gmx editconf -f MEM_PEP_IONS.gro -o MEM_PEP_IONS_resnr.gro -resnr 1;

#At this point, you can proceed with energy minimization, equilibration, and production MD as needed.

#compute -c 4 --mem 2

#minimizado
gmx grompp -f minimization.mdp -c MEM_PEP_IONS.gro -p system_m3.top -o mini.tpr -maxwarn 1

#Indice customizado
gmx select -s mini.tpr -f MEM_PEP_IONS.gro -select 'group "System"; group "Protein"; group "POPC"; group "POPE"; group "POPS"; group "TBPI";\
 group "CHOL" ; group "CARD"; group "POPC" or group "POPE" or group "POPS" or group "TBPI" or group "CHOL" or group "CARD";group "W";\
  group "Ion"; group "W" or group "Ion";' -on index.ndx;\
 sed -i 's/^\[ group_"W"_or_group_"Ion" \]/[ W_ION ]/' index.ndx;\
 sed -i 's/^\[ group_"POPC"_or_group_"POPE"_or_group_"POPS"_or_group_"TBPI"_or_group_"CHOL"_or_group_"CARD" \]/[ Lipids ]/' index.ndx

#Indice normal
echo -e "2|3|4|5|6|7\nname 30 Lipids\n8|9\nname 31 W_ION\n\nq" | gmx make_ndx -f MEM_PEP_IONS.gro -o index.ndx;



gmx mdrun -v -deffnm mini -ntmpi 2;

#equilibracion NVT
gmx grompp -f martini_eq_nvt.mdp -c mini.gro -p system_m3.top -o eq_nvt.tpr -n index.ndx -maxwarn 1;

gmx mdrun -v -deffnm eq_nvt -ntmpi 2;

#equilibracion NPT
gmx grompp -f martini_eq.mdp -c eq_nvt.gro -p system_m3.top -o eq_npt_020.tpr -n index.ndx -maxwarn 1;

gmx mdrun -v -deffnm eq_npt_020 -ntmpi 2;

#minimizado despues de la eq NPT
gmx grompp -f minimization.mdp -c eq_npt_020.gro -p system_m3.top -o mini_eq_npt.tpr -n index.ndx -maxwarn 1;

gmx mdrun -v -deffnm mini_eq_npt -ntmpi 2;

#equilibracion NPT 2
gmx grompp -f martini_eq.mdp -c mini_eq_npt.gro -p system_m3.top -o eq_npt2_020.tpr -n index.ndx -maxwarn 1;

gmx mdrun -v -deffnm eq_npt2_020 -ntmpi 2;


#produccion
gmx grompp -f martini_md.mdp -c eq_npt2_020.gro -p system_m3.top -o md_020.tpr -n index.ndx -maxwarn 1;


# =====================================
# 
# produccion con double-precision
# 
# =====================================
module load cesga/2020 gcc/system openmpi/4.0.5_ft3 gromacs/2021.1-double

gmx_d grompp -f martini_md.mdp -c eq_npt2_020.part0001.gro -n index.ndx -p system_m3.top -o md_20_d.tpr

export OMP_NUM_THREADS=8
gmx_d mdrun -v -deffnm md_20_d -ntomp 8 -ntmpi 2 -cpi -noappend #Cancelamos con CTRL+C

gmx_d trjconv -f md_20_d.cpt -s md_20_d.tpr -o md_20_d.gro 

# ===================================== Produccion normal

gromacs/2021.1

gmx grompp -f martini_md.mdp -c md_20_d.gro -n index.ndx -p system_m3.top -o md_20.tpr -maxwarn 1



#sbatch run_COV.sh (Con -c 2 -n 2)


# Preparar los .tpr sin trayectoria para las replicas en OPES

module load cesga/2020 gcc/system openmpi/4.1.4_ft3_cuda gromacs/2021.4-plumed-2.8.0



for i in `ls -d TEST_COV*`; do cd $i; pwd; echo $i; gmx grompp -f ../MDP_SIN_XTC.mdp -c eq_npt2_020.gro -n index.ndx\
 -p system_m3.top -o ${i##*_}_no_xtc.tpr -maxwarn 1 ; cd ..; done



tail -f "$(ls -t *.log | head -n1)"

tail "$(ls -t *.log | head -n1)"


"""
In case you want to analyze and later continue the trajectory:

If you concatenate and delete the XTC files by parts (in that order, please), then send the execution script normally, the trajectory will continue as usual. Nothing else is required.

If you later concatenate the previous one with the new parts, just place them in order and that's it.

VERIFIED WITH PAULA ON OCTOBER 22, 2025. CHECK THE LAB JOURNAL ON THAT DATE (NOTION).
"""
for i in `ls -d AP0*`; do cd $i; python ../modular_analysis.py -top md.tpr -traj traj_skip100.xtc --analyses tilt zcontacts rolling --rolling_skip 10 -out _RESULTS --time 5000 ; cd ..; done