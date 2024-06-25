# import required modules
import os
import py4dgeo
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from sklearn.cluster import KMeans

import readfromvrt



def build_analysis():
    analysis = py4dgeo.SpatiotemporalAnalysis(f'{data_path}/riverbank.zip', force=True)

    # read distance array
    analysis.distances=np.transpose(np.load('4dfilt.npy'))

    # apply temporal averaging
    analysis.smoothed_distances = py4dgeo.temporal_averaging(analysis.distances, smoothing_window=6)

    # create reference cloud
    x = range(370)
    y = range(459,0,-1)
    X, Y = np.meshgrid(x, y)
    z=np.zeros(169830)
    cloud=np.column_stack((X.flatten(),Y.flatten(),z.flatten()))
    #print(cloud)

    analysis.corepoints = cloud

    return analysis

# specify the data path
data_path = os.curdir

# sub-directory containing the point clouds
pc_dir = os.path.join(data_path, 'rasterized_dod')

# check if the data path exists
if not os.path.exists(pc_dir):
    raise Exception('Data path does not exist. Please make sure to specify the correct path.')

# list of point clouds (time series)
pc_list = os.listdir(pc_dir)

print(pc_list[5])

timestamps = []
for f in pc_list:
    if not f.endswith('.tif'):
        continue

    # get the timestamp from the file name
    timestamp_str = '_'.join((f.split('.')[0].split('_')[3:5])) # yields YYYYMMDD_hhmmss

    # convert string to datetime object
    timestamp = datetime.strptime(timestamp_str[2:], '%y%m%d_%H%M')
    timestamps.append(timestamp)

# create the spatiotemporal analysis object  
# Use one of these two lines !!
analysis = py4dgeo.SpatiotemporalAnalysis(f'{data_path}/riverbank.zip')
#analysis = build_analysis()

# load the smoothed distances
distances = analysis.smoothed_distances

# extract the time series at the selected core point
cp_sel_idx = 102341
ts_sel = distances[cp_sel_idx]
print(ts_sel)

# plot the time series
plt.plot(timestamps, ts_sel, c='blue', linewidth=1.0)

# format the date labels
dtFmt = mdates.DateFormatter('%b-%d') 
plt.gca().xaxis.set_major_formatter(dtFmt) 

# add plot elements
plt.xlabel('Date')
plt.ylabel('Distance [m]')
plt.ylim(-0.1, 0.1)

# add grid with minor ticks every day
plt.grid(which='both', linestyle='--')
plt.gca().xaxis.set_minor_locator(mdates.DayLocator(interval=12))

plt.show()



fig, ax = plt.subplots(1,1, figsize=(15,5))

# get the change magnitude of the last epoch
change_vals = analysis.smoothed_distances[:, -1]

# plot coordinates colored by change values 
cloud = analysis.corepoints.cloud
d = ax.scatter(cloud[:,0], cloud[:,1], c = change_vals, cmap='seismic_r', vmin=-1.0, vmax=1.0, s=1)
ax.set_aspect('equal')
plt.colorbar(d, format=('%.2f'), label='Change value [m]', ax=ax)

# add plot elements
ax.set_xlabel('X [m]')
ax.set_ylabel('Y [m]')

#print(cloud[:,0]) # gibt erste Spalte zurück!!--------------------
plt.show()


#define the number of clusters
ks = [6]

# create an array to store the labels
labels = np.full((distances.shape[0], len(ks)), np.nan)

# perform clustering for each number of clusters
for kidx, k in enumerate(ks):
    print(f'Performing clustering with k={k}...')
    nan_indicator = np.logical_not(np.isnan(np.sum(distances, axis=1)))
    kmeans = KMeans(n_clusters=k, random_state=0).fit(distances[nan_indicator, :])
    labels[nan_indicator, kidx] = kmeans.labels_

# plot the cluster labels as a map
fig, ax = plt.subplots(1,1, figsize=(7,7))

cmap_clustering = 'tab20'
sc1 = ax.scatter(cloud[:,0],cloud[:,1],c=labels[:,0],cmap=cmap_clustering,s=1, label=ks[0])

ax.set_aspect('equal')
ax.set_title(f'# clusters = {ks[0]}')

plt.tight_layout()
plt.show()
