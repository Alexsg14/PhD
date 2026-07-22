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

proc style_pep {rep} {
	
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
	color change rgb 0 1 1 1;

	### BACKGROUND
	color Display {Background} 0;


	### Display settings
	axes location off
	display shadows on
	display ambientocclusion on
	display depthcue on
	display cuedensity 0.09
	display reposition 600 1000
	display resize 1267 1000
	display projection Orthographic
	display nearclip set 0.01
	display farclip set 20.00
	display aoambient 1
	display aodirect 0.15
	
	display rendermode {Tachyon RTX RTRT}
	### MATERIAL DEFAULT
	# Delete "all" by default
	# First 0 is the Rep number; second 0 is the molecule_number
	mol delrep 0 $rep 



	## Lipids

	#~~~~~~Representation of Membrane~~~~~~~~

	#POPC
	#color change rgb 1 0.176 0.706 0.725; #Membrane

	# POPI
	#color change rgb 4 0.012 0.886 0.506; #Membrane

	# POPS
	#color change rgb 5 0.988 0.745 0.016; #Membrane
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Use Down below
	 

	# POPC
	color change rgb 1 0.042 0.746 0.640; #Analisis
	# POPE
	color change rgb 2 0.992 0.012 0.996; #Magenta
	# POPG
	color change rgb 3 0.992 0.012 0.016; #Red
	# POPI
	color change rgb 4 0.239 0.522 0.776; #Blue Google
	# POPS
	color change rgb 5 0.4 0.2 0.6;       #violet
	# CHOL
	color change rgb 6 0.992 0.992 0.016; #Yellow
	# CDL2
	color change rgb 7 0.455 0.106 0.278; #Wine
	# PO4
	color change rgb 8 0.350 0.350 0.350; #Grey

	# POPA
	color change rgb 15 0.012 0.886 0.506; #Analisis Roberto (jade)

	# DOPC
	color change rgb 17 0.810 0 0; #Red 2
	# DOPE
	color change rgb 18 0.890 0.350 0; #Orangeish
	# DOPS
	color change rgb 19 0.960 0.720 0; #ambar
	# DPSM
	color change rgb 20 0 0.900 0.040; #Light green



	## Aminoacids

	# ACIDIC RESIDUES {ASP(D), GLU(E)}
	color change rgb 9 1 0 0;

	# BASIC RESIDUES {LYS(K), ARG(R), HIS(H)}
	color change rgb 10 0.009999999776482582 0.03999999910593033 0.9300000071525574;

	# HYDROPHOBIC RESIDUES {GLY(G), ALA(A), VAL(V), ILE(I), LEU(L), TRP(W), PRO(P), PHE(F), MET(M), TYR(Y)}
	color change rgb 11 0.5 0.8999999761581421 0.4000000059604645;

	# POLAR RESIDUES {GLN(Q), THR(T), SER(S), ASN(N), CYS(C)}
	color change rgb 12 1 1 0;

	# BACKBONE
	color change rgb 13 0 0 0; 

	# WATER
	color change rgb 14 0.019999999552965164 0.3799999952316284 0.6700000166893005

	# REAL WATER
	color change rgb 16 0.030 0.567 1.000

	# APPLY COLOR TO AMINO ACIDS
	color Resname ASP 9;
	color Resname GLU 9;
	color Resname LYS 10;
	color Resname ARG 10;
	color Resname HIS 10;
	color Resname GLY 11;
	color Resname ALA 11;
	color Resname VAL 11;
	color Resname LEU 11;
	color Resname ILE 11;
	color Resname PRO 11;
	color Resname PHE 11;
	color Resname MET 11;
	color Resname TRP 11;
	color Resname SER 12;
	color Resname THR 12;
	color Resname CYS 12;
	color Resname TYR 12;
	color Resname ASN 12;
	color Resname GLN 12;


	### MATERIAL DEFAULT

	# PO4
	mol selection {name PO4 or name PO2 or name PO1};
	mol representation VDW 2 32;
	mol material AOChalky;
	mol color ColorID 8;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep off;

	# DOPC
	mol selection {resname DOPC and not name PO4};
	mol representation VDW 1.4 32;
	mol material AOChalky;
	mol color ColorID 17;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep off;
	
	# DPPC
	mol selection {resname DPPC and not name PO4};
	mol representation VDW 1.4 32;
	mol material AOChalky;
	mol color ColorID 17;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep off;
	

	# DOPE
	mol selection {resname DOPE and not name PO4};
	mol representation VDW 1.4 32;
	mol material AOChalky;
	mol color ColorID 18;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep off;

	# DOPS
	mol selection {resname DOPS and not name PO4};
	mol representation VDW 1.4 32;
	mol material AOChalky;
	mol color ColorID 19;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep off;

	# DPSM
	mol selection {resname DPSM and not name PO4};
	mol representation VDW 1.4 32;
	mol material AOChalky;
	mol color ColorID 20;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep off;
	
	# LPA
        mol selection {resname LPA and not name PO4};
	mol representation VDW 1.4 32;
	mol material AOChalky;
	mol color ColorID 15;
	mol addrep top; 
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep off;
	
	# POPA
        mol selection {resname POPA and not name PO4};
	mol representation VDW 1.4 32;
	mol material AOChalky;
	mol color ColorID 15;
	mol addrep top; 
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep off;

	# POPC
	mol selection {resname POPC and not name PO4};
	mol representation VDW 1.4 32;
	mol material AOChalky;
	mol color ColorID 1; 
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep off;

	# POPE
	mol selection {resname POPE and not name PO4};
	mol representation VDW 1.4 32;
	mol material AOChalky;
	mol color ColorID 2; 
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep off;

	# POPG
	mol selection {resname POPG and not name PO4};
	mol representation VDW 1.4 32;
	mol material AOChalky;
	mol color ColorID 3; 
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep off;

	# POPI
	mol selection {resname POPI and not name PO4};
	mol representation VDW 1.2 32;
	mol material AOChalky;
	mol color ColorID 4; 
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep off;
	
	# POPI
	mol selection {resname TBPI and not name PO4};
	mol representation VDW 1.2 32;
	mol material AOChalky;
	mol color ColorID 4; 
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep off;

	# POPS
	mol selection {resname POPS and not name PO4};
	mol representation VDW 1.4 32;
	mol material AOChalky;
	mol color ColorID 5; 
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep off;

	# CHOL
	mol selection {resname CHOL};
	mol representation VDW 1.4 32;
	mol material AOChalky;
	mol color ColorID 6; 
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep off;

	# CDL2
	mol selection {resname CDL2};
	mol representation VDW 1.4 32;
	mol material AOChalky;
	mol color ColorID 7; 
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep off;
	
	# CDL2
	mol selection {resname CARD};
	mol representation VDW 1.4 32;
	mol material AOChalky;
	mol color ColorID 7; 
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	mol showrep $rep $nrep off;
	





	## Peptide

	# Backbone
	mol selection {name BB};
	mol representation VDW 1.5 32;
	mol material AOChalky;
	mol color COLORID 32;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	
	#N / C TERM
	# Selección backbone
	set sel [atomselect top "name BB"];
	# Obtener lista de índices
	set idx [$sel get index];
	# Primer y último índice
	set firstBB [lindex $idx 0];
	set lastBB  [lindex $idx end];
	# Primer BB
	mol selection "index $firstBB";
	mol representation VDW 2.2 32;
	mol material AOChalky;
	mol color COLORID 27;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}];
	mol smoothrep $rep $nrep 7;
	# Último BB
	mol selection "index $lastBB";
	mol representation VDW 2.2 32;
	mol material AOChalky;
	mol color COLORID 28;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}];
	mol smoothrep $rep $nrep 7;

	# Acidic
	mol selection {(resname ASP or resname GLU) and not resname BB};
	mol representation VDW 1.3 32;
	mol material AOChalky;
	mol color COLORID 9;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;

	# Basic
	mol selection {(resname LYS ARG HIS) and not name BB}
	mol representation VDW 1.3 32;
	mol material AOChalky;
	mol color COLORID 10;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;

	# Hydrophobic
	mol selection {(resname VAL LEU ILE PRO PHE MET TRP) and not name BB} 
	mol representation VDW 1.3 32;
	mol material AOChalky;
	mol color COLORID 11;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;

	mol selection {(resname GLY ALA)} 
	mol representation VDW 1.5 32;
	mol material AOChalky;
	mol color COLORID 11;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;
	
	mol selection {(resname GLY)} 
	mol representation VDW 1.5 32;
	mol material AOChalky;
	mol color COLORID 11;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;

	mol selection {(resname ALA) and not name BB} 
	mol representation VDW 1.5 32;
	mol material AOChalky;
	mol color COLORID 11;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;

	# Polar
	mol selection {(resname SER THR CYS TYR ASN GLN) and not name BB}
	mol representation VDW 1.3 32;
	mol material AOChalky;
	mol color COLORID 12;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}]
	mol smoothrep $rep $nrep 7;


	## Water
	mol selection {resname W or resname PW}
	mol representation VDW 1.3 32;
	mol material AOChalky;
	mol color COLORID 14;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}];
	mol smoothrep $rep $nrep 7;
	#mol modselect $rep 20 "none";
	mol showrep $rep $nrep off;
	
	## Water
	mol selection {(resname W or resname PW) and within 20 of (resname ALA ASN ASP GLN GLU GLY HIS ILE LEU LYS MET PHE VAL)};
	mol representation VDW 1.3 32;
	mol material AOChalky;
	mol color COLORID 14;
	mol addrep top;
	# obtener el índice de la rep recién creada
	set nrep [expr {[molinfo $rep get numreps] - 1}];
	# activar update selection every frame
	mol selupdate $nrep $rep on;
	mol smoothrep $rep $nrep 7;

	#Water close down
	mol selection {(resname W or resname PW) and z>72 and z<100 and within 20 of name BB};
	mol representation VDW 1.3 32;
	mol material AOChalky;
	mol color COLORID 21;
	mol addrep top;
	# obtener el índice de la rep recién creada
	set nrep [expr {[molinfo $rep get numreps] - 1}];
	# activar update selection every frame
	mol selupdate $nrep $rep on;
	mol smoothrep $rep $nrep 7;
	
	#Water close up
	mol selection {(resname W or resname PW) and z>110 and z<138 and within 20 of name BB};
	mol representation VDW 1.3 32;
	mol material AOChalky;
	mol color COLORID 21;
	mol addrep top;
	# obtener el índice de la rep recién creada
	set nrep [expr {[molinfo $rep get numreps] - 1}];
	# activar update selection every frame
	mol selupdate $nrep $rep on;
	mol smoothrep $rep $nrep 7;
	
	# PO4 down
	mol selection {(name PO4 or name PO2 or name PO1) and z<110};
	mol representation VDW 2 32;
	mol material AOChalky;
	mol color ColorID 8;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}];
	mol smoothrep $rep $nrep 7;
	
	# PO4 up
	mol selection {(name PO4 or name PO2 or name PO1) and z>110};
	mol representation VDW 2 32;
	mol material AOChalky;
	mol color ColorID 8;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}];
	mol smoothrep $rep $nrep 7;
	
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
	mol selection {resname W or resname PW}
	mol representation QuickSurf 4.5 15.0 4.0 3.0; #4.5 15.0 4.0 3.0
	mol material RealWater;
	mol color COLORID 16;
	mol addrep top;
	set nrep [expr {[molinfo $rep get numreps] - 1}];
	mol smoothrep $rep $nrep 7;
	
	
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
