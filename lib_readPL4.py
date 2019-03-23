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
		'deltat':0.0,
		'nvar':0,
		'pl4size':0,
		'steps':0,
		'tmax':0.0
	}

	# open binary file for reading
	with open(pl4file, 'rb') as f:
		pl4 = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
		
		# read DELTAT
		miscData['deltat'] = struct.unpack('<f', pl4[40:44])[0]
	
		# read number of vars
		miscData['nvar'] = struct.unpack('<L', pl4[48:52])[0] / 2
		
		# read PL4 disk size
		miscData['pl4size'] = struct.unpack('<L', pl4[56:60])[0]-1
		
		# compute the number of simulation miscData['steps'] from the PL4's file size
		miscData['steps'] = (miscData['pl4size'] - 5*16 - miscData['nvar']*16) / ((miscData['nvar']+1)*4)
		miscData['tmax'] = (miscData['steps']-1)*miscData['deltat']
		
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
		
		# read and store actual data, map it to a numpy read only array
		data = np.memmap(f,dtype=np.float32,mode='r',shape=(miscData['steps'],miscData['nvar']+1),offset=5*16 + miscData['nvar']*16)
			
		return dfHEAD,data,miscData

# Convert types from integers to strings
def convertType(df):	
	df['TYPE'] = df['TYPE'].apply(lambda x: 'V-node' if x == 4 else x)
	df['TYPE'] = df['TYPE'].apply(lambda x: 'E-bran' if x == 7 else x)
	df['TYPE'] = df['TYPE'].apply(lambda x: 'V-bran' if x == 8 else x)
	df['TYPE'] = df['TYPE'].apply(lambda x: 'I-bran' if x == 9 else x)
	
	return 0
	
# Get desired variable data
def getVarData(dfHEAD,data,Type,From,To):
	
	import numpy as np
	
	# Search for desired data in header
	df = dfHEAD[(dfHEAD['TYPE'] == Type) & (dfHEAD['FROM'] == From) & (dfHEAD['TO'] == To)]
				
	if not df.empty:
		data_sel = data[:,df.index.values[0]+1] # One column shift given time vector
		
	else:
		print "Variable %s-%s of %s not found!"%(From,To,Type) 
		return(None)

	return(data_sel)
