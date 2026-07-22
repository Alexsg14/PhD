#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 24 12:25:07 2022

@author: fabs
"""

import numpy as np
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# SuPepDex - Definitions and information for the SuPepMemb Analysis
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

### LIPIDS

# Definitions

LIPIDS = {
    "POPA": {
        "RB": "PO4",
        "HG": [ "PO4", "GL1", "GL2" ],
        "T1": [ "C1A", "D2A", "C3A", "C4A" ],
        "T2": [ "C1B", "C2B", "C3B", "C4B" ],
        "color" : '#daa520'
        },
    "POPC": {
        "RB": "PO4",
        "HG": [ "NC3", "PO4", "GL1", "GL2" ],
        "T1": [ "C1A", "D2A", "C3A", "C4A" ],
        "T2": [ "C1B", "C2B", "C3B", "C4B" ],
        "color" : '#055B4E'
        },
    "POPE": {
        "RB": "PO4",
        "HG": [ "NH3", "PO4", "GL1", "GL2" ],
        "T1": [ "C1A", "D2A", "C3A", "C4A" ],
        "T2": [ "C1B", "C2B", "C3B", "C4B" ],
        "color" : '#FF00FF' 
        },
    "POPS": {
        "RB": "PO4",
        "HG": [ "CNO", "PO4", "GL1", "GL2" ],
        "T1": [ "C1A", "D2A", "C3A", "C4A" ],
        "T2": [ "C1B", "C2B", "C3B", "C4B" ],
        "color" : '#663399' 
        },
    "POPG": {
        "RB": "PO4",
        "HG": [ "GL0", "PO4", "GL1", "GL2" ],
        "T1": [ "C1A", "D2A", "C3A", "C4A" ],
        "T2": [ "C1B", "C2B", "C3B", "C4B" ],
        "color" : '#FF3300'
        },
    "POPI": {
        "RB": "PO4",
        "HG": ["C1", "C2", "C3", "PO4", "GL1", "GL2"], #Alex
        "T1": [ "C1A", "D2A", "C3A", "C4A" ],
        "T2": [ "C1B", "C2B", "C3B", "C4B" ],
        "color" : '#3D85C6'
        },
    "TBPI": {
        "RB": "PO4",
        "HG": ["C1", "C2", "C3", "PO4", "GL1", "GL2"], #Alex
        "T1": [ "C1A", "D2A", "C3A", "C4A" ],
        "T2": [ "C1B", "C2B", "C3B", "C4B" ],
        "color" : '#3D85C6'
        },
    "CDL2": {
        "RB": "PO41",
        "HG": ["GL0", "PO41", "PO42", "GL11", "GL12", "GL21", "GL22"], #Alex
        "color": '#741B47'
        },
    "CARD": {
        "RB": "PO41",
        "HG": ["GL0", "PO41", "PO42", "GL11", "GL12", "GL21", "GL22"], #Alex
        "color": '#741B47'
        },
    "DOPC": {
        "RB": "PO4",
        "HG": [ "NC3", "PO4", "GL1", "GL2" ],
        "T1": [ "C1A", "D2A", "C3A", "C4A" ],
        "T2": [ "C1B", "D2B", "C3B", "C4B" ],
        "color" : '#C82842'
        },
    "DOPE": {
        "RB": "PO4",
        "HG": [ "NH3", "PO4", "GL1", "GL2" ],
        "T1": [ "C1A", "D2A", "C3A", "C4A" ],
        "T2": [ "C1B", "D2B", "C3B", "C4B" ],
        "color" : '#F08041'  
        },
    "DOPS": {
        "RB": "PO4",
        "HG": [ "CNO", "PO4", "GL1", "GL2" ],
        "T1": [ "C1A", "D2A", "C3A", "C4A" ],
        "T2": [ "C1B", "D2B", "C3B", "C4B" ],
        "color" : '#FEC544'  
        },
    "DPSM": {
        "RB": "PO4",
        "HG": [ "NC3", "PO4", "AM1", "AM2" ],
        "T1": [ "T1A", "C2A", "C3A", "C4A" ],
        "T2": [ "C1B", "C2B", "C3B", "C4B" ],
        "color" : '#6BAC2E' 
        },
    "DLPC": {
        "RB": "PO4",
        "HG": [ "NHC", "PO4", "GL1", "GL2" ],
        "T1": [ "C1A", "C2A", "C3A" ],
        "T2": [ "C1B", "C2B", "C3B" ],
        "color" : '#000000'  # NOT DEFINED
        },
    "DLPG": {
        "RB": "PO4",
        "HG": [ "GL0", "PO4", "GL1", "GL2" ],
        "T1": [ "C1A", "C2A", "C3A" ],
        "T2": [ "C1B", "C2B", "C3B" ],
        "color" : '#000000'  # NOT DEFINED
        }
    }

HTMOLS = {
    "CHOL": {
        "RB": "ROH",
        "HG": [ "ROH" ],
        "color": '#FFFF00'
        }
    }

MEMBCOMP = { **LIPIDS , **HTMOLS }

## Querys

# Lipids in the system
Lipid = 'resname ' + ' or resname '.join( LIPIDS )
# Heteromolecules in the system
HtMol = 'resname ' + ' or resname '.join( HTMOLS )
# Membrane in the system
Membr = Lipid + ' or ' + HtMol

# Headgroups of the lipids in the system
LipHG = ' or '.join([' ( resname ' + i + '  and ( name ' + ' or name '.join( LIPIDS[ i ][ "HG" ] ) + ') )' for i in LIPIDS ] )
# Headgroups of the heteromolecules in the system
HtmHG = ' or '.join([' ( resname ' + i + '  and ( name ' + ' or name '.join( HTMOLS[ i ][ "HG" ] ) + ') )' for i in HTMOLS ] )
# Headgroups of the membrane in the system
MemHG = LipHG + ' or ' + HtmHG

# Tails of the lipids in the system
LipTG = ' or '.join([' ( resname ' + i + '  and not ( name ' + ' or name '.join( LIPIDS[ i ][ "HG" ] ) + ') )' for i in LIPIDS ] )
# Tails of the heteromolecules in the system
HtmTG = ' or '.join([' ( resname ' + i + '  and not ( name ' + ' or name '.join( HTMOLS[ i ][ "HG" ] ) + ') )' for i in HTMOLS ] )
# Tailgroups of the membrane in the system
MemTG = LipTG + ' or ' + HtmTG

# Reference beads of the lipids in the system
LipRB = ' or '.join([' ( resname ' + i + '  and name ' + LIPIDS[ i ][ "RB" ] + ' ) ' for i in LIPIDS ] )
# Reference beads of the heteromolecules in the system
HtmRB = ' or '.join([' ( resname ' + i + '  and name ' + HTMOLS[ i ][ "RB" ] + ' ) ' for i in HTMOLS ] )
# Reference beads of the membrane in the system
MemRB = LipRB + ' or ' + HtmRB


### AMINO ACIDS


AMINO = {
      'ASP': {
          'label':'D',
          'hydrophobicity': -0.77,
          'behavior': 'acidic'
          },
      'GLU': {
          'label':'E',
          'hydrophobicity': -0.64,
          'behavior': 'acidic'
          },
      'LYS': {
          'label':'K',
          'hydrophobicity': -0.99,
          'behavior': 'basic'
          },
      'ARG': {
          'label':'R',
          'hydrophobicity': -1.01,
          'behavior': 'basic'
          },
      'HIS': {
          'label':'H',
          'hydrophobicity': 0.13,
          'behavior': 'basic'
          },
      'GLY': {
          'label':'G',
          'hydrophobicity': 0,
          'behavior': 'hydrophobic'
          },
      'ALA': {
          'label':'A',
          'hydrophobicity': 0.31,
          'behavior': 'hydrophobic'
          },
      'VAL': {
          'label':'V',
          'hydrophobicity': 1.22,
          'behavior': 'hydrophobic'
          },
      'LEU': {
          'label':'L',
          'hydrophobicity': 1.70,
          'behavior': 'hydrophobic'
          },
      'ILE': {
          'label':'I',
          'hydrophobicity': 1.80,
          'behavior': 'hydrophobic'
          },
      'PRO': {
          'label':'P',
          'hydrophobicity': 0.72,
          'behavior': 'hydrophobic'
          },
      'PHE': {
          'label':'F',
          'hydrophobicity': 1.79,
          'behavior': 'hydrophobic'
          },
      'MET': {
          'label':'M',
          'hydrophobicity': 1.23,
          'behavior': 'hydrophobic'
          },
      'TRP': {
          'label':'W',
          'hydrophobicity': 2.25,
          'behavior': 'hydrophobic'
          },
      'SER': {
          'label':'S',
          'hydrophobicity': -0.04,
          'behavior': 'polar'
          },
      'THR': {
          'label':'T',
          'hydrophobicity': 0.26,
          'behavior': 'polar'
          },
      'CYS': {
          'label':'C',
          'hydrophobicity': 1.54,
          'behavior': 'polar'
          },
      'TYR': {
          'label':'Y',
          'hydrophobicity': 0.96,
          'behavior': 'polar'
          },
      'ASN': {
          'label':'N',
          'hydrophobicity': -0.60,
          'behavior': 'polar'
          },
      'GLN': {
          'label':'Q',
          'hydrophobicity': -0.22,
          'behavior': 'polar'
          }
      }

# Amino acids with the same behavior
AMINO_CHAR = { char: [ i for i in AMINO if AMINO[i]["behavior"]==char ] 
              for char in ['polar', 'hydrophobic', 'acidic', 'basic' ] }


### PEPTIDES

Activity = {
    "NC00001"   : ["None"],
    "NC00002"   : ["None"],
    "NC00003"   : ["None"],
    "NC00004"   : ["None"],
    "NC00005"   : ["None"],
    "NC00006"   : ["None"],
    "NC00007"   : ["None"],
    "NC00008"   : ["None"],
    "NC00009"   : ["None"],
    "NC00010"   : ["None"],
    "DRAMP00008": [ "Antimicrobial", "Antibacterial", "Anti-Gram+"],
    "DRAMP00009": [	"Antimicrobial", "Antibacterial", "Anti-Gram+"],
    "DRAMP00012": [	"Antimicrobial", "Antibacterial" ],
    "DRAMP00013": [	"Antimicrobial", "Antibacterial" ],
    "DRAMP00037": [	"Antimicrobial", "Antibacterial", "Anti-Gram+"],
    "DRAMP00068": [	"Antimicrobial", "Antibacterial", "Anti-Gram+"],
    "DRAMP00143": [	"Antimicrobial", "Antibacterial" ],
    "DRAMP00169": [ "Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-" ],
    "DRAMP00170": [	"Antimicrobial", "Antibacterial", "Anti-Gram+"],
    "DRAMP00249": [	"Antimicrobial", "Antibacterial", "Antifungal"],
    "DRAMP00359": [ "" ],
    "DRAMP00363": [ "Antimicrobial", "Antibacterial" ],
    "DRAMP01007": [ "Antimicrobial", "Antibacterial", "Anti-Gram+", "Antifungal"  ],
    "DRAMP01301": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antifungal", "Antiprotozoal" ],
    "DRAMP01302": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antifungal" ],
    "DRAMP01303": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antifungal" ],
    "DRAMP01445": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antifungal" ],
    "DRAMP01549": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antiviral" ],
    "DRAMP01607": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Anti-cancer" ],
    "DRAMP01609": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-cancer" ],
    "DRAMP01610": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-cancer" ],
    "DRAMP01668": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antiprotozoal" ],
    "DRAMP02136": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antifungal" ],
    "DRAMP02315": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-" ],
    "DRAMP02316": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-" ],
    "DRAMP02317": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-" ],
    "DRAMP02330": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antifungal" ],
    "DRAMP02331": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antifungal" ],
    "DRAMP02386": [	"Antimicrobial", "Antibacterial" ],
    "DRAMP02473": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antifungal" ],
    "DRAMP02483": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Antifungal" ],
    "DRAMP02521": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antifungal" ],
    "DRAMP02960": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-" ],
    "DRAMP02961": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-" ],
    "DRAMP03002": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antifungal" ],
    "DRAMP03042": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-" ],
    "DRAMP03052": [	"Antimicrobial", "Antibacterial", "Anti-Gram+"],
    "DRAMP03217": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Insecticidal" ],
    "DRAMP03218": [	"Antimicrobial", "Antibacterial", "Insecticidal" ],
    "DRAMP03220": [	"Antimicrobial", "Antibacterial", "Insecticidal" ],
    "DRAMP03278": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antifungal" ],
    "DRAMP03279": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antifungal" ],
    "DRAMP03320": [	"Antimicrobial", "Antibacterial", "Anti-Gram+"],
    "DRAMP03721": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-" ],
    "DRAMP03724": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Hemolytic" ],
    "DRAMP03725": [	"Antimicrobial", "Antibacterial" ],
    "DRAMP03726": [	"Antimicrobial", "Antibacterial" ],
    "DRAMP03736": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antifungal" ],
    "DRAMP03750": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antifungal" ],
    "DRAMP03751": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antifungal" ],
    "DRAMP03823": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-" ],
    "DRAMP03967": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antitumor" ],
    "DRAMP04075": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-", "Antifungal" ],
    "DRAMP18193": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-" ],
    "DRAMP18508": [	"Antimicrobial", "Antibacterial", "Anti-Gram+", "Anti-Gram-" ] 
    }

### WATER MOLECULES

WATER = {
    "martini22":   "W",
    "martini22p":  "PW",
    # Duplicated in case other key is easier to use
    "Martini_v2.2": "W",
    "Martini_v2.2P": "PW"
    }

### FORCEFIELDS

FF = { "martini22p": { "ID" : 1,
                       "name" : "Martini_v2.2P" },
      "martini22":   { "ID" : 2,
                       "name" : "Martini_v2.2" },
      # Duplicated in case other key is easier to use
      "Martini_v2.2P": { "ID" : 1,
                         "name" : "Martini_v2.2P" },
      "Martini_v2.2":   { "ID" : 2,
                          "name" : "Martini_v2.2" }
    }

### MEMBRANE MODELS

MEMBRANE_MODELS = {
    "CANCER":        {'model': 'Cancer',
                      'name' : 'DOPC:DOPE:DOPS:DPSM:CHOL (3:3:3:2:4)' },
    "NORMAL":        {'model': 'Healthy mammal',
                      'name' : 'DOPC:DOPE:DOPS:DPSM:CHOL (2:2:1:0:2 / 1:2:4:3:5)' },
    "POPC":          {'model': 'Healthy mammal',
                      'name' : 'POPC' },
    "POPE_POPG_1_3": {'model': 'Gram-positive bacteria',
                      'name' : 'POPG:POPE (3:1)' },
    "POPE_POPG_3_1": {'model':'Gram-negative bacteria',
                      'name' : 'POPG:POPE (1:3)' },
    "POPE_POPG_1_9": {'model': 'Bacteria',
                      'name' : 'POPG:POPE (9:1)' },
    }



###### FUNCTIONS

def RoundStdv( Mean: float, Stdv: float, SigFig: int = 2 ) -> tuple :
    '''
    RoundStdv:
     - Performs the rounding of a magnitude and its standard deviation so the later
      is rounded with SigFig significant figures.
    '''

    # Define the format of the standar deviation
    StdvFormat = '%.' + str( SigFig ) + 'g'
    
    # Apply the format to each standar deviation
    Stdv = float( StdvFormat % Stdv )
    
    # The position of the last significant figure in the standar deviation is given by
    LastSigFig = int( np.floor ( np.log10( np.abs( Stdv ) ) ) ) - SigFig
    
    # And the first significant figure in the value
    FirstSigFig = int( np.floor ( np.log10( np.abs( Mean ) ) ) )
    
    # Number of significant figures
    MeanSigFig = [ int( FirstSigFig - LastSigFig ) if int( FirstSigFig - LastSigFig ) > 0 else 0 ][0]
    
    # So the appropriate formate for each value is
    MeanFormat = '%.' + str( MeanSigFig ) + 'g'

    # Apply the format to each value
    Mean = float( MeanFormat % Mean )
    
    # At this point, the rounding is correct, but the format may not be        
    # If the standar deviation is greater than the unit (in absolute terms)...
    if np.abs( Stdv ) >= 1:
        #...and the length of the string is greater than the SigFig + 1
        if len( str( np.abs(Stdv) ) ) > ( SigFig + 1 ):
            # ... then we only need to remove the decimal places (which are going to be zero)
            Stdv = str( int( Stdv ) )
            Mean = str( int( Mean ) )
        else:
            # If the lenght is smaller, then we need to introduce zeros
            # For a number of the form XX···X.YY···Y
            nX = int( np.floor( np.log10( np.abs( Stdv ) ) ) ) + 1
            
            # So the number of decimal places must be
            dec = SigFig - nX
            
            # Therefore, the format is
            Stdv = str( ( '{0:.' + str(dec) + 'f}' ).format(Stdv) )
            Mean = str( ( '{0:.' + str(dec) + 'f}' ).format(Mean) )
    # If the number is smaller than the unit
    else:
            
        # Again, we need to introduce zeros 
        # So the number of decimal places must be (as seen when rounding)
        dec = np.abs( int( np.floor ( np.log10( np.abs( Stdv ) ) ) ) - SigFig + 1 )
            
        # Therefore, the format is:
        Stdv = str( ( '{0:.' + str(dec) + 'f}' ).format(Stdv) )
        Mean = str( ( '{0:.' + str(dec) + 'f}' ).format(Mean) )
        
    return Mean , Stdv 


