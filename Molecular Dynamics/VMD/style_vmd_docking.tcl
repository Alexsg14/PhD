# ============================================================
#   Custom Style for YAP-TEAD Docking
# ============================================================

proc style_docking {} {
	
	### ILUMINACION
	axes location off;
	light 0 on; 
	light 0 pos {0.027767 -0.111499 1.003392};
	light 1 off;
	light 2 off;
	light 3 on; 
	light 3 pos {-0.313564 1.371837 0.140526}

	### BACKGROUND
	color Display {Background} 8;

	### DISPLAY SETTINGS
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
	display rendermode {Tachyon RTX RTRT}

	# Escala de color por defecto
	color scale method cividis
	color scale min 0.12
	color scale midpoint 0.50
	color scale max 1.0


	# ============================================================
	# MOL 0 (rep 0 en tus terminos): loopmodel_aligned.pdb
	# ============================================================
	if {[molinfo num] > 0} {
		mol delrep 0 0
		
		# Chain A
		mol selection "chain A";
		mol representation NewCartoon 0.3 32;
		mol material AOChalky;
		mol color ColorID 0; # Azul
		mol addrep 0;
		set nrep [expr {[molinfo 0 get numreps] - 1}]
		mol smoothrep 0 $nrep 7;
		mol showrep 0 $nrep on;
		
		# Chain B
		mol selection "chain B";
		mol representation NewCartoon 0.3 32;
		mol material AOChalky;
		mol color ColorID 1; # Rojo
		mol addrep 0;
		set nrep [expr {[molinfo 0 get numreps] - 1}]
		mol smoothrep 0 $nrep 7;
		mol showrep 0 $nrep on;
	}

	# ============================================================
	# MOL 1 (rep 1 en tus terminos): receptor_clean.pdb
	# Igual que Chain B
	# ============================================================
	if {[molinfo num] > 1} {
		mol delrep 0 1
		
		mol selection "all";
		mol representation NewCartoon 0.3 32;
		mol material AOChalky;
		mol color ColorID 1; # Rojo (Igual que chain B)
		mol addrep 1;
		set nrep [expr {[molinfo 1 get numreps] - 1}]
		mol smoothrep 1 $nrep 7;
		mol showrep 1 $nrep on;
	}

	# ============================================================
	# MOL 2 (rep 2 en tus terminos): all_poses.mol2 (Ligando)
	# Licorice
	# ============================================================
	if {[molinfo num] > 2} {
		mol delrep 0 2
		
		mol selection "all";
		mol representation Licorice 0.3 32;
		mol material AOChalky; # O BrushedMetal
		mol color Name; # Colorea por elemento (O, N, C...)
		mol addrep 2;
		set nrep [expr {[molinfo 2 get numreps] - 1}]
		mol smoothrep 2 $nrep 7;
		mol showrep 2 $nrep on;
	}

	# Hacemos que mol 0 sea el "Top" (T toggle) y centramos la camara en el
	mol top 0
	display resetview
}

# Ejecutamos la funcion para que se aplique automaticamente al cargar
style_docking
