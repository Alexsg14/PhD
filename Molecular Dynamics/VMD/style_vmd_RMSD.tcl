# ============================================================
#   Created by: Alejandro Seco Gonzalez
#   Year: 2025
# ============================================================

proc lastrep {molid} {
    expr {[molinfo $molid get numreps] - 1}
}

proc show {molid state} {
    set repid [lastrep $molid]
    mol showrep $molid $repid $state
}

proc style_RMSD {rep} {
	mol top $rep
	
	axes location off;
	light 0 on; 
	light 0 pos {0.027767 -0.111499 1.003392};
	light 1 off;
	light 2 off;
	light 3 on; 
	light 3 pos {-0.313564 1.371837 0.140526}

	### COLORS
	## Background
#	color change rgb 0 1 1 1;

	### BACKGROUND
	color Display {Background} 8;


	### Display settings
	axes location off
	display shadows on
	display ambientocclusion on
	display depthcue on
	display cuedensity 0.09
	display reposition 850 650
	display resize 1025 1000
	display projection Orthographic
	display nearclip set 0.01
	display farclip set 20.00
	display aoambient 1
	display aodirect 0.15
	
	#display dof_focaldist 0.55
	#display dof_fnumber 60

	display rendermode {Tachyon RTX RTRT}
	### MATERIAL DEFAULT
	# Delete "all" by default
	# First 0 is the Rep number; second 0 is the molecule_number
	mol delrep 0 $rep 

	# Escala de color por defecto
	color scale method cividis
	color scale min 0.12
	color scale midpoint 0.50
	color scale max 1.0



	## Lipids


	### MATERIAL DEFAULT



	## Protein
	mol selection protein;
        mol representation NewCartoon 0.3 32;
        mol material BrushedMetal;
        mol color ColorID 8;
        mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep on;
        
        mol selection protein;
        mol representation Licorice 0.3 32;
        mol material BrushedMetal;
        mol color ColorID 8;
        mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep on;
        
        mol selection protein;
        mol representation NewCartoon 0.3 32;
        mol material AOChalky;
        mol color Beta;
        mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep on;
	
	#Protein Licorice

	mol selection protein;
	mol representation Licorice 0.3 32;
	mol material AOChalky;
	mol color Beta;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep on;
        
        

}
