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

proc style {rep} {
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
	mol selection protein;
        mol representation NewCartoon 0.3 32;
        mol material Edgy;
        mol color ColorID 6;
        mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep on;
        
        mol selection "chain A";
        mol representation NewCartoon 0.3 32;
        mol material Edgy;
        mol color ColorID 22;
        mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep on;
        
        mol selection "chain B";
        mol representation NewCartoon 0.3 32;
        mol material Edgy;
        mol color ColorID 9;
        mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep on;
	
	#Protein Licorice

       	#mol selection protein;
        #mol representation Licorice 0.3 32;
        #mol material AOChalky;
        #mol color Structure;
        #mol addrep top;
	#set nrep [expr {[molinfo $rep get numreps] - 1}]
	#mol smoothrep $rep $nrep 7;
	#mol showrep $rep $nrep on;
        
	# Ligand
	mol selection "not protein and not resname SOL NA";
        mol representation Licorice 0.3 32;
        mol material AOChalky;
        mol color ColorID 17;
        mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep on;
        
        # Surface Protein near Ligand
        #mol selection "protein and within 8 of (not protein and not resname SOL NA)";
	#mol representation Surf 1.600000 0.000000;
	#mol material AOChalky;
	#mol color ColorID 23; 
	#mol addrep top;
	#set nrep [expr {[molinfo $rep get numreps] - 1}]
	#mol smoothrep $rep $nrep 7;
	#mol showrep $rep $nrep on;

	##SOL
	#mol selection resname SOL;
        #mol representation VDW 1.3 32;
        #mol material AOChalky;
        #mol color COLORID 14;
        #mol addrep top;
	#set nrep [expr {[molinfo $rep get numreps] - 1}]
	#mol smoothrep $rep $nrep 7;
	#mol showrep $rep $nrep on;
        #mol modselect $rep 20 "none";
	

	##RealWater
	set material_list [material list]	
	if {[lsearch $material_list "RealWater"] == -1} {
		material add RealWater
	}
	material change ambient RealWater 0.000
	material change specular RealWater 0.430
	material change diffuse RealWater 0.280
	material change shininess RealWater 0.500
	material change mirror RealWater 0.000
	material change opacity RealWater 0.080
	#mol selection resname SOL
	#mol material RealWater;
	#mol color COLORID 16;
	#mol addrep top;
	#mol smoothrep $rep 6 7;
	
	
	#RealWater anterior
	#material add RealWater
	#material change ambient RealWater 0.150
	#material change specular RealWater 0.250
	#material change diffuse RealWater 0.360
	#material change shininess RealWater 1.000
	#material change mirror RealWater 0.010
	#material change opacity RealWater 0.250
	#mol selection {resname W or resname PW}
	#mol representation QuickSurf 3.0 3.0 0.5 3.0;
	#mol material RealWater;
	#mol color COLORID 16;
	#mol addrep top;
	#mol smoothrep $rep 21 7;
}
