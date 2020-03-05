#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  lib_readPL4.py
#  https://github.com/ldemattos/readPL4
#  
#  Copyright 2019 Leonardo M. N. de Mattos <l@mattos.eng.br>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, version 3.0.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

# Read PISA's binary PL4
def readPL4(pl4file):
	
	import mmap
	import struct
	import pandas as pd
	import numpy as np
	
	miscData = {
		'delta':0.0,
		'nvar':0,
		'pl4size':0,
		'steps':0,		
        'cpx':0,
        'nch':0
	}

	# open binary file for reading
	with open(pl4file, 'rb') as f:
		pl4 = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
		
		# read DELTAT
		miscData['delta'] = struct.unpack('<f', pl4[40:44])[0]
	
		# read number of vars
		miscData['nvar'] = struct.unpack('<L', pl4[48:52])[0] / 2
		
		# read PL4 disk size
		miscData['pl4size'] = struct.unpack('<L', pl4[56:60])[0]-1
		
		# compute the number of simulation miscData['steps'] from the PL4's file size
		miscData['steps'] = (miscData['pl4size'] - 5*16 - miscData['nvar']*16) / ((miscData['nvar']+1)*4)		
		
		# generate pandas dataframe	to store the PL4's header
		dfHEAD = pd.DataFrame()
		dfHEAD['TYPE'] = ''
		dfHEAD['FROM'] = ''
		dfHEAD['TO'] = ''
		
		for i in xrange(0,miscData['nvar']):
			pos = 5*16 + i*16
			h = struct.unpack('3x1c6s6s',pl4[pos:pos+16])
			dfHEAD = dfHEAD.append({'TYPE': int(h[0]),\
			                        'FROM': h[1],\
			                        'TO': h[2]}, ignore_index=True)
		
		# Check for unexpected rows of zeroes
		# See https://github.com/ldemattos/readPL4/issues/2
		expsize = (5 + miscData['nvar'])*16 + miscData['steps']*(miscData['nvar']+1)*4
		nullbytes = 0
		if miscData['pl4size'] > expsize: 
			nullbytes = miscData['pl4size']-expsize
		
		# read and store actual data, map it to a numpy read only array
		data = np.memmap(f,dtype=np.float32,mode='r',shape=(miscData['steps'],miscData['nvar']+1),\
        offset=(5 + miscData['nvar'])*16 + nullbytes)
        
		# Automatically convert header type
        convertType(dfHEAD)
        
        # Additional stuff from frequency scan
        miscData['cpx'] = struct.unpack('<L', pl4[64:68])[0]
        miscData['nch'] = struct.unpack('<L', pl4[68:72])[0]
        if (miscData['cpx'] !=0) and (miscData['nch'] != 0):
            
            # Acquire FMIN and FMAX directly from read data
            miscData['fmin'] = data[0,0]
            miscData['fmax'] = data[-1,0]
            
            # Adjust complex format
            if miscData['cpx'] > 0:
                dfHEAD['COMPLEX'] = ''
                setComplexType(dfHEAD,miscData['cpx'])
                
        else:        
            # Acquire TMAX directly from read data
            miscData['tmax'] = data[-1,0]
            
			
        return dfHEAD,data,miscData

# Convert types from integers to strings
def convertType(df):	
	df['TYPE'] = df['TYPE'].apply(lambda x: 'V-node' if x == 4 else x)
	df['TYPE'] = df['TYPE'].apply(lambda x: 'E-bran' if x == 7 else x)
	df['TYPE'] = df['TYPE'].apply(lambda x: 'V-bran' if x == 8 else x)
	df['TYPE'] = df['TYPE'].apply(lambda x: 'I-bran' if x == 9 else x)
	
	return 0
	
# Get desired variable data
def getVarData(dfHEAD,data,Type,From,To,Complex='COMPLEX'):	
	# Search for desired data in header
    if Complex=='COMPLEX':
        df = dfHEAD[(dfHEAD['TYPE'] == Type) & (dfHEAD['FROM'] == From) & (dfHEAD['TO'] == To)]
    else:
        df = dfHEAD[(dfHEAD['TYPE'] == Type) & (dfHEAD['FROM'] == From) &\
        (dfHEAD['TO'] == To) & (dfHEAD['COMPLEX'] == Complex)]
				
	if not df.empty:
		data_sel = data[:,df.index.values[0]+1] # One column shift given time vector
		
	else:
		print "Variable %s-%s of %s not found!"%(From,To,Type) 
		return(None)

	return(data_sel)
 
# Set correct complex type for each variable (freq. scan only)
def setComplexType(dfHEAD,cpx):
    from itertools import cycle

    if cpx == 3:
        seq = cycle(['ABS','ANG','RE','IM'])
    
    elif cpx == 2:
        seq = cycle(['RE','IM'])        
    
    elif cpx == 1:
        seq = cycle(['ABS','ANG'])    
    
    dfHEAD['COMPLEX'] = [next(seq) for count in range(dfHEAD.shape[0])]    
    
    return 0
