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
imageStack = np.load(pathToImageStack)
ds = rasterio.open(myVRT)
print(ds.mode)
print(ds.height)
print(ds.width)
#print(ds.indexes)
gt = ds.transform
shape = (ds.height,ds.width)

# nd array to Dataframe
# one line corresponds to one time stamp (dod), all pixels shaped in a row, use reshape 
# img rows / cols to get original dimensions - see plotprint function
df = pd.DataFrame(imageStack)
overall_points = [[1,2,3]]
   
if plotprint:
    # using iteritems() function to retrieve rows
    for i in ds.indexes:
        # print(key, value) # value equals row content
        # reform a numpy array of the original shape
        #print(value)
        band_array = ds.read(i) #np.asarray(value).reshape(shape)

        # datetime(year, month, day, hour, minute, second, microsecond)

            #rasterFnSplit = os.path.basename(pathToImgFiles[key]).split('_')
            #rasterFnSplitDateTime = datetime.datetime.strptime(rasterFnSplit[3]+rasterFnSplit[4], "%Y%m%d%H%M")



        # Set up grid and test data
        nx, ny = ds.width, ds.height
        x = range(nx)
        y = range(ny,0,-1)

        #hf = plt.figure()
        #ha = hf.add_subplot(111, projection='3d')

        X, Y = np.meshgrid(x, y)  # `plot_surface` expects `x` and `y` data to be 2D
        #ha.plot_surface(X, Y, band_array)

        # plt.subplot(1, 2, 1) # row 1, col 2 index 1
        # plt.scatter(X, band_array, s=0.05)
        # plt.axhline(y=np.mean(band_array), color='r', linestyle='-')
        # plt.title('First view')
        # plt.xlabel('X-axis ')
        # plt.ylabel('Z-axis ')

        # plt.subplot(1, 2, 2) # index 2
        # plt.scatter(Y, band_array, s=0.05)
        # plt.axhline(y=np.mean(band_array), color='r', linestyle='-')
        # plt.title("Second view")
        # plt.xlabel('Y-axis ')
        # plt.ylabel('Z-axis ')

        # plt.show()

        # z=band_array.flatten()
        # mask_nan=z!=np.nan 
        # print(mask_nan)     
        # X=X.flatten()
        # Y=Y.flatten()
        # print(z.shape==z[mask_nan].shape)
        # pcd=np.column_stack((X[mask_nan],Y[mask_nan],z[mask_nan]))


        # Mask the nodata values:
        band_array = np.ma.masked_invalid(band_array)
        #print(np.logical_not(band_array.mask))
        X=X[np.logical_not(band_array.mask)]
        Y=Y[np.logical_not(band_array.mask)]
        z=band_array[np.logical_not(band_array.mask)]
        # Mask ignore Range
        z = np.where((z < ignoreRange) & (z > -ignoreRange) , 0.0, z )
    
        
        pcd=np.column_stack((X.flatten(),Y.flatten(),z.flatten()))

        # Mask values greater than mean
        #mask=z>np.nanmean(z)
        print(np.nanmean(z))
        spatial_query=pcd[z>np.nanmean(z)]
        print(pcd.shape==spatial_query.shape)


        overall_points = np.append(overall_points, spatial_query, axis=0)


        #plotting the results 3D
        ax = plt.axes(projection='3d')
        ax.scatter(overall_points[:,0], overall_points[:,1], overall_points[:,2], s=0.1)
        plt.show()

        #plotting the results 2D
        plt.scatter(overall_points[:,0], overall_points[:,1], s=0.1)
        plt.show()










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
#Close raster
ds = None
