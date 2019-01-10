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

	# open binary file for reading
	with open(pl4file, 'rb') as f:
		pl4 = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
		
		# read DELTAT
		deltat = struct.unpack('<f', pl4[40:44])[0]
		print "DELTAT=%f"%(deltat)
	
		# read number of vars
		nvar = struct.unpack('<L', pl4[48:52])[0] / 2
		print "nvar=%i"%(nvar)
		
		# read PL4 disk size
		pl4size = struct.unpack('<L', pl4[56:60])[0]-1
		print "pl4size=%i"%(pl4size)
		
		# compute the number of simulation steps from the PL4's file size
		steps = (pl4size - 5*16 - nvar*16) / ((nvar+1)*4)
		print "STEPS=%i / TMAX=%f"%(steps,(steps-1)*deltat)
		
		# generate pandas dataframe	to store the PL4's header
		dfHEAD = pd.DataFrame()
		dfHEAD['TYPE'] = ''
		dfHEAD['FROM'] = ''
		dfHEAD['TO'] = ''
		
		for i in xrange(0,nvar):
			pos = 5*16 + i*16
			h = struct.unpack('3x1c6s6s',pl4[pos:pos+16])
			dfHEAD = dfHEAD.append({'TYPE': int(h[0]),\
			                        'FROM': h[1],\
			                        'TO': h[2]}, ignore_index=True)
		
		# read and store actual data, map it to a numpy read only array
		data = np.memmap(f,dtype=np.float32,mode='r',shape=(steps,nvar+1),offset=5*16 + nvar*16)
			
		return dfHEAD,data

# Convert types from integers to strings
def convertType(df):
	
	df['TYPE'] = df['TYPE'].apply(lambda x: 'V-node' if x == 4 else x)
	df['TYPE'] = df['TYPE'].apply(lambda x: 'V-bran' if x == 8 else x)
	df['TYPE'] = df['TYPE'].apply(lambda x: 'I-bran' if x == 9 else x)
	
	return 0
	
