# import required modules
import os
import py4dgeo
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from sklearn.cluster import KMeans
from linearChangeSeedAnders import LinearChangeSeeds
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
analysis = py4dgeo.SpatiotemporalAnalysis(f'{data_path}/riverbank.zip')
#analysis = build_analysis()

# load the smoothed distances
#analysis.smoothed_distances = py4dgeo.temporal_averaging(analysis.distances, smoothing_window=6)
distances = analysis.smoothed_distances

# extract the time series at the selected core point
cp_sel_idx = 102341
#ts_sel = distances[cp_sel_idx]

########################################################### 4d obc ------

# analysis.invalidate_results(seeds=True, objects=True)
# algo = LinearChangeSeeds(
#     neighborhood_radius=2.0,
#     seed_subsampling=30,    # nur jeden 30. Punkt untersuchen --> für echte Analyse lieber 1 nehmen
#     window_width=6,
#     minperiod=3,
#     height_threshold=0.10,
# )

locs_of_interest = np.array([[110, 290, 1.78810005e+01],
       [125, 200, 1.85109997e+01],
       [270, 160, 1.83260002e+01],
       [131, 229, 2.41650009e+01],
       [128, 206, 2.34039993e+01],
       [54, 347, 2.29480000e+01],
       [273, 170, 2.91429996e+01],
       [192, 108, 2.89029999e+01],
       [134, 164, 3.05119991e+01],
       [160, 160, 3.13659992e+01]])
print(locs_of_interest)
# build scipy kd-tree to search for corepoints corresponding to locs of interest
from scipy.spatial import KDTree
corepoints_cloud = analysis.corepoints.cloud
tree = KDTree(np.c_[corepoints_cloud[:,0].ravel(), corepoints_cloud[:,1].ravel()])
dd, cp_sel_idxs = tree.query(locs_of_interest[:,:2], k=1)
cp_sel = corepoints_cloud[cp_sel_idxs]

if 1:
    cp_sel_idx = cp_sel_idxs[1]
    #for cp_sel_idx in cp_sel_idxs:
    ts_sel = analysis.distances[cp_sel_idx]

    plt.plot(ts_sel, label='dist')
    plt.plot(analysis.smoothed_distances[cp_sel_idx], label='smoothed')
    plt.legend()
    plt.show()

print(cp_sel_idxs)
# region growing params are experimental
algo = LinearChangeSeeds(
    neighborhood_radius=2.0,
    min_segments=500,
    minperiod = 3,
    thresholds=[0.5,0.6,0.7,0.8,0.9], max_segments=10000, seed_candidates=list(cp_sel_idxs)) #  #[84076]

# only needs to be rerun, if the algorithm above is changed (results are stored in the analysis object)
analysis.invalidate_results(seeds=True, objects=True, smoothed_distances=False)
objects = algo.run(analysis)

print("test")
print(f"The segmentation extracted {len(objects)} 4D objects-by-change.")

sel_cp = 84076 # index of selected corepoint
oid = 0 # index of selected object

store_all = True

example_seed = objects[0].seed
seed_end = example_seed.end_epoch
seed_start = example_seed.start_epoch
seed_cp_idx = example_seed.index

seed_timeseries = analysis.smoothed_distances[seed_cp_idx]

plt.plot(seed_timeseries, c='blue')
plt.scatter(seed_start, seed_timeseries[seed_start], c='black')
plt.scatter(seed_end, seed_timeseries[seed_end], c='black')
plt.show()


# # store all seed properties in an array: corepoint index, start epoch, end epoch
# all_seeds = analysis.seeds
# all_seeds_props = np.zeros((len(all_seeds),3), dtype=int)
# s=0
# for seed in all_seeds:
#     all_seeds_props[s] = [seed.index, seed.start_epoch, seed.end_epoch]
#     s+=1
# sel_seeds_props = all_seeds_props

# cmap = mpl.cm.get_cmap('nipy_spectral')

# s=0
# timestamps = [t + analysis.reference_epoch.timestamp for t in analysis.timedeltas]
# timestamps_range = range(len(timestamps))

# import matplotlib.dates as mdates
# fig,ax = plt.subplots()
# ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d')) #'%Y' %H:%M

# for seed, cmapval in zip(sel_seeds_props, np.arange(0,1.0,1.0/len(sel_seeds_props))):
#     s += 1
#     if s%1>0:
#         continue

#     seed_end = seed[2]
#     seed_start = seed[1]
#     seed_cp_idx = seed[0]

#     seed_timeseries = analysis.smoothed_distances[seed_cp_idx]

#     cp_idx, start_epoch, stop_epoch = seed
#     timeseries = analysis.smoothed_distances[cp_idx]
#     timeseries_seed = timeseries[start_epoch:stop_epoch+1]

#     rgba = cmap(cmapval)
#     plt.plot(timestamps, timeseries, label=cp_idx, c='black', alpha=0.5, linewidth=.5)
#     plt.plot(timestamps[start_epoch:stop_epoch+1], timeseries_seed, label=cp_idx, c=rgba, alpha=0.5, linewidth=2.)

# #plt.legend()
# plt.tight_layout()
# #plt.savefig('seed_timeseries_all.png', dpi=300)
# #plt.close()
# plt.show()

# objects[oid].plot()

# from scipy.spatial import ConvexHull
# from matplotlib.patches import Polygon

# fig, axs = plt.subplots(1,2,figsize=(9,5))
# fig.set_facecolor('white')
# ax1, ax2 = axs
# # get indices of 4D-OBC
# idxs = objects[oid].indices

# # subset of core points incorporated in 4D-OBC
# cloud = analysis.corepoints.cloud
# subset_cloud = cloud[idxs,:2]

# # Compute convex hull
# hull = ConvexHull(subset_cloud)

# # plot the timeseries
# ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d')) #'%Y' %H:%M
# seed_timeseries = analysis.smoothed_distances[sel_cp]

# start_epoch = objects[oid].start_epoch
# end_epoch = objects[oid].end_epoch
# timeseries = analysis.smoothed_distances[sel_cp]
# timeseries_seed = timeseries[start_epoch:end_epoch+1]

# # Extract DTW distances from this object
# indexarray = np.fromiter(objects[oid].indices, np.int32)
# distarray = np.fromiter((objects[oid].distance(i) for i in indexarray), np.float64)
# # Create a colormap with distance for this object
# cmap = plt.cm.get_cmap("viridis")
# maxdist = np.nanmax(distarray)
# for idx in idxs[::50]:
#     pp = ax1.plot(
#             timestamps,
#             analysis.distances_for_compute[idx],
#             linewidth=0.7,
#             alpha=0.3,
#             color=cmap(objects[oid].distance(idx)), #  / maxdist #do not normalize, but assume full possible range from 0 to 1; thereby all colorbars are scaled the same
#     )
# #plt.colorbar(pp, label='DTW distance', ax=ax1, shrink=.8)
# sm = plt.cm.ScalarMappable(cmap='viridis', norm=plt.Normalize(vmin=0, vmax=1))
# plt.colorbar(sm, label='DTW distance', ax=ax1, shrink=.8)

# ax1.plot(timestamps, timeseries, label=sel_cp, c='black', alpha=0.75, linewidth=.5)
# ax1.plot(timestamps[start_epoch:end_epoch+1], timeseries_seed, label=sel_cp, c='blue', alpha=1., linewidth=2.)
# ax1.set_label('M3C2 distance [m]')

# # plot the corepoints cloud - change values at peak magnitude of object
# epoch_of_interest = int(objects[oid].end_epoch) #int(objects[oid].start_epoch + (objects[oid].end_epoch - objects[oid].start_epoch)/2)
# distances_of_interest = [dists[epoch_of_interest] for dists in analysis.smoothed_distances]
# sc = ax2.scatter(cloud[:,0], cloud[:,1], c = distances_of_interest, cmap='seismic', s=1, vmin=-0.5, vmax=0.5)
# plt.colorbar(sc, label='M3C2 distance [m]', ax=ax2, shrink=.8)

# # add further elements to map plot
# ax2.set_aspect('equal')
# # plot convex hull
# ax2.add_patch(Polygon(subset_cloud[hull.vertices,0:2], label = 'convex hull', fill = False))
# # plot seed location
# ax2.scatter(cloud[sel_cp,0], cloud[sel_cp,1], marker = '*', c = 'black', label = 'seed', s=5)
# ax2.legend()

# ax2.set_title(f'{(analysis.reference_epoch.timestamp + analysis.timedeltas[epoch_of_interest]).strftime("%Y-%m-%d %H:%M")}', y=1.03)

# plt.tight_layout()