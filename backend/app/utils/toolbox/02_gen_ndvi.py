##!/usr/bin/env python

# Parameters
lib_dir =  '/home/jinha/python/lib'
in_dir =   '/home/jinha/jinha-depot/gdsl/Cruz_PPAC/2019/01_COR19-03_TAR/results/mcs'
out_dir =  '/home/jinha/jinha-depot/gdsl/Cruz_PPAC/2019/01_COR19-03_TAR/results/ndvi'
out_suffix = '_ppac_mcs_tar_ndvi.dat'
gdal_driver = 'ENVI'
img_ext = '.tif'
band_nir = 4
band_r = 2

# Import libraries
import sys, os, glob
import numpy as np
from osgeo import gdal, gdalnumeric, ogr, osr
sys.path.insert(1, lib_dir)
import rs3

# Load all tif files in in_dir
files = glob.glob(in_dir + '/' + '*' + img_ext)
files.sort()
print(*files, sep='\n')

# Create out_dir if not existing
if not os.path.exists(out_dir):
	os.makedirs(out_dir)

for i in range(len(files)):
	print('Procesing ', str(i+1), '/', str(len(files)), '   (', str('{:.0f}'.format(float(i+1) / len(files) * 100.0)), '%)')

	# Input file name
	in_fn = files[i]

	# Open image without loading to memory
	in_img = rs3.RSImage(in_fn)

	# Initialize output array
	out_arr = np.zeros((1, in_img.ncol, in_img.nrow), dtype = np.float32)

	# Read bands
	nir = in_img.img[band_nir,:,:].astype(np.float32)
	red = in_img.img[band_r,:,:].astype(np.float32)

	# Calculate normalized difference vegetation index
	b1 = nir - red
	b2 = nir + red
	ndvi = b1 / b2

	# Save image
	basename = os.path.basename(in_fn)
	out_fn = os.path.join(out_dir, os.path.splitext(basename)[0][0:8] + out_suffix)
	driver = gdal.GetDriverByName(gdal_driver)
	outds = driver.Create(out_fn, in_img.ds.RasterXSize, in_img.ds.RasterYSize, 1, gdal.GDT_Float32)
	outds.SetGeoTransform(in_img.ds.GetGeoTransform())
	outds.SetProjection(in_img.ds.GetProjection())
	outds.GetRasterBand(1).WriteArray(ndvi)
	outds = None