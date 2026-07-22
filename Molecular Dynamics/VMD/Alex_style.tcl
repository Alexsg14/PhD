# ============================================================
#   Created by: Alejandro Seco Gonzalez
#   Year: 2025
# ============================================================
proc style_alex {rep} {
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



	## Lipids


	### MATERIAL DEFAULT



	## Protein
	mol selection "resname MOL";
        mol representation Licorice 0.3 32;
        mol material AOChalky;
        mol color ColorID 23;
        mol addrep top;
        set nrep [expr {[molinfo $rep get numreps] - 1}]
        mol smoothrep $rep $nrep 0;
        
        mol selection "resname 0GB";
        mol representation Licorice 0.3 32;
        mol material AOEdgy;
        mol color ColorID 1;
        mol addrep top;
        set nrep [expr {[molinfo $rep get numreps] - 1}]
        mol smoothrep $rep $nrep 0;
        
        
        mol selection "index 168";
        mol representation Licorice 0.6 32;
        mol material BrushedMetal;
        mol color ColorID 20;
        mol addrep top;
        set nrep [expr {[molinfo $rep get numreps] - 1}]
        mol smoothrep $rep $nrep 0;
        
        mol selection "index 176";
        mol representation Licorice 0.6 32;
        mol material BrushedMetal;
        mol color ColorID 26;
        mol addrep top;
        set nrep [expr {[molinfo $rep get numreps] - 1}]
        mol smoothrep $rep $nrep 0;
        
        mol selection "index 181";
        mol representation Licorice 0.6 32;
        mol material BrushedMetal;
        mol color ColorID 32;
        mol addrep top;
        set nrep [expr {[molinfo $rep get numreps] - 1}]
        mol smoothrep $rep $nrep 0;
}
