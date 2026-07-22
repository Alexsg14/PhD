#source /media/ciqus/TOSHIBA\ EXT/RENDER_VMD.tcl

# ============================================================
#   Created by: Alejandro Seco Gonzalez
#   Year: 2025
# ============================================================

#display resetview
#rotate x by 93
#display height 3.0
puts "Enter num and axis"
puts ""
puts "giro <num> <axis> for a test of spin axis"
puts "video <num> <axis> <filename> for render without trajectory frames"
puts "make_movie <num> <angle> <axis> <filename> for render trajectory"
puts "smooth <num> <rep> for change smooth of the representations. Example: smooth 0 0"
puts "style <rep> to load the style. You must indicate the ID to apply. Example: style 0"
puts "pic <filename> <fuzz> <res1> <res2> to render an image of the actual scene. Fuzz to set the threshold of transparency. res flags for resolution (1920 1080, for example)"
puts "obj <output_path> to render to obj and mtl. Path must be absolute /home/ciqus/.../file.obj "
puts "double <gro_file> <xtc_file> <nframes 10> <skip 1> <output_dir Video_double> <basename double> for a video "
puts "" 

# Dynamically locate the script's directory for relative loading
set script_dir [file dirname [file normalize [info script]]]

source [file join $script_dir "materials.tcl"]
source [file join $script_dir "style_vmd.tcl"]
source [file join $script_dir "style_vmd_RMSD.tcl"]
source [file join $script_dir "style_vmd_martini.tcl"]
source [file join $script_dir "style_vmd_martini_peptidomica.tcl"]
source [file join $script_dir "Alex_style.tcl"]
source [file join $script_dir "style_yt.tcl"]
source [file join $script_dir "style_vmd_docking.tcl"]

# Configure tachyon path with environment check and local fallback
set tachyon_bin "tachyon"
if {[info exists ::env(TACHYON_BIN)]} {
    set tachyon_bin $::env(TACHYON_BIN)
} elseif {[file exists "/home/ciqus/Descargas/vmd-1.9.4a55/lib/tachyon/tachyon_LINUXAMD64"]} {
    set tachyon_bin "/home/ciqus/Descargas/vmd-1.9.4a55/lib/tachyon/tachyon_LINUXAMD64"
}


#Test of spin
proc giro {num axis} {
	for {set i 0} {$i < [molinfo top get numreps]} {incr i 1} {
	mol smoothrep 0 $i 0}
        set tcl_precision 12
        #set num [molinfo top get numframes]
        set angle [expr 360.0 / $num]
        puts $angle
        dorotate $num $angle $axis
        

}


proc dorotate {nframes angle axis} {
        #animate goto 0
        for {set i 0} {$i < $nframes} {incr i 1} {
                set fnum [expr 0 +$i]
                #animate goto $fnum
                rotate $axis by $angle
                display update
                 #render Tachyon aaa_${i} "\"$tachyon_bin\" -aasamples 1  %s -res 1920 1080 -fullshade -o %s.tga"
        }
}


#Creates a video with rotation in x, y or z
proc video {num axis filename} {
	for {set i 0} {$i < [molinfo top get numreps]} {incr i 1} {
	mol smoothrep 0 $i 0}
        set tcl_precision 12
        #set num [molinfo top get numframes]
        set angle [expr 360.0 / $num]
        puts $angle
        dorotate_ $num $angle $axis $filename
        exec ffmpeg -r 24 -f image2 -s 1920x1080 -i ${filename}_%0d.tga -vcodec libx264 -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" -crf 17  -pix_fmt yuv420p trajectory_24.mp4 -y
        

}


proc dorotate_ {nframes angle axis filename} {
        #animate goto 0
        for {set i 0} {$i < $nframes} {incr i 1} {
                set fnum [expr 0 +$i]
                #animate goto $fnum
                rotate $axis by $angle
                display update
                 render Tachyon ${filename}_${i} "\"$tachyon_bin\" -aasamples 12  %s -res 1920 1080 -fullshade -o %s.tga"
        
        }
}

#Creates a video of a trajectory. If angle = 0, no rotation
proc dorot {nframes angle axis filename} {
	#display resetview
	#rotate x by 93
	#display height 3.0
        #animate goto 0
        for {set i 0} {$i < $nframes} {incr i 1} {
                set fnum [expr 0 +$i]
                animate goto $fnum
                rotate $axis by $angle
                display update
                #render aasamples TachyonLOptiXInternal 32
                #render aosamples TachyonLOptiXInternal 12
                #render TachyonLOptiXInternal ${filename}_${i}.tga
                 render Tachyon ${filename}_${i} "\"$tachyon_bin\" -aasamples 12 %s -res 1920 1080 -fullshade -o %s.tga"
        }
}

proc make_movie {num angle axis filename} {
#	for {set i 0} {$i < [molinfo top get numreps]} {incr i 1} {
#	mol smoothrep 0 $i 7}
        set tcl_precision 12
        #set num [molinfo top get numframes]
        set angle [expr $angle.0 / $num]
        puts $angle
        dorot $num $angle $axis $filename
        exec ffmpeg -r 24 -f image2 -s 1920x1080 -i ${filename}_%0d.tga -vcodec libx264 -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" -crf 17  -pix_fmt yuv420p trajectory_24.mp4 -y

}

proc smooth {num rep} {
	for {set i 0} {$i < [molinfo top get numreps]} {incr i 1} {
	mol smoothrep $rep $i $num}
}

proc pic {filename fuzz res1 res2} {
    global tachyon_bin

    render Tachyon ${filename}.tga \
        "\"$tachyon_bin\" -aasamples 24 %s -res $res1 $res2 -fullshade -format TARGA -o %s"

    exec convert ${filename}.tga ${filename}.png
    exec convert ${filename}.tga -fuzz ${fuzz}% -transparent White ${filename}_transparent.png
}

proc obj {output_path} {
    # output_path = ruta completa SIN extensión
    # Ejemplo:
    # export_wavefront "/home/ciqus/Descargas/OBJ/escena1"

    if {[molinfo num] == 0} {
        error "No hay moléculas cargadas en VMD."
    }

    # Verificar que el directorio exista
    set outdir [file dirname $output_path]
    if {![file isdirectory $outdir]} {
        error "El directorio no existe: $outdir"
    }

    # Exportar a Wavefront
    render Wavefront $output_path ""

    puts "Exportado correctamente:"
    puts "  ${output_path}"
    puts "  ${output_path}"
}

proc double {gro_file xtc_file {nframes 10} {skip 1} {output_dir Video_double} {basename double}} {

    # -------------------------------
    # Crear carpeta si no existe
    # -------------------------------
    if {![file exists $output_dir]} {
        file mkdir $output_dir
        puts "Carpeta creada: $output_dir"
    } else {
        puts "Carpeta ya existe: $output_dir"
    }

    # -------------------------------
    # Cargar moléculas
    # -------------------------------
    mol new $gro_file waitfor all
    mol addfile $xtc_file waitfor all
    style_m 0
    smooth 0 0

    mol new $gro_file waitfor all
    mol addfile $xtc_file waitfor all
    style_m 1
    smooth 1 0

    # -------------------------------
    # Separación basada en tamaño de caja
    # -------------------------------
    set box_x [molinfo 0 get a]

    if {$box_x > 0} {
        set shift $box_x
    } else {
        set sel [atomselect 0 "all"]
        set minmax [measure minmax $sel]
        set min [lindex $minmax 0]
        set max [lindex $minmax 1]
        set size_x [expr {[lindex $max 0] - [lindex $min 0]}]
        set shift [expr {$size_x * 1.2}]
        $sel delete
    }

    set half_shift [expr {0.5 * $shift}]

    mol fix 0
    rotate x by 90
    translate by $shift 0 0
    mol free 0
    translate by [expr {-1.0 * $half_shift}] 0 0

    scale by 1.5

    # -------------------------------
    # Número de frames
    # -------------------------------
    set total [molinfo top get numframes]

    if {$nframes eq "all"} {
        set end [expr {$total - 1}]
    } else {
        set end [expr {$nframes - 1}]
        if {$end >= $total} {
            set end [expr {$total - 1}]
        }
    }

    global tachyon_bin

    # -------------------------------
    # Render loop
    # -------------------------------
    for {set i 0} {$i <= $end} {incr i $skip} {

        animate goto $i
        display update

        set base "${output_dir}/${basename}_${i}"

        render Tachyon $base \
        "\"$tachyon_bin\" -aasamples 12 %s -res 1800 1100 -fullshade -o %s.tga"

        exec magick ${base}.tga \
            -fuzz 10% -transparent White \
            ${base}.png
    }

    # -------------------------------
    # Crear GIF dentro de la carpeta
    # -------------------------------
    exec magick -delay 4 -loop 0 \
        ${output_dir}/${basename}_*.png \
        ${output_dir}/${basename}.gif

    puts "GIF creado: ${output_dir}/${basename}.gif"
}

#proc style {num} {
#	source /media/ciqus/TOSHIBA\ EXT/style_vmd.tcl
#	st $num
#	puts "Set the number of representation"
#}

#ffmpeg -r 60 -f image2 -s 1920x1080 -i aaa_%0d.tga -vcodec libx264 -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" -crf 17  -pix_fmt yuv420p test.mp4 -y
#ffmpeg -r 24 -f image2 -s 1920x1080 -i aaa_%0d.tga -vcodec libx264 -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" -crf 17  -pix_fmt yuv420p trajectory_24.mp4 -y

#Images with transparent background
#for i in `seq 0 119`; do convert aaa_$i.tga -fuzz 20%% -transparent White no_back/bbb_$i.png; done






#_
