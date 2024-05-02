#os.environ['PROJ_LIB'] = 'C:\\Users\\Mela\\anaconda3\\Library\\share\\proj'
#os.environ['GDAL_DATA'] = 'C:\\Users\\Mela\\anaconda3\\Library\\share'

import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import datetime
import rasterio
import rasterio
from mpl_toolkits.mplot3d import Axes3D


# global settings
np.set_printoptions(threshold=np. inf)



'''SETTINGS'''
#set wd
wd = r'C:\Users\adria\Documents\PhotogKP'
# set filter to test
# other
plotprint = True # Print filtered pngs (required for video output!)
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
ds = rasterio.open(myVRT)
print(ds.mode)
print(ds.height)
print(ds.width)
shape = (ds.height,ds.width)

def get_graph_of_pixel(x,y, time):
    graph=[[0,0]]
    for i in range(1,time):
        band_array = ds.read(i)
        graph = np.append(graph, [[i,band_array[x,y]]], axis=0)
        print(band_array[x,y])
    
    plt.figure(dpi=100)
    plt.plot(graph[:,0],graph[:,1])
    plt.show()
    return

get_graph_of_pixel(200,200, 900)


#Close raster
ds = None





        # Calculate the extent:
            # if key == 0:
            #     ys, xs = band_array.shape
            #     ulx, xres, _, uly, _, yres = gt
            #     extent = [ulx, ulx+xres*xs, uly, uly+yres*ys]
            
            # # And plot the result:
            # fig, ax = plt.subplots(figsize=(5,6), constrained_layout=True, facecolor='w', dpi=300)
            # # generate cmap
            # cmap = plt.cm.get_cmap("bwr").copy() # cmap = plt.cm.viridis
            # cmap.set_bad('gray')
            # # show
            # im = ax.imshow(band_array, extent=extent, vmin = -0.5, vmax = 0.5, cmap=cmap)
            # cb = fig.colorbar(im, shrink=.5)
            # # set labels and axis titles
            # ax.set_title('M3C2 distance: ' + rasterFnSplitDateTime.strftime("%Y-%m-%d, %H:%M"), pad=30)
            # ax.set_xlabel('Column #')
            # ax.set_ylabel('Row #')
            # # output
            # file_out = os.path.join(os.path.basename(os.path.splitext(pathToImgFiles[key])[0])+ "_" +  '_filtered.png')
            # print(file_out)
            # ax.figure.savefig(file_out)
            # plt.close()
            # print(rasterFnSplitDateTime.strftime("%Y-%m-%d, %H:%M"))

