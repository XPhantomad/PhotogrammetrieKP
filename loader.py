#os.environ['PROJ_LIB'] = 'C:\\Users\\Mela\\anaconda3\\Library\\share\\proj'
#os.environ['GDAL_DATA'] = 'C:\\Users\\Mela\\anaconda3\\Library\\share'

import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
from osgeo import gdal
import datetime


# global settings
np.set_printoptions(threshold=np. inf)



'''SETTINGS'''
#set wd
wd = r'D:\PROJECTS\PULMANKIJOKI\PROCESSED_DATA\SFM_CHANGE-DETECTION\bank_erosion_game_TL\CD_Bank_20210418__20211020_Game_TL_dayOnly_all\compareM3C2'
# set filter to test
# other
plotprint = False # Print filtered pngs (required for video output!)
ignoreRange = 0.10 # ignore values +-val in output because of non-significant change (e.g. due to noise, registration error, ...)
useIgnoreRange = True
videoOutput = False # generate a video out of the filtered images
fillNAlimit = 10 # max 10 connected pixels to be filled if no information is given
#epsgCode = 32635 #work locally -> not yet implemented

# 3.4.24: calc some stats
stats = True

'''PROCESSING'''

    

myVRT = os.path.join(wd, 'myVRT.tif')
pathToImgFiles = sorted(glob.glob(os.path.join(wd, 'm3c2', '*RASTER_Z_AND_SF_b4.tif')))
pathToImageStack = os.path.join(wd, '4dfilt.npy')


# load image stack # npy array. use VRT to get image dimensions
print ("prepared image stack found. Continue ...")
imageStack = np.load(pathToImageStack)
ds = gdal.Open(myVRT, gdal.GA_ReadOnly)
gt = ds.GetGeoTransform()
shape = ds.GetRasterBand(1).ReadAsArray().shape
nodata = ds.GetRasterBand(1).GetNoDataValue()

# nd array to Dataframe
# one line corresponds to one time stamp (dod), all pixels shaped in a row, use reshape 
# img rows / cols to get original dimensions - see plotprint function
df = pd.DataFrame(imageStack)

   
if plotprint:
    # using iteritems() function to retrieve rows
    for key, value in df.iterrows():
        # print(key, value) # value equals row content
        # reform a numpy array of the original shape
        band_array = np.asarray(value).reshape(shape)
        # datetime(year, month, day, hour, minute, second, microsecond)
        rasterFnSplit = os.path.basename(pathToImgFiles[key]).split('_')
        rasterFnSplitDateTime = datetime.datetime.strptime(rasterFnSplit[3]+rasterFnSplit[4], "%Y%m%d%H%M")
        # Mask the nodata values:
        band_array = np.ma.masked_values(band_array, nodata)
        if useIgnoreRange:
            band_array = np.where((band_array < ignoreRange) & (band_array > -ignoreRange) , 0.0, band_array )

        # Calculate the extent:
        if key == 0:
            ys, xs = band_array.shape
            ulx, xres, _, uly, _, yres = gt
            extent = [ulx, ulx+xres*xs, uly, uly+yres*ys]
        
        # And plot the result:
        fig, ax = plt.subplots(figsize=(5,6), constrained_layout=True, facecolor='w', dpi=300)
        # generate cmap
        cmap = plt.cm.get_cmap("bwr").copy() # cmap = plt.cm.viridis
        cmap.set_bad('gray')
        # show
        im = ax.imshow(band_array, extent=extent, vmin = -0.5, vmax = 0.5, cmap=cmap)
        cb = fig.colorbar(im, shrink=.5)
        # set labels and axis titles
        ax.set_title('M3C2 distance: ' + rasterFnSplitDateTime.strftime("%Y-%m-%d, %H:%M"), pad=30)
        ax.set_xlabel('Column #')
        ax.set_ylabel('Row #')
        # output
        file_out = os.path.join(os.path.basename(os.path.splitext(pathToImgFiles[key])[0])+ "_" +  '_filtered.png')
        print(file_out)
        ax.figure.savefig(file_out)
        plt.close()
        print(rasterFnSplitDateTime.strftime("%Y-%m-%d, %H:%M"))
#Close raster
ds = None
