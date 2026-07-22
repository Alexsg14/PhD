#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 24 11:34:45 2022

@author: fabs
"""

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# MODULES
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import os
import re
import sys
import json
import time
import math
import pickle
import argparse

import MDAnalysis
import MDAnalysis.topology
import MDAnalysis.transformations
import MDAnalysis.analysis.leaflet

import numpy as np
import pandas as pd
import SuPepDex as SDX
import matplotlib as mpl

mpl.use('Agg')

import statsmodels.api as sm
# from statsmodels import api as sm
import matplotlib.pyplot as plt
import matplotlib.colors as mcol
import matplotlib.ticker as mticker

from typing import Callable

from matplotlib import font_manager
from scipy.optimize import curve_fit, leastsq
from scipy.spatial import Voronoi, ConvexHull
from scipy.spatial.transform import Rotation as R

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# SCRIPT ARGUMENTS
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

# Program description
parser = argparse.ArgumentParser(description =
    '''SuPepMem Analysis v1.0\n
       Analysis of the trajectories for the SuPepMem Database.''')

parser.add_argument( "-f", "--folder", type = str, default = os.getcwd(),
    help = """Location of the simulation files.\n
    Default: %(default)s """ )
parser.add_argument( "-o", "--out", type = str, default = os.getcwd() + '/Analysis',
    help = """Folder with the outcomes of the analysis.\n
    Default: %(default)s """ )

parser.add_argument( "-tpr", "--tpr", type = str, default = 'MINIMIZATION.tpr',
    help = """TPR File for the simulation.\n
    Default: %(default)s """ )
parser.add_argument( "-xtc", "--xtc", type = str, default = 'PRODUCTION.xtc',
    help = """XTC File with the trajectories of the system.\n
    Default: %(default)s """ )
parser.add_argument( "-mdp", "--mdp", type = str, default = 'mdout.mdp',
    help = """MDP File of the production.\n
    Default: %(default)s """ )
    
parser.add_argument( "-ff", "--forcefield", type = str, default = 'martini22p',
    help = """Force field of the simulation.\n
    Default: %(default)s""")
    
parser.add_argument( "-A", "--all", action = 'store_true',
    help = "Perform every analysis, plot graphs and compute averages." )
parser.add_argument( "-a", "--analysis", action = 'store_true',
    help = "Perform every analysis." )
parser.add_argument( "-p", "--plot", action = 'store_true',
    help = "Plot the results." )

parser.add_argument( "-style", "--style", type=str, 
    default = os.path.abspath( os.path.dirname( __file__ ) ) + '/SuPepMem.mplstyle',
    help = """ Custom MPLSTYLE file.\n
    Default: %(default)s """)
parser.add_argument( "-font", "--font", type=str, 
    default = os.path.abspath( os.path.dirname( __file__ ) ),
    help = """ Folder with fonts for the graphs.\n
    Default: %(default)s """)

parser.add_argument( "-b", "--bins", type = int, default = 200,
    help = """Number of bins for the representations.\n
    Default: %(default)s""")
parser.add_argument( "-i", "--initial_time", type = int, default = 0,
    help = """Initial time of the analysis.\n
    Default: %(default)s ps""")
parser.add_argument( "-l", "--last_time", type = int, default = 5000000,
    help = """Last time of the analysis.\n
    Default: %(default)s ps""")
parser.add_argument( "-av", "--average_time", type = int, default = 4000000,
    help = """Time to start the average.\n
    Default: %(default)s ps""")
parser.add_argument( "-sr", "--skip_rough", type = int, default = 100,
    help = """Frames to skip in the rough analysis.\n
    Default: %(default)s """)
parser.add_argument( "-sf", "--skip_fine", type = int, default = 10,
    help = """Frames to skip in the fine analysis.\n
    Default: %(default)s """)

args = parser.parse_args()

print('                                                             ')
print('           SuPepMem  Analysis v1.0                           ')
print('                                                             ')
print(' Currently working in:                                       ')
print('  ' + args.folder)
print('                                                             ')
if os.path.isfile( args.style ):
    print(' Using the customized SuPepMem Matplotlib Style              ')
    
    # Load the fonts in the font folder
    for font_file in font_manager.findSystemFonts(fontpaths=args.font):
        font_manager.fontManager.addfont(font_file)
        
    # Load the style
    plt.style.use( args.style )

if not os.path.isdir( args.out ):
    os.makedirs( args.out )
    print(' Output folder created succesfuly.')
else:
    print(' Output folder already exists, data will be overwritten.')
print('  ')



#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# ANALYSIS FUNCTIONS
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

#def Angles( frame ):
#    global Results
#    
#    # Backbone principal vector
#    Vec = ( Backbone[-1].position - Backbone[0].position ) / np.linalg.norm( ( Backbone[-1].position - Backbone[0].position ) )
#    
#    # Store the angles formed in the XY, XZ and YZ projections
#    Results[ "angles" ][ frame.time ] = [ FindAngle( Vec[:2] ), FindAngle( Vec[::2] ), FindAngle( Vec[1:] )  ]
#    
#    return

# ---- Reporte rápido de módulos cargados (opcional pero útil) ----
def _report_loaded_modules():
    try:
        import numpy as _np, pandas as _pd, matplotlib as _mpl, MDAnalysis as _mda, statsmodels as _sm
        _mods = {
            "Python": sys.version.split()[0],
            "NumPy": getattr(_np, "__version__", "?"),
            "Pandas": getattr(_pd, "__version__", "?"),
            "Matplotlib": getattr(_mpl, "__version__", "?"),
            "MDAnalysis": getattr(_mda, "__version__", "?"),
            "statsmodels": getattr(_sm, "__version__", "?"),
        }
        print("\n[Módulos] Cargados correctamente:")
        for k, v in _mods.items():
            print(f"  - {k}: {v}")
    except Exception as e:
        print(f"[Módulos] Advertencia: no se pudo listar versiones ({e})")


def AreaPerLipid( frame ):
    '''
    AreaPerLipid:
     - Determine the area per lipid of the system in a certain frame
    Returns the area per lipid of the membrane, of the upper leaflet and the lower leaflet
    '''
    global Results
    # Area of the simulation box
    area = frame.dimensions[0] * frame.dimensions[1]
    
    Results[ "area" ][ frame.time ] = [ 0.02 * area / ( len( UpperLipRB ) + len( LowerLipRB ) ), 
                                        0.01 * area / len( UpperLipRB ), 
                                        0.01 * area / len( LowerLipRB ) ]
    return


def AreaPerLipid_Voronoi( frame ):
    '''
    AreaPerLipid_Voronoi:
     - Determine the area per lipid of the system in a certain frame using its Voronoi tesselation
    Returns the area per lipid of the membrane, of the upper leaflet and the lower leaflet.
    
    WARNING: NOT FINISHED
    '''
    global Results
    
    # Positions of the lipids in the simulation and adjacent cells 
    UpperLipids = np.vstack( [ [ Lipid.position[:2] + np.array([ i*frame.dimensions[0], j*frame.dimensions[1] ] )
                              for Lipid in UpperLipRB ] for i in (0,-1,1) for j in (0,-1,1) ] )
    
    LowerLipids = np.vstack( [ [ Lipid.position[:2] + np.array([ i*frame.dimensions[0], j*frame.dimensions[1] ] )
                              for Lipid in LowerLipRB ] for i in (0,-1,1) for j in (0,-1,1) ] )
    
    # Voronoi diagram associated to each leaflet
    VorUpper = Voronoi( UpperLipids )
    VorLower = Voronoi( LowerLipids )
    
    # Dictionary for the results
    AreasTotal = { lipid: [] for lipid in LipSys }
    AreasUpper = { lipid: [] for lipid in LipSys }
    AreasLower = { lipid: [] for lipid in LipSys }
    
    # Compute the area associated to each Voronoi region and store for each kind of lipid
    for i, lipid in enumerate( UpperLipRB.resnames ):
        if lipid in LipSys:
            AreasTotal[ lipid ].append( ConvexHull( VorUpper.vertices[ VorUpper.regions[ VorUpper.point_region[i] ] ] ).volume ) 
            AreasUpper[ lipid ].append( ConvexHull( VorUpper.vertices[ VorUpper.regions[ VorUpper.point_region[i] ] ] ).volume ) 
                
    for i, lipid in enumerate( LowerLipRB.resnames ):
        if lipid in LipSys:
            AreasTotal[ lipid ].append( ConvexHull( VorLower.vertices[ VorLower.regions[ VorLower.point_region[i] ] ] ).volume )
            AreasLower[ lipid ].append( ConvexHull( VorLower.vertices[ VorLower.regions[ VorLower.point_region[i] ] ] ).volume )
    
    # Average the values by kind of lipid and store the number of lipids of each kind (weights)
    AreasTotal = { lipid: ( 0.01 * np.mean( AreasTotal[ lipid ] ), 0.01 * np.std( AreasTotal[ lipid ] ) / np.sqrt( len( AreasTotal[ lipid ] ) ) , len( AreasTotal[ lipid ] ) ) if AreasTotal[ lipid ] else ( 0, 0, 0 ) for lipid in AreasTotal }
    AreasUpper = { lipid: ( 0.01 * np.mean( AreasUpper[ lipid ] ), 0.01 * np.std( AreasUpper[ lipid ] ) / np.sqrt( len( AreasUpper[ lipid ] ) ) , len( AreasUpper[ lipid ] ) ) if AreasUpper[ lipid ] else ( 0, 0, 0 ) for lipid in AreasUpper }
    AreasLower = { lipid: ( 0.01 * np.mean( AreasLower[ lipid ] ), 0.01 * np.std( AreasLower[ lipid ] ) / np.sqrt( len( AreasLower[ lipid ] ) ) , len( AreasLower[ lipid ] ) ) if AreasLower[ lipid ] else ( 0, 0, 0 ) for lipid in AreasLower }
    
    # Weighted average of all areas. Result must match the area of the XY dimension of the cell divided by the number of lipids on each leaflet
    AvTotal = np.average( [ AreasTotal[ lipid ][0] for lipid in LipSys if AreasTotal[ lipid ] ], weights = [ AreasTotal[ lipid ][2] for lipid in LipSys if AreasTotal[ lipid ] ] )
    AvUpper = np.average( [ AreasUpper[ lipid ][0] for lipid in LipSys if AreasUpper[ lipid ] ], weights = [ AreasUpper[ lipid ][2] for lipid in LipSys if AreasUpper[ lipid ] ] )
    AvLower = np.average( [ AreasLower[ lipid ][0] for lipid in LipSys if AreasLower[ lipid ] ], weights = [ AreasLower[ lipid ][2] for lipid in LipSys if AreasLower[ lipid ] ] )
    
    # Process the data before asign it to the Results dictionary
    Results[ "area_vor" ][ frame.time ] = { 'Total': { 'Global': ( AvTotal , np.sqrt( np.average( [ AreasTotal[ lipid ][0] - AvTotal for lipid in LipSys ] , weights = [ AreasTotal[ lipid ][2] for lipid in LipSys ] ) / len( [ 1 for lipid in LipSys if AreasTotal[ lipid ][2]  ] ) ) ),
                                                      **{ lipid: ( AreasTotal[ lipid ][2], AreasTotal[ lipid ][0], AreasTotal[ lipid ][1] ) for lipid in LipSys } } ,
                                            'Upper': { 'Global': ( AvUpper , np.sqrt( np.average( [ AreasUpper[ lipid ][0] - AvUpper for lipid in LipSys ] , weights = [ AreasUpper[ lipid ][1] for lipid in LipSys ] ) / len( [ 1 for lipid in LipSys if AreasUpper[ lipid ][2] ] ) ) ),
                                                      **{ lipid: ( AreasUpper[ lipid ][2], AreasUpper[ lipid ][0], AreasUpper[ lipid ][1] ) for lipid in LipSys } } ,
                                            'Lower': { 'Global': ( AvLower , np.sqrt( np.average( [ AreasLower[ lipid ][0] - AvLower for lipid in LipSys ] , weights = [ AreasLower[ lipid ][1] for lipid in LipSys ] ) / len( [ 1 for lipid in LipSys if AreasLower[ lipid ][2] ] ) ) ),
                                                      **{ lipid: ( AreasLower[ lipid ][2], AreasLower[ lipid ][0], AreasLower[ lipid ][1] ) for lipid in LipSys } } }


def COG( frame ):
    '''
    COG:
     - Determine the Z coordinate of the Center of Geometry of a set of selections
    Returns the position (nm) of the peptide, membrane, first and last elements of the 
    peptide backbone and the position of the HGs of the upper and lower leaflets.
    '''
    global Results

    Results[ "COG" ][ frame.time ] = [ 
        Peptides.center_of_geometry()[2] * 0.1,
        Membrane.center_of_geometry()[2] * 0.1,
        Backbone[0].position[2] * 0.1,
        Backbone[-1].position[2] * 0.1,
        UpperLipRB.center_of_geometry()[2] * 0.1,
        LowerLipRB.center_of_geometry()[2] * 0.1 ]
    return


def Contacts( frame ):
    '''
    Contacts:
     - Determine the contacts between peptide and other groups
    Returns the number of contacts between the backbone of the peptide and water,
    lipid headgroups and lipid tails.
    '''
    global Results
    
    Results[ "contacts_norm" ][ frame.time ] = [ 
                len( np.unique( MDAnalysis.lib.NeighborSearch.AtomNeighborSearch( 
                      u.select_atoms( 'resname {}'.format( Water ) ), 
                      frame.dimensions ).search( u.select_atoms( 'protein' ), 6 ).resids ) ) / len( Peptides ),
                len( np.unique( MDAnalysis.lib.NeighborSearch.AtomNeighborSearch( 
                      u.select_atoms( SDX.LipHG ), 
                      frame.dimensions ).search( u.select_atoms( 'protein' ), 6 ).resids ) ) / len( Peptides ),
                len( np.unique( MDAnalysis.lib.NeighborSearch.AtomNeighborSearch(
                      u.select_atoms( SDX.LipTG ),
                      frame.dimensions ).search( u.select_atoms( 'protein' ), 6 ).resids ) ) / len( Peptides ) ]
    
    Results[ "contacts_tot" ][ frame.time ] = [ 
                len( np.unique( MDAnalysis.lib.NeighborSearch.AtomNeighborSearch( 
                      u.select_atoms( 'resname {}'.format( Water ) ), 
                      frame.dimensions ).search( u.select_atoms( 'protein' ), 6 ).resids ) ),
                len( np.unique( MDAnalysis.lib.NeighborSearch.AtomNeighborSearch( 
                      u.select_atoms( SDX.LipHG ), 
                      frame.dimensions ).search( u.select_atoms( 'protein' ), 6 ).resids ) ),
                len( np.unique( MDAnalysis.lib.NeighborSearch.AtomNeighborSearch(
                      u.select_atoms( SDX.LipTG ),
                      frame.dimensions ).search( u.select_atoms( 'protein' ), 6 ).resids ) ) ]
    
    return


def ContactsType( frame ):
    '''
    ContactsType:
     - Determine the contacts between the amino acids and the lipids
    Returns the number of contacts between each type of amino acid and each lipid.
    '''
    global Results

    Results[ "contype_norm" ][ frame.time ] = { lipid: { amino: 
            ( len( MDAnalysis.lib.NeighborSearch.AtomNeighborSearch( 
                  u.select_atoms( 'resname {} and ( name '.format( lipid ) + ' or name '.join( SDX.MEMBCOMP[ lipid ][ "HG" ] ) + ' )' ), 
                  frame.dimensions ).search( u.select_atoms( 'resname {}'.format( amino ) ), 6, level='R' ) ) +
            len( MDAnalysis.lib.NeighborSearch.AtomNeighborSearch( 
                  u.select_atoms( 'resname {} and not ( name '.format( lipid ) + ' or name '.join( SDX.MEMBCOMP[ lipid ][ "HG" ] ) + ' )' ), 
                  frame.dimensions ).search( u.select_atoms( 'resname {}'.format( amino ) ), 6, level='R' ) ) ) / max( len(u.select_atoms("resname {}".format(amino))), 1 )
            for amino in SDX.AMINO  } for lipid in MemSys }
        
    Results[ "contype_tot" ][ frame.time ] = { lipid: { amino: 
            ( len( MDAnalysis.lib.NeighborSearch.AtomNeighborSearch( 
                  u.select_atoms( 'resname {} and ( name '.format( lipid ) + ' or name '.join( SDX.MEMBCOMP[ lipid ][ "HG" ] ) + ' )' ), 
                  frame.dimensions ).search( u.select_atoms( 'resname {}'.format( amino ) ), 6, level='R' ) ) +
            len( MDAnalysis.lib.NeighborSearch.AtomNeighborSearch( 
                  u.select_atoms( 'resname {} and not ( name '.format( lipid ) + ' or name '.join( SDX.MEMBCOMP[ lipid ][ "HG" ] ) + ' )' ), 
                  frame.dimensions ).search( u.select_atoms( 'resname {}'.format( amino ) ), 6, level='R' ) ) )
            for amino in SDX.AMINO  } for lipid in MemSys }
        
    return


def ContactsResid( frame ):
    '''
    ContactsResid:
    - Determine the contact between each specific element of the backbone and the lipids
    '''
    global Results
    
    Results[ "contres_norm" ][ frame.time ] = { lipid: { ( atom.resname, i ): 
                                ( len( np.unique( MDAnalysis.lib.NeighborSearch.AtomNeighborSearch( 
                                      u.select_atoms( 'resname {} and ( name '.format( lipid ) + ' or name '.join( SDX.MEMBCOMP[ lipid ][ "HG" ] ) + ' )' ), 
                                      frame.dimensions ).search( atom, 6, level='R' )) ) +
                                len( np.unique( MDAnalysis.lib.NeighborSearch.AtomNeighborSearch( 
                                      u.select_atoms( 'resname {} and not ( name '.format( lipid ) + ' or name '.join( SDX.MEMBCOMP[ lipid ][ "HG" ] ) + ' )' ), 
                                      frame.dimensions ).search( atom, 6 , level='R') ) ) )
                        for i, atom in enumerate( u.select_atoms( 'name BB' ) ) } for lipid in MemSys }
    
    Results[ "contres_tot" ][ frame.time ] = { lipid: { ( atom.resname, i ): 
                                ( len( np.unique( MDAnalysis.lib.NeighborSearch.AtomNeighborSearch( 
                                      u.select_atoms( 'resname {} and ( name '.format( lipid ) + ' or name '.join( SDX.MEMBCOMP[ lipid ][ "HG" ] ) + ' )' ), 
                                      frame.dimensions ).search( atom.atoms, 6, level='R' )) ) +
                                len( np.unique( MDAnalysis.lib.NeighborSearch.AtomNeighborSearch( 
                                      u.select_atoms( 'resname {} and not ( name '.format( lipid ) + ' or name '.join( SDX.MEMBCOMP[ lipid ][ "HG" ] ) + ' )' ), 
                                      frame.dimensions ).search( atom.atoms, 6 , level='R') ) ) ) / max( len( atom.atoms ), 1 )
                        for i, atom in enumerate( u.select_atoms('protein').residues ) } for lipid in MemSys }
    
    return


def Density( frame ):
    '''
    Density:
     - Determine the density of some groups in the cell
    Returns the mass of each selected group in the sliced cell for each frame.
    A latter processing allows to find the density profile of such groups
    '''
    global Results

    # Split the box in bins    
    Bins = [ i * frame.dimensions[2] / args.bins for i in range( args.bins ) ]
    
### Water    
    # Position of each particle in terms of bins
    Zbin = [ i-1 for i in np.digitize( WaterMols.positions[:,2], Bins ) ]
    # Add the mass of each particle to its corresponding bin
    for i, atom in enumerate( WaterMols ):
        Results[ "density" ][ "water" ][ Zbin[ i ] ] += atom.mass
    
### Headgroups
    # Position of each particle in terms of bins
    Zbin = [ i-1 for i in np.digitize( Headgroup.positions[:,2], Bins ) ]
    # Add the mass of each particle to its corresponding bin
    for i, atom in enumerate( Headgroup ):
        Results[ "density" ][ "HG" ][ Zbin[ i ] ] += atom.mass
    
### Tailgroups
    # Position of each particle in terms of bins
    Zbin = [ i-1 for i in np.digitize( Tailgroup.positions[:,2], Bins ) ]
    # Add the mass of each particle to its corresponding bin
    for i, atom in enumerate( Tailgroup ):
        Results[ "density" ][ "TG" ][ Zbin[ i ] ] += atom.mass 
        
### Peptide
    # Position of each particle in terms of bins
    Zbin = [ i-1 for i in np.digitize( Peptides.positions[:,2], Bins ) ]
    # Add the mass of each particle to its corresponding bin
    for i, atom in enumerate( Peptides ):
        Results[ "density" ][ "peptide" ][ Zbin[ i ] ] += atom.mass 
    return


def DensMap( frame ):
    '''
    DensMap:
     - Determine the density of lipids around the peptide
    Returns the coordinates of the reference bead of the lipids in the upper and
    lower leaflets to build the density map around the peptide.
    '''
    global Results
    # Center of geometry of the membrane in Z
    COG = u.select_atoms( SDX.Membr ).center_of_geometry()[2]
    
    for molecule in Results[ "densmap" ]:
        # Try-except are required in case lipids are only present in one leaflet
        try:
            # Coodinates of the lipids, splitted by leaflets, with reference in the COG
            # Each membrane is extended in x and y, forming a cross
            ULeaflet = np.vstack( [ 
                # Simulation cell
                [ [ Coord[0], Coord[1], Coord[2] - COG ] 
                 for Coord in UpperLipRB.select_atoms( 'resname {}'.format( molecule ) ).positions ],
                # Extension in +x
                [ [ Coord[0] + frame.dimensions[0], Coord[1], Coord[2] - COG ] 
                 for Coord in UpperLipRB.select_atoms( 'resname {} and prop x < {}'.format( molecule , ( np.sqrt(2) - 1 ) * frame.dimensions[0]/2 ) ).positions ],
                # Extension in -x
                [ [ Coord[0] - frame.dimensions[0], Coord[1], Coord[2] - COG ] 
                 for Coord in UpperLipRB.select_atoms( 'resname {} and prop x > {}'.format( molecule , ( 3 - np.sqrt(2) ) * frame.dimensions[0]/2 ) ).positions ],
                # Extension in +y
                [ [ Coord[0], Coord[1] + frame.dimensions[1], Coord[2] - COG ] 
                 for Coord in UpperLipRB.select_atoms( 'resname {} and prop y < {}'.format( molecule , ( np.sqrt(2) - 1 ) * frame.dimensions[1]/2 ) ).positions ],
                # Extension in -y
                [ [ Coord[0], Coord[1] - frame.dimensions[1], Coord[2] - COG ] 
                 for Coord in UpperLipRB.select_atoms( 'resname {} and prop y > {}'.format( molecule , ( 3 - np.sqrt(2) ) * frame.dimensions[1]/2 ) ).positions ]
                ] )
            
            # Center the system in (0,0) to perform a rotation
            ULeaflet -= np.append( frame.dimensions[:2]/2 , 0 )
            
            # Rotate the positions to align the peptide in the Y axis
            ULeaflet = AlignWithAxis( ULeaflet, Vector = Results[ "PepDF" ][ "Vec" ][-1], Axis = np.array([0,1,0]) )
            
            # Put the system in its previous position
            ULeaflet += np.append( frame.dimensions[:2]/2 , 0 )
            
            # Append the coordinates of the lipids
            Results[ "densmap" ][ molecule ][ "Upper" ] = np.vstack( [ Results[ "densmap" ][ molecule ][ "Upper" ], ULeaflet ] )  
        except: pass
            
        try:
            # Coodinates of the lipids, splitted by leaflets, with reference in the COG
            # Each membrane is extended in x and y, forming a cross
            LLeaflet = np.vstack( [ 
                # Simulation cell
                [ [ Coord[0], Coord[1], Coord[2] - COG ] 
                 for Coord in LowerLipRB.select_atoms( 'resname {}'.format( molecule ) ).positions ],
                # Extension in +x
                [ [ Coord[0] + frame.dimensions[0], Coord[1], Coord[2] - COG ] 
                 for Coord in LowerLipRB.select_atoms( 'resname {} and prop x < {}'.format( molecule , ( np.sqrt(2) - 1 ) * frame.dimensions[0]/2 ) ).positions ],
                # Extension in -x
                [ [ Coord[0] - frame.dimensions[0], Coord[1], Coord[2] - COG ] 
                 for Coord in LowerLipRB.select_atoms( 'resname {} and prop x > {}'.format( molecule , ( 3 - np.sqrt(2) ) * frame.dimensions[0]/2 ) ).positions ],
                # Extension in +y
                [ [ Coord[0], Coord[1] + frame.dimensions[1], Coord[2] - COG ] 
                 for Coord in LowerLipRB.select_atoms( 'resname {} and prop y < {}'.format( molecule , ( np.sqrt(2) - 1 ) * frame.dimensions[1]/2 ) ).positions ],
                # Extension in -y
                [ [ Coord[0], Coord[1] - frame.dimensions[1], Coord[2] - COG ] 
                 for Coord in LowerLipRB.select_atoms( 'resname {} and prop y > {}'.format( molecule , ( 3 - np.sqrt(2) ) * frame.dimensions[1]/2 ) ).positions ]
                ] )
            
            # Center the system in (0,0) to perform a rotation
            LLeaflet -= np.append( frame.dimensions[:2]/2 , 0 )
            
            # Rotate the positions to align the peptide in the Y axis
            LLeaflet = AlignWithAxis( LLeaflet, Vector = Results[ "PepDF" ][ "Vec" ][-1], Axis = np.array([0,1,0]) )
            
            # Put the system in its previous position
            LLeaflet += np.append( frame.dimensions[:2]/2 , 0 )
            
            # Append the coordinates of the lipids
            Results[ "densmap" ][ molecule ][ "Lower" ] = np.vstack( [ Results[ "densmap" ][ molecule ][ "Lower" ], LLeaflet ] )
        except: pass 
    return


def DistMin( frame ):
    '''
    DistMin:
     - Determine minimum distance between the peptide and the lipids
    Returns the minimum distance between peptide and heagroups and peptide and tails
    '''
    global Results
    
    Results[ "mindist" ][ frame.time ] = [
        0.1*np.min( MDAnalysis.analysis.distances.distance_array( 
            u.select_atoms( 'name BB' ).positions,
            u.select_atoms( SDX.LipHG ).positions,
            frame.dimensions ) ),
        0.1*np.min( MDAnalysis.analysis.distances.distance_array( 
            u.select_atoms( 'name BB' ).positions,
            u.select_atoms( SDX.LipTG ).positions,
            frame.dimensions ) ) ]
    return


def ElectrostaticDipolarMoment( frame ):
    global Results

    Ref = Peptides.center_of_geometry()
    
    # The positions of each bead with respect to the COG
    Vec = np.array( [ Atom.position - Ref for Atom in Peptides ] )
    
    # The charge of each bead
    Ch = np.array( [ Atom.charge for Atom in Peptides ] )
    
    # Multiply the charges by the relative vectors and sum them
    DipMom = np.sum( np.array( [ Vec[i] * Ch[i] for i in range( len( Ch ) ) ] ), axis = 0 )
    
    # The module of the electric dipole moment
    DipNorm = np.linalg.norm( DipMom )
    
    # The longitudinal component of the hydrophobic moment, projection on the principal vector
    DipLong = np.abs( np.dot( DipMom, PrVec ) )
    
    # If the longitudinal component is larger than the module (inaccuracy), assume them to be equal
    if np.abs(DipNorm) < np.abs(DipLong): DipLong = DipNorm

    # The transversal component is the difference between the moment and the longitudinal component
    DipTrans = np.sqrt( DipNorm**2 - DipLong**2 )
    
    Results["electrostatic moment"][ frame.time ] = [ DipNorm/10, DipLong/10, DipTrans/10 ]
    
    return


def HydrophobicDipolarMoment( frame ):
    global Results
    global TrVec
    
    Ref = Backbone.center_of_geometry()
    
    # The positions of each bead with respect to the COG
    Vec = np.array( [ Atom.position - Ref for Atom in Backbone ] )
    
    # The hydrophobicities of each bead
    HPh = np.array( [ SDX.AMINO[ Res ]["hydrophobicity"] for Res in Backbone.resnames ] )
    
    # Multiply the hidrohpobicities by the relative vectors and sum them
    HydroMom = np.sum( np.array( [ Vec[i] * HPh[i] for i in range( len( HPh ) ) ] ), axis = 0 )
    
    # The module of the hydrophobic moment
    HydroNorm = np.linalg.norm( HydroMom )
    
    # The longitudinal component of the hydrophobic moment, projection on the principal vector
    HydroLong = np.abs( np.dot( HydroMom, PrVec ) )
    
    # Define a transversal vector
    TrVec =  HydroMom / HydroNorm - PrVec * np.dot( HydroMom / HydroNorm, PrVec )
    TrVec /= np.linalg.norm( TrVec )
    
    # If the longitudinal component is larger than the module (numerical errors), assume them to be equal
    if np.abs(HydroNorm) < np.abs(HydroLong): HydroLong = HydroNorm
    
    # The transversal component is the difference between the moment and the longitudinal component
    HydroTrans = np.sqrt( HydroNorm**2 - HydroLong**2 )
    
    Results["hydrophobic moment"][ frame.time ] = [ HydroNorm/10, HydroLong/10, HydroTrans/10 ]
    
    return


def PepDF( frame ):
    '''
    PepDF:
      - Determine the rotation and displacement of the peptide.
    Returns the position and orientation of the peptide in the XY plane. A further
    processing is required to find the displacemente and rotation.
    '''
    global Results
    global BBPos
  
    # Time of the frame
    Results[ "PepDF" ][ "Time" ].append( frame.time )
  
    # Position of the peptide
    Results[ "PepDF" ][ "COG" ].append( PBCImage( np.append( Backbone.center_of_geometry()[:2], 0 ), Results[ "PepDF" ][ "COG" ][-1] ) )
  
    # Position of the beads of the backbone
    BBPos = np.array( [ PBCImage( Backbone.positions[i,:], BBPos[i,:] ) for i in range( len( Backbone ) ) ] ) 
    
    # Compute the principal vector
    BB = LeastSquaresLine( BBPos, BBPos[-1,:] - BBPos[0,:] )  
  
    # Ensure its rigth orientation 
    BB = BB if np.dot( BB, BBPos[-1,:] - BBPos[0,:] ) >= 0 else -BB
      
    # Principal vector of the peptide (normalized)    
    Results[ "PepDF" ][ "Vec" ].append( np.append( BB[:2], 0 ) / np.linalg.norm( BB[:2] ) )
  
    return

# def Roll( frame ):
#     #Roll:
#     #- Determine the roll angle
#     global Results
#     global FstPrVec, FstTrVec
#
#     if not Results[ "roll" ]:
#         # In the first iteration, we just compute the relevant vectors
#       
#         # Vector between the first 2 beads of the backbone
#         FstTrVec = ( Backbone[1].position - Backbone[0].position ) / np.linalg.norm( Backbone[1].position - Backbone[0].position )
#       
#         # Transversal component of the vector between the first 2 beads 
#         FstTrVec -= np.dot( FstTrVec, FstPrVec ) * FstPrVec 
#       
#         # Normalize the vector
#         FstTrVec = FstTrVec / np.linalg.norm( FstTrVec )
#       
#         Results[ "roll" ][ frame.time ] = 0
#   
#     else:
#         # In following steps, we need to align the principal vectors 
#       
#         # Align the backbones
#         BB_al = AlignWithAxis( Backbone.positions, PrVec, FstPrVec )
#       
#         # Vector between the first 2 beads of the backbone
#         TrVec = ( BB_al[1,:] - BB_al[0,:] ) / np.linalg.norm( BB_al[1,:] - BB_al[0,:] )
#       
#         # Transversal component of the vector between the first 2 beads 
#         TrVec -= np.dot( TrVec, FstPrVec ) * FstPrVec
#       
#         # Normalize the vector
#         TrVec = TrVec / np.linalg.norm( TrVec )
#       
#         # Angle between transversal vectors
#         Angle = np.rad2deg( np.arccos( np.dot( TrVec, FstTrVec ) ) )
#       
#         Results[ "roll" ][ frame.time ] = Angle #if Angle <= 90 else Angle -180
#   
#     return

 
def Spin( frame ):
    '''
    Spin:
    - Determine the rotation of the peptide with respect to the membrane
    '''
    global Results
    #global RotRef
    
    #TrVec = Backbone[1].position - Backbone[0].position
    #TrVec /= np.linalg.norm( TrVec )
    #TrVec = TrVec - PrVec * 
    
    # Tilt vector, a vector normal to the principal vector contained in the plane formed by the principal vector and the normal to the surface
    TlVec = -np.cross( PrVec, np.cross( PrVec, np.array([0,0,1]) ) )
    TlVec /= np.linalg.norm( TlVec )
    
    # The angle between TrVec and TlVec
    RotAngle = np.rad2deg( np.arccos( np.dot( TrVec, TlVec ) ) )
    
    # Avoid problems when vectors are (anti)parallel; change the range [0,180) -> [0,360)
    if np.dot( TlVec, TrVec ) == 1: RotAngle = 0
    elif np.dot( TlVec, TrVec ) == -1: RotAngle = 180
    else: RotAngle = RotAngle if np.dot( PrVec, np.cross( TrVec, TlVec ) ) >=0 else 360 - RotAngle
    
    Results[ "spin" ][ frame.time ] = RotAngle if RotAngle >=0 else 360 + RotAngle
    
    return


def Tilt( frame ):
    '''
    Tilt:
     - Determine the angle between the peptide and the membrane
    Returns the angle formed by the peptide and the Z axis for a certain frame.
    '''
    global Results
        
    # Write the results
    Results[ "tilt" ][ frame.time ] = np.rad2deg( np.arccos( PrVec[2] / np.linalg.norm( PrVec ) ) )
    
    return


#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# AUXILIAR FUNCTIONS
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

def AlignWithAxis( Positions, Vector: np.ndarray, Axis: np.ndarray ):
    '''
    AlignWithAxis:
     - Orients a system with a Vector parallel to an Axis
    Returns the rotated Positions such Vector is parallel to Axis
    '''
    
    # Angle between the vector and the axis
    Angle = np.arccos( np.inner( Vector, Axis ) / ( np.linalg.norm( Vector ) * np.linalg.norm( Axis ) ) )
    
    # Rotation axis, a vector orthogonal to both Vector and Axis of module Angle
    RotAxis = Angle * np.cross( Vector, Axis ) / np.linalg.norm( np.cross( Vector, Axis ) )
    
    # Define the rotation
    Rotation = R.from_rotvec( RotAxis )
    
    return Rotation.apply( Positions )


def CenterInBox( Selection: str ):
    '''
    CenterInBox:
     - MDAnalysis Trajectory transfromation to center a Selection in the box
    '''
    def wrapped(ts):
        ts.positions +=  np.array( [ 0, 0, ts.dimensions[2]/2 - u.select_atoms( Selection ).center_of_geometry()[2] ] )
        return ts
    return wrapped


def Format( x, pos ):
    '''
    Format
     - Changes the format of a number to a.b·10^{c} in LaTeX format
    '''
    a, b = [ float(i) for i in '{:.2e}'.format(x).split('e') ]
    if a or b:
        return r'${}\cdot10^{{{:.0f}}}$'.format( a, b )
    elif a:
        return r'${}$'.format( a )
    else:
        return '0'


def ProgressBar(it, prefix="", size=60, file=sys.stdout):
    '''
    ProgressBar:
     - A Progress Bar for the state of the analysis
    '''
    count = len(it)
    def show(j):
        try:
            x = int(size*j/count)
        except:
            x = 0
        file.write("%s[%s%s] %i/%i\r" % (prefix, "#"*x, "."*(size-x), j, count))
        file.flush()        
    show(0)
    for i, item in enumerate(it):
        yield item
        show(i+1)
    file.write("\n")
    file.flush()


def BuildCmap( Colors, Points = None ):
    '''
    BuildCmap:
     - Builds a color map using a set of colors
    '''
    
    # HEX values are acepted, but must be converted into RGB
    RGB = [ mcol.to_rgb( color ) for color in Colors ]
    
    # If the list of points is not provided, create one
    if not Points:
        Points = list( np.linspace( 0, 1, len( RGB ) ) )
    
    # Dictionary for the colors: each entry is assigned to each primary color,
    # and it contains a set of lists with the references and the contribution
    # of each primary color to them.
    ColorDic = { color: [ [ Points[i], RGB[i][n], RGB[i][n] ] for i in range( len( Points ) ) ] 
                for n, color in enumerate( [ 'red', 'green', 'blue' ] ) }
    
    # Build the color map    
    return mcol.LinearSegmentedColormap('custom_cmap', segmentdata = ColorDic, N = 256)


def ErrorACF( Data, k: int = 2 ):
    '''
    ErrorACF:
     - Compute the AutoCorrelation Function of a time series and determine the 
      autocorrelation time, which is then used to find the real variance.
    '''
    
    def decay( x, t ):
        return np.exp( -x / t )
    
    # Autocorrelation function of the data
    ACF = sm.tsa.acf( Data )
    
    # Compute the correlation time
    Par, _ = curve_fit( decay, np.arange( len( ACF ) ),  ACF )
    
    # Exponential decay approximation of the autocorrelation function
    e = np.exp( -1/Par[0] )
    
    # Error, after taking into account the correlation, applying a coverage factor
    Error = k * np.sqrt( 
        np.var( Data )/len( Data ) * ( 
            ( 1 + e ) / ( 1 - e ) 
            - 2 * e / len( Data ) * (
                1 - e ** len( Data ) ) / ( 1 - e )**2 ) )
    return SDX.RoundStdv( np.mean( Data ), Error )
           

def FindAngle( Vec: list ) -> float :
    '''
    FindAngle:
     - Determines the angle between vectors, between 0 and 2π
    '''
    
    # Compute the angle
    angle = np.arctan2( Vec[0], Vec[1] )
    
    # Correct if the angle is negative
    if angle < 0: angle = 2. * np.pi + angle
    
    return angle


def LeastSquaresLine( Points, Guess = [1,1,1] ):
    
    # Center of the cloud
    Center = np.mean( Points, axis=0 )
    
    # Distance between the plane and a point
    def Distance( Par, Coords ):
        return np.linalg.norm( np.cross( Coords - Center, Par ), axis=1 ) / np.linalg.norm( Par )
    
    # Vector
    Vector = leastsq( Distance, Guess, args = Points )[0]
    
    return  Vector / np.linalg.norm( Vector )


def LeastSqueresPlane( Points, Guess = [1,1,1,1] ):
    
    # Distance between the plane and a point
    def Distance( Par, Coords ):
        return ( ( Par[:3] * Coords ).sum(axis=1) + Par[3] ) / np.linalg.norm( Par[:3] )
    
    return leastsq( Distance, Guess, args = Points )[0]


def BackbonePrVec( frame ):
    '''
    BackbonePrVec:
    - Determine the principal vector of the backbone
    '''
    global PrVec 
    
    # Compute the principal vector
    PrVec = LeastSquaresLine( Backbone.positions, Backbone.positions[-1] - Backbone.positions[0] )
    
    # Ensure its rigth orientation 
    PrVec = PrVec if np.dot( PrVec, Backbone.positions[-1] - Backbone.positions[0] ) >= 0 else -PrVec
    
    return 


def SplitLeaflets( frame ):
    '''
    SplitLeaflets:
     - Determines the composition of each leaflet of the bilayer
    '''
    global UpperLipRB, UpperLipid, LowerLipRB, LowerLipid
    '''
    Leaflet = MDAnalysis.analysis.leaflet.LeafletFinder( u, SDX.LipRB, cutoff=22 )
    
    if Leaflet.groups(0).center_of_geometry()[2] > Leaflet.groups(1).center_of_geometry()[2]:
        UpperLipRB = Leaflet.groups(0).select_atoms( SDX.LipRB )
        UpperLipid = u.select_atoms( 'resid {}:{}'.format( UpperLipRB.resids[0],UpperLipRB.resids[-1] ) )
        LowerLipRB  = Leaflet.groups(1).select_atoms( SDX.LipRB )
        LowerLipid = u.select_atoms( 'resid {}:{}'.format( LowerLipRB.resids[0],LowerLipRB.resids[-1] ) )
    else:
        UpperLipRB = Leaflet.groups(1).select_atoms( SDX.LipRB )
        UpperLipid = u.select_atoms( 'resid {}:{}'.format( UpperLipRB.resids[0],UpperLipRB.resids[-1] ) )
        LowerLipRB  = Leaflet.groups(0).select_atoms( SDX.LipRB )
        LowerLipid = u.select_atoms( 'resid {}:{}'.format( LowerLipRB.resids[0],LowerLipRB.resids[-1] ) )
    return
    
    '''
    
    COG = u.select_atoms( SDX.Membr ).center_of_geometry()[2]
    
    UpperLipRB = u.select_atoms( SDX.LipRB + ' and prop z >' + str( COG ) )
    UpperLipid = u.select_atoms( SDX.Lipid + ' and prop z >' + str( COG ) )
    
    LowerLipRB = u.select_atoms( SDX.LipRB + ' and prop z <' + str( COG ) )
    LowerLipid = u.select_atoms( SDX.Lipid + ' and prop z <' + str( COG ) )
    
    #UpperMemRB = u.select_atoms( SDX.MemRB + ' and prop z >' + str( COG ) )
    #UpperMembr = u.select_atoms( SDX.Membr + ' and prop z >' + str( COG ) )
    
    #LowerMemRB = u.select_atoms( SDX.MemRB + ' and prop z <' + str( COG ) )
    #LowerMembr = u.select_atoms( SDX.Membr + ' and prop z <' + str( COG ) )
    
    return


def PBCImage( Point: np.ndarray, Ref: np.ndarray ):
    '''
    PBCImage:
     - Finds the position of a Point in the periodic image which minimizes the
      distance to a reference.
    '''
    
    # Relative position of the point with respect to the reference
    Position = Point - Ref
    
    # Squared distance, in components, of the point to the reference
    D2 = Position * Position
    
    # Squared distance, in components, of the periodic images to the reference
    D2im1 = ( Position + frame.dimensions[:3] ) ** 2
    D2im2 = ( Position - frame.dimensions[:3] ) ** 2
    
    return np.array( [ Point[i] + frame.dimensions[i] if ( D2im1[i] < D2[i] and D2im1[i] < D2im2[i] ) 
                         else Point[i] - frame.dimensions[i] if ( D2im2[i] < D2[i] and D2im2[i] < D2im1[i] ) 
                         else Point[i] for i in range(3) ] )    


def ProcessAngles():
    '''
    ProcessAngles:
     - Determines the Euler angles
     
    WARNING: NOT FINISHED
    '''
    
    Phases = [ 0, 0, 0 ]
    
    for i, t in enumerate( Results[ "angles" ] ):
        if i == 0:
            Angles = np.array( [ [ t/1000, 0,0,0 ] ] )
            angles_ref = Results[ "angles" ][ t ]
        else:
            
            angles = np.array( [ Results[ "angles" ][ t ][0] - angles_ref[0],
                                 Results[ "angles" ][ t ][1] - angles_ref[1],
                                 Results[ "angles" ][ t ][2] - angles_ref[2] ] )
            
            for j in range(3):
                if ( angles[j] < np.pi/2. ) and ( Angles[-1,j] > 1.5*np.pi ):  Phases[j] += 2 * np.pi
                elif ( angles[j] > 1.5*np.pi ) and ( Angles[-1,j] < np.pi/2 ): Phases[j] -= 2 * np.pi
                
            angles = ( ( angles + Phases ) / np.pi ).tolist()
            
            Angles = np.vstack( [ Angles, np.array( [ [ t/1000, *angles ] ] ) ] )
            
    return pd.DataFrame( Angles, columns = [ 'Time', 'Yaw', 'Pitch', 'Roll'] )


def ProcessPepDF( Windows: list = [ 5, 50, 100, 200 ] ):
    '''
    ProcessPepDF:
     - Finds the displacement and rotation of the peptide in the plane of the membrane.
    
    '''
    global Disp, Angl
    
    # An extra phase term
    Phase = 0
    
    # Find the angle of the peptide with the X axis in the first frame
    Results[ "PepDF" ][ "Ang" ] = [ FindAngle( Results[ "PepDF" ][ "Vec" ][0] ) ]
    
    for i, Vec in enumerate( Results[ "PepDF" ][ "Vec" ][1:] ):
        
        # Find the angle for each frame
        Ang = FindAngle( Vec )
        Ref = FindAngle( Results[ "PepDF" ][ "Vec" ][i] )
        
        # Correction of the phase (avoid 2π jumps)
        if ( Ang < np.pi/2. ) and ( Ref > 1.5*np.pi ): Phase += 2 * np.pi
        elif ( Ang > 1.5*np.pi ) and ( Ref < np.pi/2 ): Phase -= 2 * np.pi
        
        # Save the values
        Results[ "PepDF" ][ "Ang" ].append( Ang + Phase )
        
        
    # Empty dictionaries for the results
    Time = { window: [] for window in Windows }
    Disp = { window: [] for window in Windows }
    Angl = { window: [] for window in Windows }
    
    # For each window
    for window in Windows:
    
        # Convert the window of time to a window of frames
        Frames = max( 1, int( window * 1000 / ( dt * fs ) ) ) 
    
        # Go through the trajectory, except for the number of frames equivalent to each window
        for i in range( Frames, len( Results[ "PepDF" ][ "Time" ] ) ):
            
            # The time associated to each meassure
            Time[ window ].append( Results[ "PepDF" ][ "Time" ][ i ] )
            
            # The displacement of the peptide for a time equal to the window
            Disp[ window ].append( np.linalg.norm( Results[ "PepDF" ][ "COG" ][ i ] - Results[ "PepDF" ][ "COG" ][ i - Frames ] ) / 10 )
            
            # The change in angle in the same time
            Angl[ window ].append( np.rad2deg( Results[ "PepDF" ][ "Ang" ][ i ] - Results[ "PepDF" ][ "Ang" ][ i - Frames ] ) )
    
        # Determine a number of bins given by the square root of the lenght of the data series
        Bins = int( np.sqrt( len( Time[ window ] ) ) )
        
        # Numerical parameters of the figures
        FigWidth = 10; FigHeight = 8
        width = 0.48 ; height = width * FigWidth / FigHeight
        width_cbar = 0.05
        spacex = 0.04; spacey = spacex * FigWidth / FigHeight
        
        # Some calculations
        Dimensions_2D_plot = [ spacex * 3, spacey * 2, width, height ]
        Dimensions_Pos_hist = [ spacex * 3, spacey * 2 + height + spacey, width, 1 - 4 * spacey - height ]
        Dimensions_Ang_hist = [ spacex * 3 + width + spacex, spacey * 2, 1 - 7 * spacex - width - width_cbar, height ]
        Dimensions_CBar = [ 1 - 2 * spacex - width_cbar, spacey * 2, width_cbar, height ]
        
        # Definition of the elements of the figure
        fig = plt.figure( figsize = ( FigWidth, FigHeight ) )
        ax_0 = fig.add_axes( [0,0,0,0] )
        ax_c = fig.add_axes( Dimensions_2D_plot )
        ax_p = fig.add_axes( Dimensions_Pos_hist )
        ax_a = fig.add_axes( Dimensions_Ang_hist )
        ax_b = fig.add_axes( Dimensions_CBar )
        
        # Representation of the data
        nD, BinsD, patchesD = ax_p.hist( Disp[ window ], bins = Bins )
        nA, BinsA, patchesA = ax_a.hist( Angl[ window ], bins = Bins, orientation = 'horizontal' )
        
        # Time scale
        cmap = mcol.ListedColormap( [np.array([1,1,1,1])] + [ BuildCmap(["rebeccapurple","#003b6f","forestgreen"] )(i) for i in range(255) ] )
        #from matplotlib import cm
        #cmap = mcol.ListedColormap( [np.array([1,1,1,1])] + [ cm.get_cmap('plasma', 255)(i) for i in range(255) ] )
        
        BinD = ( np.max( BinsD ) - np.min( BinsD ) ) / len( BinsD )
        BinA = ( np.max( BinsA ) - np.min( BinsA ) ) / len( BinsA )
        
        BinD2 = ( np.max( BinsD ) - np.min( BinsD ) ) / int( Bins/2 )
        BinA2 = ( np.max( BinsA ) - np.min( BinsA ) ) / int( Bins/2 )
        
        TimeD = []; TimeA = []; TimeC = np.zeros( ( int( Bins/2 ), int( Bins/2 ) ) )
        for i in ProgressBar( range( Bins ) , 'PepDF {} binning 1: '.format( window ), 20 ):
            
            # The times of the frames in the distance bin
            TimeBin = [ Time[ window ][t] for t in range( len( Disp[ window ] ) ) if ( Disp[ window ][t] >= i * BinD + BinsD[0] and Disp[ window ][t] < ( i+1 ) * BinD + BinsD[0] ) ]
            
            # The mean time for each bin in the distance histogram
            if len( TimeBin ) > 0:  TimeD.append( np.mean( TimeBin ) )
            else: TimeD.append( Time[ window ][0] )
            
            # The times of the frames in the angle bin
            TimeBin = [ Time[ window ][t] for t in range( len( Angl[ window ] ) ) if ( Angl[ window ][t] >= i * BinA + BinsA[0] and Angl[ window ][t] < ( i+1 ) * BinA + BinsA[0] ) ]
            
            if len( TimeBin ) > 0:  TimeA.append( np.mean( TimeBin ) )
            else: TimeA.append( Time[ window ][0] )
        
        for i in ProgressBar( range( int( Bins/2 ) ) ,'PepDF {} binning 2: '.format( window ), 20):
            for j in range( 0, int( Bins/2 )  ):
                TimeBin = [ Time[ window ][t] for t in range( len( Angl[ window ] ) ) if ( ( Disp[ window ][t] >= i * BinD2 + BinsD[0] and Disp[ window ][t] < ( i+1 ) * BinD2 + BinsD[0] ) 
                                                                                      and ( Angl[ window ][t] >= j * BinA2 + BinsA[0] and Angl[ window ][t] < ( j+1 ) * BinA2 + BinsA[0] ) ) ]
                if len( TimeBin ) > 0:  TimeC[i,j] = np.mean( TimeBin )
                else: TimeC[i,j] = Time[ window ][0]
        
        for i, p in enumerate(patchesD):
            plt.setp(p, 'facecolor', cmap( ( TimeD[i] - Time[ window ][0] ) / ( Time[ window ][-1] - Time[ window ][0] ) ) ) 
            
        for i, p in enumerate(patchesA):
            plt.setp(p, 'facecolor', cmap( ( TimeA[i] - Time[ window ][0] ) / ( Time[ window ][-1] - Time[ window ][0] ) ) ) 
        
        # Estilo vello
        #ax_c.scatter( Disp[ window ], Angl[ window ], alpha = 1, c = Time[ window ]/np.max( Time[ window ] ), cmap = cmap)
        
        # Estilo novo
        Bins2d, X2D, Y2D, _ = ax_0.hist2d( Disp[ window ], Angl[ window ], int( Bins/2 ) )
        ax_c.pcolormesh( X2D[:-1] , Y2D[:-1], TimeC.T, cmap = cmap  )
        ax_c.contour( X2D[:-1], Y2D[:-1], Bins2d.T, levels = 7, cmap = 'gray'  )
        
        # Axes' properties
        ax_p.set_xticklabels([])
        ax_p.set_ylabel('# Counts')
        ax_p.set_xlim( [0, np.max( BinsD ) ] )
        ax_p.set_ylim( [0, 1.1 * np.max( nD ) ] )
        
        ax_a.set_yticklabels([])
        ax_a.set_xlabel('# Counts')
        ax_a.set_ylim( [ -np.max( np.abs( BinsA ) ), np.max( np.abs( BinsA ) ) ] )
        ax_a.set_xlim( [ 0, 1.1 * np.max( np.abs( nA ) ) ] )
        
        ax_c.set_xlabel('Lateral displacement (nm)')
        ax_c.set_ylabel('Precession (degrees)')
        ax_c.set_xlim( [ 0, np.max( BinsD ) ] )
        ax_c.set_ylim( [ -np.max( np.abs( BinsA ) ), np.max( np.abs( BinsA ) ) ] )
        
        fig.suptitle( t = 'PepDF', x = (3 * spacex + width + 2 * spacex) , y = 0.92, fontsize = 30, fontweight = 'bold' )
        fig.text( x = ( 3 * spacex + width + spacex), y = 0.82, s='Time window: {} ns'.format( window ), fontsize = 25, transform=fig.transFigure, fontweight = 'bold' )
        
        cbar = mpl.colorbar.ColorbarBase( ax_b ,cmap = BuildCmap(["rebeccapurple","#003b6f","forestgreen"] ) )
        cbar.set_label('Normalized Mean Time', fontsize = 20)
        
        plt.savefig( args.out + '/PepDF_{}.png'.format( window ), dpi=300 )
        
        # Save the data
        PepDF = pd.DataFrame( np.array( [ [ BinsD[i], nD[i], TimeD[i], BinsA[i], nA[i], TimeA[i] ] for i in range(Bins) ] ),
                             columns = [ "Bins disp.", "Counts disp.", "Av. time disp.", "Bins ang.", "Counts ang.", "Av. time ang." ] )
        PepDF.to_csv( args.out + '/PepDF_{}.csv'.format( window ) )
        
    return


def PlotLineal( Name: str, Data: np.ndarray, Title: str, Legend: list, Colors: list, 
                XLabel: str = None, YLabel: str = None, 
                XLims: list = None, XTick: float = None,
                YLims: list = None, YTick: float = None,
                Correction: bool = False, Rolling: int = 10, 
                Jump: callable = None ):
    '''
    PlotLineal:
     - Representation of curves
    '''
    # Create a new figure
    fig,axs=plt.subplots()
    axs.set_title( Title )
    
    # Plot data    
    for i in range( len( Legend ) ):
        if Jump and Rolling:
            
            # Find the cross of the data with respect to the reference
            Jumps = Jump( Data.iloc[:,i+1] )
            
            # Plot the elements between intersections as differenciated lines
            for j in range( len( Jumps ) - 1 ):
                axs.plot( Data.iloc[ Jumps[j]:Jumps[j+1], 0 ], 
                          Data.iloc[ Jumps[j]:Jumps[j+1], i+1 ].rolling( Rolling, min_periods = 1 ).mean().tolist(), 
                         '-', linewidth = 1 + 2*i if Correction else 3, color = Colors[i], alpha = 1, zorder = len( Legend ) - i )
        
            # After the last intersection, print the rest of the values
            axs.plot( Data.iloc[ Jumps[-1]:, 0 ], 
                      Data.iloc[ Jumps[-1]:, i+1 ].rolling( Rolling, min_periods = 1 ).mean().tolist(), 
                    '-', linewidth = 1 + 2*i if Correction else 3, color = Colors[i], alpha = 1, zorder = len( Legend ) - i  )
            # Print the legend
            axs.plot( XLims[0]-42 , Data.iloc[:1,i+1] , linewidth = 4 , color = Colors[i] , alpha = 1, label = Legend[i] )
        
        if not Jump and Rolling:
            # Print the data
            axs.plot( Data.iloc[:,0], Data.iloc[:,i+1].rolling( Rolling, min_periods = 1 ).mean().tolist(),
                 '-', linewidth = 1 + 2*i if Correction else 3, color = Colors[i], alpha = 1, zorder = len( Legend ) - i )
            # Print a dummy with the legend
            axs.plot( XLims[0]-42 , Data.iloc[:1,i+1] , linewidth = 4 , color = Colors[i] , alpha = 1, label = Legend[i] )

        if Jump and not Rolling:
            # Find the cross of the data with respect to the reference
            Jumps = Jump( Data.iloc[:,i+1] )
            
            # Plot the elements between intersections as differenciated lines
            for j in range( len( Jumps ) - 1 ):
                axs.plot( Data.iloc[ Jumps[j]:Jumps[j+1], 0 ], 
                          Data.iloc[ Jumps[j]:Jumps[j+1], i+1 ], 
                         '-', linewidth = 1 + 2*i if Correction else 3, color = Colors[i], alpha = 1, zorder = len( Legend ) - i )
        
            # After the last intersection, print the rest of the values
            axs.plot( Data.iloc[ Jumps[-1]:, 0 ], 
                      Data.iloc[ Jumps[-1]:, i+1 ], 
                    '-', linewidth = 1 + 2*i if Correction else 3, color = Colors[i], alpha = 1, zorder = len( Legend ) - i  )
            # Print the legend
            axs.plot( XLims[0]-42 , Data.iloc[:1,i+1] , linewidth = 4 , color = Colors[i] , alpha = 1, label = Legend[i] )
        
        if not Jump and not Rolling:
            # Print the data
            axs.plot( Data.iloc[:,0], Data.iloc[:,i+1],
                 '-', linewidth = 1 + 2*i if Correction else 3, color = Colors[i], alpha = 1, zorder = len( Legend ) - i )
            # Print a dummy with the legend
            axs.plot( XLims[0]-42 , Data.iloc[:1,i+1] , linewidth = 4 , color = Colors[i] , alpha = 1, label = Legend[i] )
            
    # X-axis properties
    axs.set_xlabel( XLabel )
    if XLims:
        axs.set_xlim( XLims[0], XLims[1] )
        axs.set_xticks( np.arange( XLims[0], XLims[1], XTick ) )
    
    # Y-axis properties
    axs.set_ylabel( YLabel )
    if YLims:
        axs.set_ylim( YLims[0], YLims[1] )
        axs.set_yticks( np.arange( YLims[0], YLims[1], YTick ) )
    
    # Legend
    if len( Legend ) > 1:
        axs.legend()
    
    # Figure properties
    fig.set_size_inches(9, 6)
    plt.tight_layout()
    plt.savefig( args.out + '/' + Name + '.png', dpi=300 )
    
    return


# def PlotTwin( Name: str, Data: np.ndarray, Title: str, Legend: list, Colors: list, 
#               XLabel: str = None, YLabel: str = None,
#               XLims: list = None, XTick: float = None,
#               YLims1: list = None, YTick1: float = None, 
#               YLims2: list = None, YTick2: float = None,
#               Rolling: int = 10, Correction: bool = False):
#     # Create a new figure
#     fig,ax1=plt.subplots()
#     ax1.set_title( Title )
#     # First Y axis 
#     ax1.plot( Data.iloc[:,0], Data.iloc[:,1].rolling( Rolling, min_periods = 1 ).mean().tolist(),
#          '-', linewidth = 3, color = Colors[0],  alpha = 0.8)
#     # First Y-axis properties
#     ax1.set_ylabel( YLabel )
#     if YLims1:
#         ax1.set_ylim( YLims1[0], YLims1[1] )
#         ax1.set_yticks( np.arange( YLims1[0], YLims1[1], YTick1 ) )
#     # First X-axis properties (it will be common to both plots)
#     ax1.set_xlabel( XLabel )
#     if XLims:
#         ax1.set_xlim( XLims[0], XLims[1] )
#         ax1.set_xticks( np.arange( XLims[0], XLims[1], XTick ) )
#     # Second Y axis
#     ax2 = ax1.twinx()
#     ax2.plot( Data.iloc[:,0], Data.iloc[:,2].rolling( Rolling, min_periods = 1 ).mean().tolist(),
#          '-', linewidth = 3, color = Colors[1],  alpha = 0.8)
#     # Second Y-axis properties
#     if YLims2:
#         ax2.set_ylim( YLims2[0], YLims2[1] )
#         ax2.set_yticks( np.arange( YLims2[0], YLims2[1], YTick2 ) )
#     # Dummy plot for the legend
#     ax2.plot( XLims[0]-42 , [0] , linewidth = 4 , color = Colors[0] , alpha = 0.8, label = Legend[0] )
#     ax2.plot( XLims[0]-42 , [0] , linewidth = 4 , color = Colors[1] , alpha = 0.8, label = Legend[1] )
#     ax2.legend()
#     # Change Y tick color to match the legend 
#     plt.setp( plt.getp(ax1.axes, 'yticklabels'), color=Colors[0])
#     plt.setp( plt.getp(ax2.axes, 'yticklabels'), color=Colors[1])
#     # Figure properties
#     fig.set_size_inches(9, 6)
#     plt.tight_layout()
#     plt.savefig( args.out + '/' + Name + '.png', dpi=300 )
#     return


# def PlotHisto( Name: str, Data: np.ndarray, Title: str, Legend: list, Colors: list, 
#               XLabel: str = None, YLabel1: str = None, YLabel2: str = None,
#               XLims: list = None, XTick: float = None,
#               YLims1: list = None, YTick1: float = None, 
#               YLims2: list = None, YTick2: float = None,
#               Correction: bool = False, Rolling: int = 1,
#               Instantaneous: bool = False, Jump: Callable = None):
#     with plt.rc_context({"hatch.linewidth":16/3}):
#         fig, ax = plt.subplots( ncols=2, sharey=True, gridspec_kw={'width_ratios': [5, 1]} )
#         plt.subplots_adjust(wspace=0.075, hspace=0) # Reduces the space between subplots
#         ax[0].set_title( Title )
#         for i in range( len( Legend ) ):
#             # Plot the instantaneous data as light circles
#             if Instantaneous:
#                 print(Data.iloc[:,i+1])
#                 ax[0].plot( Data.iloc[:,0] , Data.iloc[:,i+1], 'wo', mec=Colors[i], alpha=0.5, zorder = 0 )
#             # Plot the rolling mean as a solid line
#             if Jump:
#                 Jumps = JumpFunc( Data.iloc[:,i+1] )
#                 print(Jumps)
#                 for j in range( len( Jumps ) - 1 ):
#                     ax[0].plot( Data.iloc[ Jumps[j]:Jumps[j+1], 0 ], 
#                               Data.iloc[ Jumps[j]:Jumps[j+1], i+1 ].rolling( 10, min_periods = 1 ).mean().tolist(), 
#                              '-', linewidth = 3 if Correction else 3, color = Colors[i], zorder = len( Legend ) - i )
#             else:
#                 ax[0].plot( Data.iloc[:,0] , Data.iloc[:,i+1].rolling( 10, min_periods = 1 ).mean().tolist(), 
#                            '-', linewidth = 1 + 2*i**1.5 if Correction else 3, color=Colors[i], zorder = len( Legend ) - i )
#             # Represent the instantaneous data as an histogram
#             if not Correction:
#                 N, bins, _ = ax[1].hist( Data.iloc[:,i+1], bins=int( np.sqrt( len( Data.iloc[:,i+1] ) ) ), color=Colors[i], orientation="horizontal", ec='k', zorder = len( Legend ) - i, alpha=0.5 )
#             ax[0].plot( Data.iloc[:1,0]-42 , Data.iloc[:1,i+1] , linewidth = 4 , color = Colors[i] , alpha = 1, label = Legend[i] )
#         if Correction:
#             N, bins, _ = ax[1].hist( Data.iloc[:,i+1], bins=int( np.sqrt( len( Data.iloc[:,i+1] ) ) ), color='dimgray', edgecolor='k', orientation="horizontal" )
#         # Legend
#         if len( Legend ) > 1:
#             ax[0].legend()
#         # First Y-axis properties
#         ax[0].set_ylabel( YLabel1 )
#         if YLims1:
#             ax[0].set_ylim( YLims1[0], YLims1[1] )
#             ax[0].set_yticks( np.arange( YLims1[0], YLims1[1], YTick1 ) )
#         # First X-axis properties (it will be common to both plots)
#         ax[0].set_xlabel( XLabel )
#         if XLims:
#             ax[0].set_xlim( XLims[0], XLims[1] )
#             ax[0].set_xticks( np.arange( XLims[0], XLims[1], XTick ) )
#         # Second Y-axis properties
#         ax[1].set_xlabel( YLabel2 )
#         if YLims2:
#             ax[1].set_ylim( YLims2[0], YLims2[1] )
#             ax[1].set_yticks( np.arange( YLims2[0], YLims2[1], YTick2 ) )
#         # Figure properties
#         fig.set_size_inches(11, 6)
#         plt.tight_layout()
#         plt.savefig( args.out + '/' + Name + '.png', dpi=300 )
#     return

def PlotTwin( Name: str, Data: np.ndarray, Title: str, Legend: list, Colors: list, 
              XLabel1: str = None, XLabel2: str = None, YLabel: str = None,
              XLims1: list = None, XTick1: float = None,
              XLims2: list = None, XTick2: float = None, 
              YLims: list = None, YTick: float = None,
              Correction: bool = False, Rolling: int = 10,
              Instantaneous: bool = False, Jump: Callable = None ):
    
    with plt.rc_context({"hatch.linewidth":16/3}):
        fig, ax = plt.subplots( nrows=len(Legend), ncols=2, sharex = 'col', sharey='row', gridspec_kw={'width_ratios': [5, 1]} )
        plt.subplots_adjust(wspace=0.075, hspace=0.08)
        
        fig.suptitle( Title, fontsize=25)
        fig.supylabel( YLabel, fontsize=25 )
        
        for i in range( len( Legend ) ):
            # Plot the instantaneous data as light circles
            if Instantaneous:
                ax[i,0].plot( Data.iloc[:,0] , Data.iloc[:,i+1], 'wo', mec=Colors[i], alpha=0.5, zorder = 0 )
            # Plot the rolling mean as a solid line
            if Jump:
                Jumps = JumpFunc( Data.iloc[:,i+1] )
                for j in range( len( Jumps ) - 1 ):
                    ax[i,0].plot( Data.iloc[ Jumps[j]:Jumps[j+1], 0 ], 
                              Data.iloc[ Jumps[j]:Jumps[j+1], i+1 ].rolling( Rolling, min_periods = 1 ).mean().tolist(), 
                             '-', linewidth = 3 if Correction else 3, color = Colors[i], zorder = len( Legend ) - i )
            else:
                ax[i,0].plot( Data.iloc[:,0] , Data.iloc[:,i+1].rolling( Rolling, min_periods = 1 ).mean().tolist(), 
                           '-', linewidth = 1 + 2*i**1.5 if Correction else 3, color=Colors[i], zorder = len( Legend ) - i )
    
            N, bins, _ = ax[i,1].hist( Data.iloc[:,i+1], bins=int( np.sqrt( len( Data.iloc[:,i+1] ) ) ), color=Colors[i], orientation="horizontal", ec='k', zorder = len( Legend ) - i, alpha=0.5 )
        
            ax[i,0].plot( Data.iloc[:1,0]-42 , Data.iloc[:1,1] , linewidth = 4 , color = Colors[i] , alpha = 1, label = Legend[i] )
    
            # Legend
            if len( Legend ) > 1:
                ax[i,0].legend(loc='upper right')
            
            # Y-axis properties
            if YLims:
                ax[i,0].set_ylim( YLims[i][0], YLims[i][1] )
                ax[i,0].set_yticks( np.arange( YLims[i][0], YLims[i][1], YTick[i] ) )
        
        # First X-axis properties (it will be common to both plots)
        ax[-1,0].set_xlabel( XLabel1 )
        if XLims1:
            ax[i,0].set_xlim( XLims1[0], XLims1[1] )
            ax[i,0].set_xticks( np.arange( XLims1[0], XLims1[1], XTick1 ) )
            
        # Second X-axis properties
        ax[-1,1].set_xlabel( XLabel2 )
        if XLims2:
            ax[i,1].set_xlim( XLims2[0], XLims2[1] )
            ax[i,1].set_xticks( np.arange( XLims2[0], XLims2[1], XTick2 ) )

        # Figure properties
        fig.set_size_inches(11, 6)
        plt.tight_layout()
        plt.savefig( args.out + '/' + Name + '.png', dpi=300 )

    return


def PlotHisto( Name: str, Data: np.ndarray, Title: str, Legend: list, Colors: list, 
               XLabel: str = None, YLabel1: str = None, YLabel2: str = None,
               XLims: list = None, XTick: float = None,
               YLims1: list = None, YTick1: float = None, 
               YLims2: list = None, YTick2: float = None,
               Correction: bool = False, Rolling: int = 10,
               Instantaneous: bool = False, Jump: Callable = None ):
    
    with plt.rc_context({"hatch.linewidth":16/3}):
        fig, ax = plt.subplots( ncols=2, sharey=True, gridspec_kw={'width_ratios': [5, 1]} )
        plt.subplots_adjust(wspace=0.075, hspace=0) # Reduces the space between subplots
    
        ax[0].set_title( Title )
        
        if not Correction:
            for i in range( len( Legend ) ):
                # Plot the instantaneous data as light circles
                if Instantaneous:
                    ax[0].plot( Data.iloc[:,0] , Data.iloc[:,i+1], 'wo', mec=Colors[i], alpha=0.5, zorder = 0 )
                # Plot the rolling mean as a solid line
                if Jump:
                    Jumps = JumpFunc( Data.iloc[:,i+1] )
                    for j in range( len( Jumps ) - 1 ):
                        ax[0].plot( Data.iloc[ Jumps[j]:Jumps[j+1], 0 ], 
                                  Data.iloc[ Jumps[j]:Jumps[j+1], i+1 ].rolling( Rolling, min_periods = 1 ).mean().tolist(), 
                                 '-', linewidth = 3 if Correction else 3, color = Colors[i], zorder = len( Legend ) - i )
                else:
                    ax[0].plot( Data.iloc[:,0] , Data.iloc[:,i+1].rolling( Rolling, min_periods = 1 ).mean().tolist(), 
                               '-', linewidth = 1 + 2*i**1.5 if Correction else 3, color=Colors[i], zorder = len( Legend ) - i )

                N, bins, _ = ax[1].hist( Data.iloc[:,i+1], bins=int( np.sqrt( len( Data.iloc[:,i+1] ) ) ), color=Colors[i], orientation="horizontal", ec='k', zorder = len( Legend ) - i, alpha=0.5 )
            
                ax[0].plot( Data.iloc[:1,0]-42 , Data.iloc[:1,1] , linewidth = 4 , color = Colors[i] , alpha = 1, label = Legend[i] )
            
        if Correction:
            i=0
            ax[0].plot( Data.iloc[:,0] , Data.iloc[:,i+1], 'wo', mec=Colors[i], alpha=0.5, zorder = 0 )
            if Jump:
                Jumps = JumpFunc( Data.iloc[:,i+1] )
                for j in range( len( Jumps ) - 1 ):
                    ax[0].plot( Data.iloc[ Jumps[j]:Jumps[j+1], 0 ], 
                              Data.iloc[ Jumps[j]:Jumps[j+1], i+1 ].rolling( Rolling, min_periods = 1 ).mean().tolist(), 
                             '-', linewidth = 3, color = Colors[i], zorder = len( Legend ) - i )
            else:
                ax[0].plot( Data.iloc[:,0] , Data.iloc[:,i+1].rolling( Rolling, min_periods = 1 ).mean().tolist(), 
                           '-', linewidth = 3, color=Colors[i], zorder = len( Legend ) - i )
            N, bins, _ = ax[1].hist( Data.iloc[:,i+1], bins=int( np.sqrt( len( Data.iloc[:,i+1] ) ) ), color=Colors[i], edgecolor='k', orientation="horizontal" )
            
            for i in range( len( Legend ) ):
                ax[0].plot( Data.iloc[:1,0]-42 , Data.iloc[:1,1] , linewidth = 4 , color = Colors[i] , alpha = 1, label = Legend[i] )
            
            #ax[0].annotate('NOTE: In this system, both leaflets have the same number of lipids,\n thus the values for their APL are overlapped in the plots',
            #               xy=(0.01, 0),xycoords='axes fraction', fontsize=12, horizontalalignment='left', verticalalignment='bottom')
            
        # Legend
        if len( Legend ) > 1:
            ax[0].legend(loc='upper right')
            
        # First Y-axis properties
        ax[0].set_ylabel( YLabel1 )
        if YLims1:
            ax[0].set_ylim( YLims1[0], YLims1[1] )
            ax[0].set_yticks( np.arange( YLims1[0], YLims1[1], YTick1 ) )
        
        # First X-axis properties (it will be common to both plots)
        ax[0].set_xlabel( XLabel )
        if XLims:
            ax[0].set_xlim( XLims[0], XLims[1] )
            ax[0].set_xticks( np.arange( XLims[0], XLims[1], XTick ) )
            
        # Second Y-axis properties
        ax[1].set_xlabel( YLabel2 )
        if YLims2:
            ax[1].set_ylim( YLims2[0], YLims2[1] )
            ax[1].set_yticks( np.arange( YLims2[0], YLims2[1], YTick2 ) )

        # Figure properties
        fig.set_size_inches(11, 6)
        plt.tight_layout()
        plt.savefig( args.out + '/' + Name + '.png', dpi=300 )
    return


def PlotBar( Name: str, 
             Data: np.ndarray, 
             Title: str,  
             Colors: list, 
             YLabel: str = None ):
    '''
    PlotBar:
     - Bar plot for the number of contacts per residue
    '''
    
    # Color palette
    #Colors = [ SDX.MEMBCOMP[ lipid ][ 'color' ] for lipid in MemSys ]
    #if len(Colors) == 1: Colors += Colors
    
    # Create plot (Uxia's version, modified)
    fig = plt.figure()
    plot = Data.plot( kind = 'bar', stacked = True, cmap = BuildCmap( Colors ), edgecolor='k', linewidth=1, rot=0, figsize=(9,6), legend='reverse' )
    plot.set_title( Title )
    plot.set_ylabel( YLabel )
    
    # Vertical line to separate by class
    for i in [2,6,16]:
        plt.axvline(i, color='k', lw=0.6)
    
    plt.minorticks_off()
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)
    
    # Labels with the type of amino acid. WARNING, if the format of the graph changes, these values are no longer right
    plot.text(0.45, 0.10, "Acidic", fontsize=14, bbox=dict(facecolor='k', alpha=0), transform=fig.transFigure )
    plot.text(1.03, 0.10, "Basic", fontsize=14, bbox=dict(facecolor='k', alpha=0), transform=fig.transFigure )
    plot.text(2.08, 0.10, "Hydrophobic", fontsize=14, bbox=dict(facecolor='k', alpha=0), transform=fig.transFigure )
    plot.text(3.59, 0.10, "Polar", fontsize=14, bbox=dict(facecolor='k', alpha=0), transform=fig.transFigure )
    
    plt.savefig( args.out + '/' + Name + '.png', dpi=300 )
    
    return


def PlotDensmap( ):
    '''
    PlotDensmap:
     - Density map of lipids around the peptide.
    '''
    
    for lipid in Results[ "densmap" ]:
        
        whole = np.vstack( [ Results[ "densmap" ][ lipid ][ "Upper" ][1:], 
                             Results[ "densmap" ][ lipid ][ "Lower" ][1:] ] )
        
## Create the figure
        fig, _axs  = plt.subplots(nrows=1, ncols=3, sharey= False, sharex= False)
        fig.set_size_inches(24,6)
        axs = _axs.flatten()
        fig.suptitle('Density Map of ' +  lipid, fontsize = 26, fontweight='bold')
        
        # Number of bins along each dimension
        nbins = 180
        # Dimensions of the plot
        rang =  [0, round(frame.dimensions[0]/10, 4) ] 
        # Common colormap
        #cmap = 'inferno'
        cmap = mcol.ListedColormap( [np.array([1,1,1,1])] + mpl.cm.get_cmap('cividis').colors )
        
## Histograms with the data
        # Upper leaflet XY plot
        if Results[ "densmap" ][ lipid ][ "Upper" ][1:].size:
            h_u, x_u, y_u = np.histogram2d( 
                Results[ "densmap" ][ lipid ][ "Upper" ][1:,0]/10,
                Results[ "densmap" ][ lipid ][ "Upper" ][1:,1]/10, 
                bins = [ nbins, nbins ], range = [ rang, rang ] )
            Null_upper = False
        else:
            h_u, x_u, y_u = np.histogram2d( 
                [], [], bins = [ nbins, nbins ], range = [ rang, rang ] )
            Null_upper = True
        
        # Lower leaflet XY plot
        if Results[ "densmap" ][ lipid ][ "Lower" ][1:].size:
            h_l, x_l, y_l = np.histogram2d( 
                Results[ "densmap" ][ lipid ][ "Lower" ][1:,0]/10,
                Results[ "densmap" ][ lipid ][ "Lower" ][1:,1]/10, 
                bins = [ nbins, nbins ], range = [ rang, rang ] )
            Null_lower = False
        else:
            h_l, x_l, y_l = np.histogram2d( 
                [], [], bins = [ nbins, nbins ], range = [ rang, rang ] )
            Null_lower = True
        
        # Transversal YZ plot
        if whole.size:
            h_t, x_t, y_t = np.histogram2d( 
                whole[:,1]/10,
                whole[:,2]/10, 
                bins = [ nbins, nbins ], range = [ rang, [ -round( frame.dimensions[2]/10, 4 )/2, round( frame.dimensions[2]/10, 4 )/2 ] ] )
            Null_side = False
        else:
            h_t, x_t, y_t = np.histogram2d( 
                [], [], bins = [ nbins, nbins ], range = [ rang, rang ] )
            Null_side = True
        
## Reprocess the data
        h_u *= nbins * nbins / ( 1e-3 * frame.volume * len( u.trajectory[at:lt:args.skip_rough] ))
        h_l *= nbins * nbins / ( 1e-3 * frame.volume * len( u.trajectory[at:lt:args.skip_rough] ))
        h_t *= nbins * nbins / ( 1e-3 * frame.volume * len( u.trajectory[at:lt:args.skip_rough] ))
        
        
## Subfigures
        # Upper leaflet XY plot
        axs[0].set_title('Upper Leaflet, XY')
        xi, yi = np.meshgrid( x_u, y_u )
        xy_u = axs[0].pcolormesh( xi, yi, h_u.T, cmap = cmap )
        if Null_upper: xy_u.set_clim(vmin=0, vmax=1)
        
        axs[0].axis( 'scaled' )
        axs[0].set_xlabel( 'x (nm)' )
        axs[0].set_ylabel( 'y (nm)' )
        axs[0].set_xlim( [ 0, round( frame.dimensions[0]/10, 4 ) ] )
        axs[0].set_ylim( [ 0, round( frame.dimensions[0]/10, 4 ) ] )
        axs[0].tick_params( axis = 'both', direction = 'in', top = 'on', right = 'on')
        
        cbar0 = fig.colorbar( xy_u, ax=axs[0], shrink = 0.9, format=mticker.FuncFormatter(Format) )
        cbar0.ax.set_title('nm$^{-3}$', {'fontsize': 18 }, pad = 15)
        if Null_upper: cbar0.set_ticks([0])
        
        # Lower leaflet XY plot
        axs[1].set_title('Lower Leaflet, XY')
        xi, yi = np.meshgrid( x_l, y_l )
        xy_l = axs[1].pcolormesh( xi, yi, h_l.T, cmap = cmap )
        if Null_lower: xy_l.set_clim(vmin=0, vmax=1)
        
        axs[1].axis( 'scaled' )
        axs[1].set_xlabel( 'x (nm)' )
        axs[1].set_ylabel( 'y (nm)' )
        axs[1].set_xlim( [ 0, round( frame.dimensions[0]/10, 4 ) ] )
        axs[1].set_ylim( [ 0, round( frame.dimensions[0]/10, 4 ) ] )
        axs[1].tick_params( axis = 'both', direction = 'in', top = 'on', right = 'on')
        
        cbar1 = fig.colorbar( xy_l, ax=axs[1], shrink = 0.9, format=mticker.FuncFormatter(Format) )
        cbar1.ax.set_title('nm$^{-3}$', {'fontsize': 18 }, pad = 15)
        if Null_lower: cbar1.set_ticks([0])
        
        # Transversal YZ plot
        axs[2].set_title('Transversal View, YZ')
        xi, yi = np.meshgrid( x_t, y_t )
        yz = axs[2].pcolormesh( xi, yi, h_t.T, cmap = cmap )
        if Null_side: yz.set_clim(vmin=0, vmax=1)
        
        axs[2].axis( 'scaled' )
        axs[2].set_xlabel( 'y (nm)') 
        axs[2].set_ylabel( 'z (nm)' )
        axs[2].set_xlim( [ 0, round( frame.dimensions[0]/10, 4 ) ] )
        axs[2].set_ylim( [ -round( frame.dimensions[2]/10, 4 )/2, round( frame.dimensions[2]/10, 4 )/2 ] )
        axs[2].tick_params( axis = 'both', direction = 'in', top = 'on', right = 'on' )

        cbar2 = fig.colorbar( yz, ax=axs[2], shrink = 0.9, format=mticker.FuncFormatter(Format) )
        cbar2.ax.set_title('nm$^{-3}$', {'fontsize': 18 }, pad = 15)
        if Null_side: cbar2.set_ticks([0])
        
        fig.tight_layout()
        
        plt.savefig( args.out + "/" + lipid + ".png", dpi=300) 

    return


def PeptideContactsPDB( Data: pd.core.frame.DataFrame,
                        Name: str ):
    '''
    PeptideContactsPDB
    - Builds a PDB file with the initial structure of the peptide and the number
     of contacts with the lipid in the B-factor
    '''
    
    # Add the contacts as tempfactor for generating a PDB
    u.add_TopologyAttr( 'tempfactors' )
    for atom, col in zip( Backbone, Data.columns ):
        atoms = u.select_atoms('resid {}'.format( atom.resid ))
        atoms.tempfactors = [ Data[col][0] for i in range(len(atoms)) ]
    
    # Write the PDB
    frame = u.trajectory[0]
    u.delete_bonds( Peptides.bonds )
    with MDAnalysis.Writer( args.out + '/{}.pdb'.format( Name ) ) as PDB:
        PDB.write( Peptides )
    PDB.close()
    
    return


def WeightedMean( Values: list, Stdv: list ) -> tuple :
    # Averages data with different standard deviation.
    
    if len(Values) == len(Stdv) : 
        # Weights
        Weight = [ 1 / std**2 for std in Stdv]
        # Mean
        Mean = np.sum( [ Values[i] * Weight[i] for i in range( len( Values ) ) ] )/ np.sum( Weight )
        # Standard deviation of the mean
        Std = np.sqrt( 1 / np.sum( Weight ) )
        return Mean, Std
    else:
        return print('WEIGHTED MEAN ERROR: Different dimensions in lists!')


def ReturnJSON( ):
    '''
    ReturnJSON:
     - Returns a JSON file with the averages for the DB.
    '''
    
    Data = {}
    
## Area per lipid
    # Find the time window to average
    Li = [ i for i, time in enumerate( AreaData["Time"] ) if time * 1000 >= args.average_time ][0]
    Ls = [ i for i, time in enumerate( AreaData["Time"] ) if time * 1000 <= args.last_time ][-1]
    
    Data[ "Area" ] = { value: ErrorACF( AreaData[ value ][ Li:Ls ] ) 
                       for value in [ "Total", "Upper leaflet", "Lower leaflet" ] } 
    
## Center of geometry
    # Find the time window to average
    Li = [ i for i, time in enumerate( COGData["Time"] ) if time * 1000 >= args.average_time ][0]
    Ls = [ i for i, time in enumerate( COGData["Time"] ) if time * 1000 <= args.last_time ][-1]
    
    Data[ "COG" ] = { value: ErrorACF( COGData[ value ][ Li:Ls ] ) 
                      for value in [ 'Peptide', 'Lipids', 'Peptide first BB', 'Peptide last BB',
                                     'Upper lipid HGs', 'Lower lipid HGs' ] }
    
    Data[ "Bilayer thickness" ] = SDX.RoundStdv( np.abs( float( Data["COG"][ "Upper lipid HGs" ][0] ) - float( Data["COG"][ "Lower lipid HGs" ][0] ) ),
                                    np.sqrt( float( Data["COG"][ "Upper lipid HGs" ][1] )**2 + float( Data["COG"][ "Lower lipid HGs" ][1] )**2 ) )
    
    Data[ "Peptide depth" ] = ( SDX.RoundStdv( float( Data["COG"][ "Peptide" ][0] ) - float( Data["COG"][ "Upper lipid HGs" ][0] ),
                                    np.sqrt( float( Data["COG"][ "Peptide" ][1] )**2 + float( Data["COG"][ "Upper lipid HGs" ][1] )**2 ) )
                               if float( Data["COG"][ "Peptide" ][0] ) > float( Data["COG"][ "Lipids" ][0] ) else
                                SDX.RoundStdv( float( Data["COG"][ "Lower lipid HGs" ][0] ) - float( Data["COG"][ "Peptide" ][0] ),
                                    np.sqrt( float( Data["COG"][ "Peptide" ][1] )**2 + float( Data["COG"][ "Lower lipid HGs" ][1] )**2 ) ) )
    
## Contacts
    # Find the time window to average
    Li = [ i for i, time in enumerate( ContactsTotData["Time"] ) if time * 1000 >= args.average_time ][0]
    Ls = [ i for i, time in enumerate( ContactsTotData["Time"] ) if time * 1000 <= args.last_time ][-1]

    Data[ "Contacts" ] = { value: ErrorACF( ContactsTotData[ value ][ Li:Ls ] ) 
                           for value in [ 'Peptide-Water', 'Peptide-Lipid HGs', 'Peptide-Lipid tails' ] }
    
## Tilt
    # Find the time window to average
    Li = [ i for i, time in enumerate( TiltData["Time"] ) if time * 1000 >= args.average_time ][0]
    Ls = [ i for i, time in enumerate( TiltData["Time"] ) if time * 1000 <= args.last_time ][-1]

    Data[ "Tilt" ] = ErrorACF( TiltData[ 'Tilt' ][ Li:Ls ] ) 

## PepDF
    Data[ "PepDF" ] = {
        "Angle": { value: ErrorACF( Angl[ value ] ) for value in Angl },
        "Dist":  { value: ErrorACF( Disp[ value ] ) for value in Disp }
        }
    
## Dipolar moments
    # Find the time window to average
    Li = [ i for i, time in enumerate( EDMData["Time"] ) if time * 1000 >= args.average_time ][0]
    Ls = [ i for i, time in enumerate( EDMData["Time"] ) if time * 1000 <= args.last_time ][-1]

    Data[ "EDM" ] = {
        "Long": ErrorACF( EDMData[ "Longitudinal component" ][ Li:Ls ] ),
        "Trans": ErrorACF( EDMData[ "Transversal component" ][ Li:Ls ] )
        }
    
    EDMTotal = np.sqrt( float(Data["EDM"]["Long"][0])**2+float(Data["EDM"]["Trans"][0])**2 )
    
    Data[ "EDM" ][ "Total" ] = SDX.RoundStdv( EDMTotal, 
            np.sqrt( ( float(Data["EDM"]["Long"][0]) * float(Data["EDM"]["Long"][1]) )**2
                   + ( float(Data["EDM"]["Trans"][0]) * float(Data["EDM"]["Trans"][1]) )**2 )/EDMTotal )
    
    # Find the time window to average
    Li = [ i for i, time in enumerate( HDMData["Time"] ) if time * 1000 >= args.average_time ][0]
    Ls = [ i for i, time in enumerate( HDMData["Time"] ) if time * 1000 <= args.last_time ][-1]

    Data[ "HDM" ] = {
        "Long": ErrorACF( HDMData[ "Longitudinal component" ][ Li:Ls ] ),
        "Trans": ErrorACF( HDMData[ "Transversal component" ][ Li:Ls ] )
        }
    
    HDMTotal = np.sqrt( float(Data["HDM"]["Long"][0])**2+float(Data["HDM"]["Trans"][0])**2 )
    
    Data[ "HDM" ][ "Total" ] = SDX.RoundStdv( HDMTotal, 
            np.sqrt( ( float(Data["HDM"]["Long"][0]) * float(Data["HDM"]["Long"][1]) )**2
                   + ( float(Data["HDM"]["Trans"][0]) * float(Data["HDM"]["Trans"][1]) )**2 )/HDMTotal )

## FILE
    # Data to store in the JSON file
    JSON = [ {
        "Area per lipid": [
        { "Membrane": [ { "value": Data["Area"]["Total"][0] }, { "std": Data["Area"]["Total"][1] }, { "unit": "nm<sup>2</sup>" } ,
        [ { "Upper Leaflet": [ { "value": Data["Area"]["Upper leaflet"][0] }, { "std": Data["Area"]["Upper leaflet"][1] }, { "unit": "nm<sup>2</sup>" } ] },
        { "Lower Leaflet": [ { "value": Data["Area"]["Lower leaflet"][0] }, { "std": Data["Area"]["Lower leaflet"][1] }, { "unit": "nm<sup>2</sup>" } ] } ] ] } ],
        "Average Z coordinate": [
        { "Peptide": [ {"value": Data["COG"]["Peptide"][0] }, { "std": Data["COG"]["Peptide"][1] }, { "unit": "nm" },
        [ { "First Residue": [ {"value": Data["COG"]["Peptide first BB"][0] }, { "std": Data["COG"]["Peptide first BB"][1] }, { "unit": "nm" } ] },
        { "Last Residue": [ {"value": Data["COG"]["Peptide last BB"][0] }, { "std": Data["COG"]["Peptide last BB"][1] }, { "unit": "nm" } ] } ] ] },
        { "Membrane": [ {"value": Data["COG"]["Lipids"][0] }, { "std": Data["COG"]["Lipids"][1] }, { "unit": "nm" },
        [ { "Upper Leaflet Head Groups": [ {"value": Data["COG"]["Upper lipid HGs"][0] }, { "std": Data["COG"]["Upper lipid HGs"][1] }, { "unit": "nm" } ] },
        { "Lower Leaflet Head Groups": [ {"value": Data["COG"]["Lower lipid HGs"][0] }, { "std": Data["COG"]["Lower lipid HGs"][1] }, { "unit": "nm" } ] } ] ] } ],
        "Bilayer thickness": [ {"value": Data["Bilayer thickness"][0] }, { "std": Data["Bilayer thickness"][1] }, { "unit": "nm" } ] ,
        "Peptide depth": [ {"value": Data["Peptide depth"][0] }, { "std": Data["Peptide depth"][1] }, { "unit": "nm" } ]  ,
        "Contacts": [
        { "Peptide - Water": [ {"value": Data["Contacts"]["Peptide-Water"][0] }, { "std": Data["Contacts"]["Peptide-Water"][1] }, { "unit": "" } ] },
        { "Peptide - Head groups": [ {"value": Data["Contacts"]["Peptide-Lipid HGs"][0] }, { "std": Data["Contacts"]["Peptide-Lipid HGs"][1] }, { "unit": "" } ] },
        { "Peptide - Tail groups": [ {"value": Data["Contacts"]["Peptide-Lipid tails"][0] }, { "std": Data["Contacts"]["Peptide-Lipid tails"][1] }, { "unit": "" } ] } ],
        "Tilt": [
         {"value": Data["Tilt"][0] }, { "std": Data["Tilt"][1] }, { "unit": "&deg" } ],
        "PepDF": [ { "{} ns".format(value): [ 
        { "Distance": [ {"value": Data[ "PepDF" ]["Dist"][value][0] }, {"std": Data[ "PepDF" ]["Dist"][value][1]}, {"unit": "nm"} ] }, 
        { "Angle":    [ {"value": Data[ "PepDF" ]["Angle"][value][0] }, {"std": Data[ "PepDF" ]["Angle"][value][1]} , {"unit": "&deg"} ] } ] for value in Angl }  ],
        "EDM": [
        { "Total": [ { "value": Data["EDM"]["Total"][0] }, { "std": Data["EDM"]["Total"][1] }, { "unit": "e nm" } ] },
        { "Longitudinal": [ { "value": Data["EDM"]["Long"][0] }, { "std": Data["EDM"]["Long"][1] }, { "unit": "e nm" } ] },
        { "Transversal": [ { "value": Data["EDM"]["Trans"][0] }, { "std": Data["EDM"]["Trans"][1] }, { "unit": "e nm" } ] } ],
        "HDM": [
        { "Total": [ { "value": Data["HDM"]["Total"][0] }, { "std": Data["HDM"]["Total"][1] }, { "unit": "nm" } ] },
        { "Longitudinal": [ { "value": Data["HDM"]["Long"][0] }, { "std": Data["HDM"]["Long"][1] }, { "unit": "nm" } ] },
        { "Transversal": [ { "value": Data["HDM"]["Trans"][0] }, { "std": Data["HDM"]["Trans"][1] }, { "unit": "nm" } ] } ] } ]
    
    # Write the file
    with open( args.out + '/averages.json', 'w+' ) as FILE:
        json.dump( JSON, FILE, indent = 4 )
    FILE.close()
    
    return


#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# EXECUTION
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

if __name__ == "__main__" :
    #print("He empezado!!!!")
    # Set the timer
    start_script_time=time.time()
    # Confirmar módulos cargados
    #_report_loaded_modules()

    # Location of the output folder with respect to the working directory
    args.out =  os.path.relpath( args.out, args.folder )
    
    # Change the working directory to the folder where the simulations file are located
    original_folder = os.getcwd()
    os.chdir( args.folder )
    
    if args.xtc.split('.')[-1] == 'xtc':
        fs_keyword = 'nstxtcout'#'nstxout-compressed'
    elif args.xtc.split('.')[-1] == 'trr':
        fs_keyword = 'nstxout'
    else:
        raise ValueError('Not a valid trajectory file! Only XTC and TRR can be used')

    # Read the MDP to find the timestep of the simulation and the frequency of storage
    # of data in the XTC file
    with open( args.mdp ) as MDP:
        for line in MDP:
            if re.split( '[;= ]+', line.replace(' ','').split(';')[0] )[0] == 'dt':
                dt = float( re.split( '[;= ]+', line.replace(' ','').split(';')[0] )[1] )
            elif re.split( '[;= ]+', line.replace(' ','').split(';')[0] )[0] == fs_keyword:
                fs = int( re.split( '[;= ]+', line.replace(' ','').split(';')[0] )[1] )
    
    it = int( args.initial_time / ( dt * fs ) )
    lt = int( args.last_time / ( dt * fs ) )
    at = int( args.average_time / ( dt * fs ) )
    
### Process trajectory
    # Load the structure and the trajectory
    u = MDAnalysis.Universe( args.tpr, args.xtc )
    
    # Add some bonds to the peptide
    # They are not the real bonds, but we don't need them, we just need that all
    # particles of the peptide are linked, so later the peptide can be reconstructed
    u.add_TopologyAttr( 'bonds', MDAnalysis.topology.guessers.guess_bonds(
             u.select_atoms( 'protein' ), u.select_atoms( 'protein' ).positions, 
             vdwradii={ name: 1000 for name in np.unique( u.select_atoms( 'protein' ).types ) } ) )
    
    # Reconstruct the peptide in the whole trajectory ( -pbc whole )
    #u.trajectory.add_transformations( *[ MDAnalysis.transformations.unwrap( u.select_atoms( 'protein' ) ) ] )
    u.trajectory.add_transformations(
        *[ CenterInBox( SDX.LipRB ),
           MDAnalysis.transformations.wrap( u.atoms ),
           MDAnalysis.transformations.unwrap( u.select_atoms( 'protein' ) ) ] )

    # Find the composition of the membrane
    LipSys = sorted( [ res for res in np.unique( u.select_atoms( 'name *' ).resnames ) if res in SDX.LIPIDS ] )
    HtmSys = sorted( [ res for res in np.unique( u.select_atoms( 'name *' ).resnames ) if res in SDX.HTMOLS ] )
    MemSys = LipSys + HtmSys
    
    # Water molecules
    Water = SDX.WATER[ args.forcefield ]
    
    # Referecne bead of the elements of the membrane
    MemRB = u.select_atoms( SDX.MemRB )
    
    # Selection of some important groups
    Peptides = u.select_atoms( 'protein' )
    Backbone = u.select_atoms( 'name BB'  )
    Membrane = u.select_atoms( SDX.Membr )
    Headgroup = u.select_atoms( SDX.MemHG )
    Tailgroup = u.select_atoms( SDX.MemTG )
    WaterMols = u.select_atoms( 'resname {}'.format( Water ) )
    
    # Dictionary for the results
    Results = { "area"     : {},
                "COG"      : {},
                "contacts_norm" : {},
                "contype_norm"  : {},
                "contres_norm"  : {},
                "contacts_tot" : {},
                "contype_tot"  : {},
                "contres_tot"  : {},            
                "density"  : { "water"   : [ 0 ] * args.bins,
                               "HG"      : [ 0 ] * args.bins,
                               "TG"      : [ 0 ] * args.bins,
                               "peptide" : [ 0 ] * args.bins },
                "densmap"  : { lipid : { "Lower" : np.array( [ [ 0, 0, 0 ] ] ),
                                         "Upper" : np.array( [ [ 0, 0, 0 ] ] ),
                              } for lipid in LipSys },
                "electrostatic moment": {},
                "hydrophobic moment"  : {},
                "mindist"  : {},
                "PepDF"    : { "COG"  : [],
                               "Vec"  : [],
                               "Time" : []},
                "spin"      : {},
                "tilt"     : {} }

### Perform the analysis
## First part of the trajectory, only some analysis are performed
    if args.all or args.analysis:
        for id_f, frame in zip( 
                ProgressBar( range(len(u.trajectory[it:at:args.skip_rough])) ,'First analysis: ', 20 ),  
                u.trajectory[it:at:args.skip_rough] ) :
            # Find the lipids belonging to each leaflet
            SplitLeaflets( frame )
            # Compute the principal vector of the backbone
            BackbonePrVec( frame )
            
            # Compute stuff
            AreaPerLipid( frame )
            COG( frame )
            Contacts( frame )
            DistMin( frame )
            ElectrostaticDipolarMoment( frame )
            HydrophobicDipolarMoment( frame )
            Tilt( frame )
            Spin( frame )
    
## Second part of the trajectory, all analysis are performed
        for id_f, frame in zip( 
                ProgressBar( range(len(u.trajectory[at:lt+1])) ,'Second analysis: ', 20 ),  
                u.trajectory[at:lt+1] ) :
# PepDF
            if id_f == 0:
                # Position of the peptide
                Results[ "PepDF" ][ "COG" ].append( np.append( Backbone.center_of_geometry()[:2], 0 ) )
                # Beads of the backbone
                BBPos = Backbone.positions[:,:]
                
                # Normalized principal vector of the peptide
                BackbonePrVec( frame )                
                Results[ "PepDF" ][ "Vec" ].append( np.append( PrVec[:2], 0 ) / np.linalg.norm( PrVec[:2] ) )

            else:
                PepDF( frame )
            
            if id_f % args.skip_rough == 0:
                # Find the lipids belonging to each leaflet
                SplitLeaflets( frame )
                # Compute the principal vector of the backbone
                BackbonePrVec( frame )
    
                # Compute some other stuff
                AreaPerLipid( frame )
                COG( frame )
                Contacts( frame )
                DistMin( frame )
                ElectrostaticDipolarMoment( frame )
                HydrophobicDipolarMoment( frame )
                Tilt( frame )
                Spin( frame )
                
            if id_f % args.skip_fine == 0:
                # Find the lipids belonging to each leaflet
                SplitLeaflets( frame ) 
                # Compute the principal vector of the backbone
                BackbonePrVec( frame )
                
                # Compute more stuff
                Density( frame )
                
                # Center the peptide in the box, but keeping the Z coodinate and put everything in the box
                frame = MDAnalysis.transformations.wrap( u.atoms )(
                            MDAnalysis.transformations.translate( np.append( frame.dimensions[:2]/2 , 0 ) - Results[ "PepDF" ][ "COG" ][-1] )( frame ) )
                
                # Compute the rest of stuff
                ContactsType( frame )
                ContactsResid( frame )
                DensMap( frame )
                
        with open( args.out + '/Results.pickle', 'wb' ) as OUT:
            pickle.dump( Results, OUT, protocol=pickle.HIGHEST_PROTOCOL )
                
    if args.all or args.plot: 
        
        with open( args.out + '/Results.pickle', 'rb' ) as INP:
            Results = pickle.load( INP )
        
        frame = u.trajectory[-1]
        
    ### Process the data and write the results
        try: 
            AreaData = pd.DataFrame( np.array( [ [ float(i)/1000 ] + Results["area"][i] for i in Results["area" ] if float(i)>=args.initial_time ] ),
                            columns = [ "Time", "Total", "Upper leaflet", "Lower leaflet" ] )
            AreaData.to_csv( args.out + '/area_per_lipid.csv')
        except: AreaData = pd.read_csv( args.out + '/area_per_lipid.csv', index_col=0 )
        
        try: 
            COGData = pd.DataFrame( np.array( [ [ float(i)/1000 ] + Results["COG"][i] for i in Results["COG" ] if float(i)>=args.initial_time ] ),
                           columns = [ 'Time', 'Peptide', 'Lipids', 'Peptide first BB', 'Peptide last BB', 
                                      'Upper lipid HGs', 'Lower lipid HGs' ]  )
            COGData.to_csv( args.out + '/center_of_geometry.csv')
        except: COGData = pd.read_csv( args.out + '/center_of_geometry.csv', index_col=0 )
        
        try: 
            ContactsTotData = pd.DataFrame( np.array( [ [ float(i)/1000 ] + Results["contacts_tot"][i] for i in Results["contacts_tot" ] if float(i)>=args.initial_time ] ),
                            columns = [ 'Time', 'Peptide-Water' , 'Peptide-Lipid HGs', 'Peptide-Lipid tails' ] )
            ContactsTotData.to_csv( args.out + '/contacts_tot.csv')
        except: ContactsTotData = pd.read_csv( args.out + '/contacts_tot.csv', index_col=0 )
    
        try: 
            ContactsTotTypeData = pd.DataFrame ( np.array( [ [ np.mean( [ Results["contype_tot"][ t ][ lipid ][ amino ] for t in Results["contype_tot"] ] ) 
                                                    for lipid in MemSys ] for amino in SDX.AMINO ] ),
                                      index = [ SDX.AMINO[ amino ][ "label" ] for amino in SDX.AMINO ], 
                                      columns = MemSys )
            
            ContactsTotTypeData.to_csv( args.out + '/number_of_contacts_tot.csv')
            
            ContactsTotTypeData = pd.concat( [ ContactsTotTypeData.iloc[:2],   pd.DataFrame( { lipid: 0 for lipid in MemSys }, index = [''] ), 
                                        ContactsTotTypeData.iloc[2:5],  pd.DataFrame( { lipid: 0 for lipid in MemSys }, index = [''] ), 
                                        ContactsTotTypeData.iloc[5:14], pd.DataFrame( { lipid: 0 for lipid in MemSys }, index = [''] ), 
                                        ContactsTotTypeData.iloc[14:] ] )
        except: ContactsTotTypeData = pd.read_csv( args.out + '/number_of_contacts_tot.csv', index_col=0 )
    
        try:
            ContactsTotResidData = pd.DataFrame( np.array( [ [ np.mean( [ np.sum( [ Results["contres_tot"][t][lipid][(atom.resname,i)] 
                                                for lipid in MemSys ] ) for t in Results["contres_tot"] ] ) for i, atom in enumerate(Backbone)] ] ),
                                        columns = [ (atom.resname,i) for i, atom in enumerate(Backbone) ]  )
            ContactsTotResidData.to_csv( args.out + '/contacts_peptide_tot.csv')
        except: ContactsResidData = pd.read_csv( args.out + '/contacts_peptide_tot.csv', index_col=0 )
        
        try: 
            ContactsNormData = pd.DataFrame( np.array( [ [ float(i)/1000 ] + Results["contacts_norm"][i] for i in Results["contacts_norm" ] if float(i)>=args.initial_time ] ),
                            columns = [ 'Time', 'Peptide-Water' , 'Peptide-Lipid HGs', 'Peptide-Lipid tails' ] )
            ContactsNormData.to_csv( args.out + '/contacts.csv')
        except: ContactsNormData = pd.read_csv( args.out + '/contacts.csv', index_col=0 )
    
        try: 
            ContactsNormTypeData = pd.DataFrame ( np.array( [ [ np.mean( [ Results["contype_norm"][ t ][ lipid ][ amino ] for t in Results["contype_norm"] ] ) 
                                                    for lipid in MemSys ] for amino in SDX.AMINO ] ),
                                      index = [ SDX.AMINO[ amino ][ "label" ] for amino in SDX.AMINO ], 
                                      columns = MemSys )
            
            ContactsNormTypeData.to_csv( args.out + '/number_of_contacts_norm.csv')
            
            ContactsNormTypeData = pd.concat( [ ContactsNormTypeData.iloc[:2],   pd.DataFrame( { lipid: 0 for lipid in MemSys }, index = [''] ), 
                                        ContactsNormTypeData.iloc[2:5],  pd.DataFrame( { lipid: 0 for lipid in MemSys }, index = [''] ), 
                                        ContactsNormTypeData.iloc[5:14], pd.DataFrame( { lipid: 0 for lipid in MemSys }, index = [''] ), 
                                        ContactsNormTypeData.iloc[14:] ] )
        except: ContactsNormTypeData = pd.read_csv( args.out + '/number_of_contacts_norm.csv', index_col=0 )
    
        try:
            ContactsNormResidData = pd.DataFrame( np.array( [ [ np.mean( [ np.sum( [ Results["contres_norm"][t][lipid][(atom.resname,i)] 
                                                for lipid in MemSys ] ) for t in Results["contres_norm"] ] ) for i, atom in enumerate(Backbone)] ] ),
                                        columns = [ (atom.resname,i) for i, atom in enumerate(Backbone) ]  )
            ContactsNormResidData.to_csv( args.out + '/contacts_peptide_norm.csv')
        except: ContactsNormResidData = pd.read_csv( args.out + '/contacts_peptide_norm.csv', index_col=0 )
        
        try: 
            DistData = pd.DataFrame( np.array( [ [ float(i)/1000 ] + Results["mindist"][i] for i in Results["mindist" ] if float(i)>=args.initial_time ] ),
                            columns = [ 'Time', 'Peptide BB-Lipid HGs', 'Peptide BB-Lipid tails' ] )
            DistData.to_csv( args.out + '/mindist.csv' )
        except: DistData = pd.read_csv( args.out + '/mindist.csv',index_col=0 )
        
        try:
            EDMData = pd.DataFrame( np.array( [ [ float(i)/1000 ] + Results["electrostatic moment"][i][1:] for i in Results["electrostatic moment"] if float(i)>=args.initial_time ] ),
                            columns = [ 'Time', 'Longitudinal component', 'Transversal component' ] )
            EDMData.to_csv( args.out + '/electrostatic_moment.csv' )
        except: EDMData = pd.read_csv( args.out + '/electrostatic_moment.csv',index_col=0 )
        
        try:
            HDMData = pd.DataFrame( np.array( [ [ float(i)/1000 ] + Results["hydrophobic moment"][i][1:] for i in Results["hydrophobic moment"] if float(i)>=args.initial_time ] ),
                            columns = [ 'Time', 'Longitudinal component', 'Transversal component' ] )
            HDMData.to_csv( args.out + '/hydrophobic_moment.csv' )
        except: HDMData = pd.read_csv( args.out + '/hydrophobic_moment.csv',index_col=0 )
    
        try: 
            SpinData = pd.DataFrame ( np.array( [ [ float(i)/1000 ] + [ Results["spin"][i] ] for i in Results["spin" ] if float(i)>=args.initial_time ] ),
                             columns = [ "Time", "Spin"])
            SpinData['Spin'] = SpinData['Spin'].apply(lambda x: x - 180 if x > 150 else x + 180)
            SpinData.to_csv( args.out + '/spin_o.csv')
        except: SpinData = pd.read_csv( args.out + '/spin.csv', index_col=0 )
        
        try: 
            TiltData = pd.DataFrame ( np.array( [ [ float(i)/1000 ] + [  Results["tilt"][i] ] for i in Results["tilt" ] if float(i)>=args.initial_time ] ),
                             columns = [ "Time", "Tilt"])
            TiltData.to_csv( args.out + '/tilt.csv')
        except: TiltData = pd.read_csv( args.out + '/tilt.csv', index_col=0 )
        
        try:
            DensityData = pd.DataFrame( np.array( [ [ i * frame.dimensions[2] / ( 10 * args.bins ) ] +
                                         [ Results["density"][res][i] * ( args.bins ) / ( 6.022 * frame.volume * 1e-4 * len( u.trajectory[at:lt:args.skip_fine] ) ) for res in Results["density"] ] for i in range( args.bins ) ] ),
                               columns = [ "Position", "Water", "Headgroups", "Tails", "Peptide" ]  )
            DensityData.to_csv( args.out + '/density.csv')
        except: DensityData = pd.read_csv( args.out + '/density.csv', index_col=0)            
    


        
### Plot the results
        
# Area per lipid
        # PlotLineal( Name = 'area_per_lipid', 
        #             Data = AreaData , 
        #             Title = 'Area per lipid', 
        #             Legend = AreaData.columns.tolist()[1:], 
        #             #Colors = [ "#cb4380", "#ffa600", "#003b6f" ], 
        #             Colors = ["#4477AA","#228833","#AA3377"],
        #             XLabel = 'Time (ns)', 
        #             YLabel = r'Area per lipid (nm$^{2}$)', 
        #             XLims = [ args.initial_time/1000, math.ceil( AreaData['Time'].iloc[-1] / 1000 ) * 1000 + 1 ],
        #             XTick = 1000,
        #             Correction = True if (AreaData['Upper leaflet'] == AreaData['Lower leaflet']).all() else False ) 
        PlotHisto(Name = 'area_per_lipid', 
                    Data = AreaData , 
                    Title = 'Area per lipid', 
                    Legend = AreaData.columns.tolist()[1:], 
                    Colors = ["#4477AA","#228833","#AA3377"], 
                    XLabel = 'Time (ns)', 
                    YLabel1 = r'Area per lipid (nm$^{2}$)', 
                    YLabel2 = r'Counts',
                    XLims = [ args.initial_time/1000, math.ceil( AreaData['Time'].iloc[-1] / 1000 ) * 1000 + 1 ],
                    XTick = 1000,
                    Correction = True if (AreaData['Upper leaflet'] == AreaData['Lower leaflet']).all() else False,
                    Instantaneous = False if (AreaData['Upper leaflet'] == AreaData['Lower leaflet']).all() else True)


# COG
        def JumpFunc( List ):
            Ref = COGData["Lipids"]
            return [0] + [ j for j in range( 1, len( List ) ) if ( List[j] - Ref[j] ) * ( List[j-1] - Ref[j-1] ) < 0 ] + [ len( List ) ]
    
        PlotLineal( Name = 'center_of_geometry', 
                    Data = COGData, 
                    Title = 'Z coordinate', 
                    Legend = COGData.columns.tolist()[1:], 
                    #Colors = [ "#003b6f", "#614389", '#ab4289' , '#e54a71' , "#ff7048", "#ffa600" ], 
                    Colors = ['#AA3377', '#EE6677', '#CCBB44', '#228833', '#66CCEE', '#4477AA'],
                    XLabel = 'Time (ns)', 
                    YLabel = r'Z coordinate (nm)', 
                    XLims = [ args.initial_time/1000, math.ceil( COGData['Time'].iloc[-1] / 1000 ) * 1000 + 1 ],
                    XTick = 1000,
                    Jump = JumpFunc ) 
# Contacts
        PlotLineal( Name = 'contacts_tot', 
                    Data = ContactsTotData, 
                    Title = 'Total number of contacts', 
                    Legend = ContactsTotData.columns.tolist()[1:], 
                    #Colors = [ "#003b6f", "#cb4380", "#ffa600" ], 
                    Colors = ["#4477AA","#228833","#AA3377"],
                    XLabel = 'Time (ns)', 
                    YLabel = r'# Contacts',
                    XLims = [ args.initial_time/1000, math.ceil( ContactsTotData['Time'].iloc[-1] / 1000 ) * 1000 + 1 ],
                    XTick = 1000 )
        PlotLineal( Name = 'contacts_norm', 
                    Data = ContactsNormData, 
                    Title = 'Number of contacts per bead', 
                    Legend = ContactsNormData.columns.tolist()[1:], 
                    #Colors = [ "#003b6f", "#cb4380", "#ffa600" ],
                    Colors = ["#4477AA","#228833","#AA3377"],
                    XLabel = 'Time (ns)', 
                    YLabel = r'# Contacts',
                    XLims = [ args.initial_time/1000, math.ceil( ContactsNormData['Time'].iloc[-1] / 1000 ) * 1000 + 1 ],
                    XTick = 1000 ) 
# Distance
        PlotLineal( Name = 'mindist', 
                    Data = DistData, 
                    Title = 'Minimum distance', 
                    Legend = DistData.columns.tolist()[1:], 
                    Colors = ["#4477AA","#AA3377"],
                    #Colors = [ "#cb4380", "#ffa600" ], 
                    XLabel = 'Time (ns)', 
                    YLabel = r'Minimum distance (nm)',
                    XLims = [ args.initial_time/1000, math.ceil( DistData['Time'].iloc[-1] / 1000 ) * 1000 + 1 ],
                    YLims = [0.40, 6.1], #0.450,0.491
                    XTick = 1000,
                    YTick = 0.01, 
                    Rolling = 100) #10 Rolling modificado, antes esta opcion estaba borrada, quitar si no funciona 
# Electrostatic dipolar moment
        # PlotTwin( Name = 'electrostatic_dipolar_moment',
        #             Data = EDMData,
        #             Title = 'Electrostatic Dipolar Moment',
        #             Legend = EDMData.columns.tolist()[1:],
        #             #Colors = [ "#cb4380", "#003b6f" ],
        #             Colors = ["#4477AA","#AA3377"],
        #             XLabel = 'Time (ns)',
        #             YLabel = r'EDM components (e nm)',
        #             XLims = [ args.initial_time/1000, math.ceil( EDMData['Time'].iloc[-1] / 1000 ) * 1000 + 1 ],
        #             XTick = 1000)
        
        # PlotHisto( Name = 'electrostatic_dipolar_moment',
        #             Data = EDMData,
        #             Title = 'Electrostatic Dipolar Moment',
        #             Legend = EDMData.columns.tolist()[1:],
        #             Colors = ["#4477AA","#AA3377"],
        #             XLabel = 'Time (ns)',
        #             YLabel1 = r'EDM components (e nm)',
        #             YLabel2 = r'Counts',
        #             XLims = [ args.initial_time/1000, math.ceil( EDMData['Time'].iloc[-1] / 1000 ) * 1000 + 1 ],
        #             XTick = 1000,
        #             Instantaneous = True )

        PlotTwin( Name = 'electrostatic_dipolar_moment', 
                  Data = EDMData, 
                  Title = 'Electrostatic Dipolar Moment', 
                  Legend = EDMData.columns.tolist()[1:],
                  Colors = ["#4477AA","#AA3377"], 
                  XLabel1 = 'Time (ns)',
                  XLabel2 = 'Counts', 
                  YLabel = 'EDM components (e nm)',
                  XLims1 = [ args.initial_time/1000, math.ceil( EDMData['Time'].iloc[-1] / 1000 ) * 1000 + 1 ],
                  YLims = [ (np.floor( np.min( EDMData[Col] ) ), np.ceil( np.max( EDMData[Col] ) )+0.001 ) 
                           for Col in EDMData.columns.tolist()[1:] ],
                  YTick = [ 1, 1 ],
                  XTick1 = 1000,
                  Instantaneous = True )
        
# Hydrophobic dipolar moment
        # PlotTwin( Name = 'hydrophobic_dipolar_moment',
        #             Data = HDMData,
        #             Title = 'Hydrophobic Dipolar Moment',
        #             Legend = HDMData.columns.tolist()[1:],
        #             #Colors = [ "#cb4380", "#003b6f" ],
        #             Colors = ["#4477AA","#AA3377"],
        #             XLabel = 'Time (ns)',
        #             YLabel = r'HDM components (nm)',
        #             XLims = [ args.initial_time/1000, math.ceil( HDMData['Time'].iloc[-1] / 1000 ) * 1000 + 1 ],
        #             XTick = 1000 )
        
        # PlotHisto( Name = 'hydrophobic_dipolar_moment',
        #             Data = HDMData,
        #             Title = 'Hydrophobic Dipolar Moment',
        #             Legend = HDMData.columns.tolist()[1:],
        #             Colors = ["#4477AA","#AA3377"],
        #             XLabel = 'Time (ns)',
        #             YLabel1 = r'HDM components (nm)',
        #             YLabel2 = r'Counts',
        #             XLims = [ args.initial_time/1000, math.ceil( HDMData['Time'].iloc[-1] / 1000 ) * 1000 + 1 ],
        #             XTick = 1000,
        #             Instantaneous = True )
        
        PlotTwin( Name = 'hydrophobic_dipolar_moment', 
                  Data = HDMData, 
                  Title = 'Hydrophobic Dipolar Moment', 
                  Legend = HDMData.columns.tolist()[1:],
                  Colors = ["#4477AA","#AA3377"], 
                  XLabel1 = 'Time (ns)',
                  XLabel2 = 'Counts', 
                  YLabel = 'HDM components (nm)',
                  XLims1 = [ args.initial_time/1000, math.ceil( HDMData['Time'].iloc[-1] / 1000 ) * 1000 + 1 ],
                  YLims = [ (np.floor( np.min( HDMData[Col] ) ), np.ceil( np.max( HDMData[Col] ) )+0.001 ) 
                           for Col in HDMData.columns.tolist()[1:] ],
                  YTick = [ 1, 1 ],
                  XTick1 = 1000,
                  Instantaneous = True )
        
# Tilt
        def JumpFunc( List ):
            return [0] + [ j for j in range( 1, len( List ) ) if np.abs( List[j] - List[j-1] ) > 180 ] + [ len( List ) ]
        
        PlotHisto( Name="tilt", 
                   Data=TiltData, 
                   Title="Tilt", 
                   Legend=['Tilt'], 
                   #Colors=['#003b6f'], 
                   Colors = ["#4477AA"],
                   XLabel='Time (ns)',
                   YLabel1='Angle (degrees)',
                   YLabel2='Counts',
                   XLims=[ args.initial_time/1000, math.ceil( TiltData['Time'].iloc[-1] / 1000 ) * 1000 + 1  ],
                   XTick=1000,
                   Jump = JumpFunc,
                   Instantaneous=True )
        
# Spin
        def JumpFunc( List ):
            return [0] + [ j for j in range( 1, len( List ) ) if np.abs( List[j] - List[j-1] ) > 180 ] + [ len( List ) ]
    
        PlotHisto( Name="spin", 
                   Data=SpinData, 
                   Title="Peptide spin", 
                   Legend=['Spin'], 
                   #Colors=['#003b6f'], 
                   Colors = ["#4477AA"],
                   XLabel='Time (ns)',
                   YLabel1='Angle (degrees)',
                   YLabel2='Counts',
                   XLims=[ args.initial_time/1000, math.ceil( SpinData['Time'].iloc[-1] / 1000 ) * 1000 + 1  ],
                   XTick=1000,
                   Jump = JumpFunc,
                   Instantaneous=True )
# Density
        PlotLineal( Name = 'density', 
                    Data = DensityData, 
                    Title = 'Lateral density', 
                    Legend = DensityData.columns.tolist()[1:], 
                    #Colors = [ "#003b6f", "#94438c", "#f35464", "#ffa600" ],
                    Colors = ["#4477AA","#228833","#CCBB44","#AA3377"],
                    XLabel = 'Position (nm)', 
                    YLabel = 'Lateral density (kg m$^{-3}$)', 
                    XLims = [0, DensityData.iloc[-1,0]],
                    XTick = 1,
                    Rolling = False ) 
# Contacts by type
        PlotBar(  Name = 'number_of_contacts_tot', 
                  Data = ContactsTotTypeData, 
                  Title = 'Average number of total contacts per residue type',  
                  Colors =  [ SDX.MEMBCOMP[ lipid ][ 'color' ] for lipid in MemSys ] 
                      if len(MemSys) > 1 else 2*[ SDX.MEMBCOMP[ lipid ][ 'color' ] 
                      for lipid in MemSys ],
                  YLabel = '# Contacts' )
        PlotBar(  Name = 'number_of_contacts_norm', 
                  Data = ContactsNormTypeData, 
                  Title = 'Average number of total contacts per residue type per bead',  
                  Colors =  [ SDX.MEMBCOMP[ lipid ][ 'color' ] for lipid in MemSys ] 
                      if len(MemSys) > 1 else 2*[ SDX.MEMBCOMP[ lipid ][ 'color' ] 
                      for lipid in MemSys ],
                  YLabel = '# Contacts / # Beads' )
# Contacts by residue
        PeptideContactsPDB( Data = ContactsTotData,
                            Name = 'peptide_contacts_tot' )
        PeptideContactsPDB( Data = ContactsNormData,
                            Name = 'peptide_contacts_norm' )
# Densmap
        PlotDensmap()
# PepDF
        ProcessPepDF()
           
        # Print the averages in a JSON file
        ReturnJSON()
    
### Terminate
    os.chdir( original_folder )
    
    final_time = time.time() - start_script_time
    print("--- TOTAL TIME: {} ---".format( 
        ''.join(['{0:.0f} hours '.format(final_time//3600) 
                     if final_time>=3600 else '', 
                 '{0:.0f} minutes '.format(final_time//60-60*(final_time//3600)) 
                     if final_time>=60 else '' , 
                 '{0:.0f} seconds'.format(final_time-60*(final_time//60))]) ) )

'''
def PlotHisto( Name: str, Data: np.ndarray, Title: str, Legend: list, Colors: list, 
              XLabel: str = None, YLabel1: str = None, YLabel2: str = None,
              XLims: list = None, XTick: float = None,
              YLims1: list = None, YTick1: float = None, 
              YLims2: list = None, YTick2: float = None,
              Correction: bool = False, Rolling: int = 1,
              Instantaneous: bool = False, Jump: Callable = None):
    
    with plt.rc_context({"hatch.linewidth":16/3}):
        fig, ax = plt.subplots( ncols=2, sharey=True, gridspec_kw={'width_ratios': [5, 1]} )
        plt.subplots_adjust(wspace=0.075, hspace=0) # Reduces the space between subplots
    
        ax[0].set_title( Title )
        
        if not Correction:
            for i in range( len( Legend ) ):
                # Plot the instantaneous data as light circles
                if Instantaneous:
                    ax[0].plot( Data.iloc[:,0] , Data.iloc[:,i+1], 'wo', mec=Colors[i], alpha=0.5, zorder = 0 )
                # Plot the rolling mean as a solid line
                if Jump:
                    Jumps = JumpFunc( Data.iloc[:,i+1] )
                    for j in range( len( Jumps ) - 1 ):
                        ax[0].plot( Data.iloc[ Jumps[j]:Jumps[j+1], 0 ], 
                                  Data.iloc[ Jumps[j]:Jumps[j+1], i+1 ].rolling( 10, min_periods = 1 ).mean().tolist(), 
                                 '-', linewidth = 3 if Correction else 3, color = Colors[i], zorder = len( Legend ) - i )
                else:
                    ax[0].plot( Data.iloc[:,0] , Data.iloc[:,i+1].rolling( 10, min_periods = 1 ).mean().tolist(), 
                               '-', linewidth = 1 + 2*i**1.5 if Correction else 3, color=Colors[i], zorder = len( Legend ) - i )
        
                print("NO")
                N, bins, _ = ax[1].hist( Data.iloc[:,i+1], bins=int( np.sqrt( len( Data.iloc[:,i+1] ) ) ), color=Colors[i], orientation="horizontal", ec='k', zorder = len( Legend ) - i, alpha=0.5 )
            
                ax[0].plot( XLims[0]-42 , Data.iloc[:1,i+1] , linewidth = 4 , color = Colors[i] , alpha = 1, label = Legend[i] )
            
        if Correction:
            i=0
            ax[0].plot( Data.iloc[:,0] , Data.iloc[:,i+1], 'wo', mec=Colors[i], alpha=0.5, zorder = 0 )
            if Jump:
                Jumps = JumpFunc( Data.iloc[:,i+1] )
                for j in range( len( Jumps ) - 1 ):
                    ax[0].plot( Data.iloc[ Jumps[j]:Jumps[j+1], 0 ], 
                              Data.iloc[ Jumps[j]:Jumps[j+1], i+1 ].rolling( 10, min_periods = 1 ).mean().tolist(), 
                             '-', linewidth = 3, color = Colors[i], zorder = len( Legend ) - i )
            else:
                ax[0].plot( Data.iloc[:,0] , Data.iloc[:,i+1].rolling( 10, min_periods = 1 ).mean().tolist(), 
                           '-', linewidth = 3, color=Colors[i], zorder = len( Legend ) - i )
            N, bins, _ = ax[1].hist( Data.iloc[:,i+1], bins=int( np.sqrt( len( Data.iloc[:,i+1] ) ) ), color=Colors[i], edgecolor='k', orientation="horizontal" )
            
            for i in range( len( Legend ) ):
                ax[0].plot( XLims[0]-42 , Data.iloc[:1,i+1] , linewidth = 4 , color = Colors[i] , alpha = 1, label = Legend[i] )
            
            ax[0].annotate('NOTE: In this system, both leaflets have the same number of lipids,\n thus the values for their APL are overlapped in the plots',
                           xy=(0.01, 0),xycoords='axes fraction', fontsize=12, horizontalalignment='left', verticalalignment='bottom')
            
        # Legend
        if len( Legend ) > 1:
            ax[0].legend(loc='upper right')
            
        # First Y-axis properties
        ax[0].set_ylabel( YLabel1 )
        if YLims1:
            ax[0].set_ylim( YLims1[0], YLims1[1] )
            ax[0].set_yticks( np.arange( YLims1[0], YLims1[1], YTick1 ) )
        
        # First X-axis properties (it will be common to both plots)
        ax[0].set_xlabel( XLabel )
        if XLims:
            ax[0].set_xlim( XLims[0], XLims[1] )
            ax[0].set_xticks( np.arange( XLims[0], XLims[1], XTick ) )
            
        # Second Y-axis properties
        ax[1].set_xlabel( YLabel2 )
        if YLims2:
            ax[1].set_ylim( YLims2[0], YLims2[1] )
            ax[1].set_yticks( np.arange( YLims2[0], YLims2[1], YTick2 ) )
    
        print(ax[0].get_ylim()[0])

    
        # Figure properties
        fig.set_size_inches(11, 6)
        plt.tight_layout()
        plt.savefig( args.out + '/' + Name + '.png', dpi=300 )
    return




PlotHisto(Name = 'area_per_lipid_hist', 
            Data = AreaData , 
            Title = 'Area per lipid', 
            Legend = AreaData.columns.tolist()[1:], 
            Colors = [ "#cb4380", "#ffa600", "#003b6f" ], 
            XLabel = 'Time (ns)', 
            YLabel1 = r'Area per lipid (nm$^{2}$)', 
            YLabel2 = r'Counts',
            XLims = [ args.initial_time/1000, math.ceil( AreaData['Time'].iloc[-1] / 1000 ) * 1000 + 1 ],
            XTick = 1000,
            Correction = True if (AreaData['Upper leaflet'] == AreaData['Lower leaflet']).all() else False )

'''
