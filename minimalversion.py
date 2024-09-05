# import required modules
import os
import py4dgeo
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
from scipy.spatial import KDTree
import statistics


image_width = 370
image_height = 459

# Changepoint detection parameter
height_threshhold = -0.04
occurence_threshold = 0.2          # Prozent der Pixel unter dem Schwellwert, damit Event erkannt wird
mean_threshold = 0.1             # difference threshold of the means before and after the changepoints

def build_analysis():
    analysis = py4dgeo.SpatiotemporalAnalysis(f'{data_path}/riverbank.zip', force=True)

    # read distance array
    analysis.distances=np.transpose(np.load('4dfilt.npy'))

    # apply temporal averaging
    analysis.smoothed_distances = py4dgeo.temporal_averaging(analysis.distances, smoothing_window=6)

    # create reference cloud
    x = range(image_width)
    y = range(image_height,0,-1)
    X, Y = np.meshgrid(x, y)
    z=np.zeros(image_width*image_height)
    cloud=np.column_stack((X.flatten(),Y.flatten(),z.flatten()))

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
create_analysis = input("Create a new analysis [y/n]:")
if(create_analysis == "n"):
    analysis = py4dgeo.SpatiotemporalAnalysis(f'{data_path}/riverbank.zip')
else:
    analysis = build_analysis()

# load the smoothed distances
distances = analysis.smoothed_distances

def plot_time_series(timestamps, time_series):
    # plot the time series
    plt.plot(timestamps, time_series, c='blue', linewidth=1.0)

    # format the date labels
    dtFmt = mdates.DateFormatter('%b-%d') 
    plt.gca().xaxis.set_major_formatter(dtFmt) 

    # add plot elements
    plt.xlabel('Date')
    plt.ylabel('Anteil der Punkte kleiner als Schwellwert')
    plt.ylim(0, max(time_series)+0.5*max(time_series))

    # add grid with minor ticks every day
    plt.grid(which='both', linestyle='--')
    plt.gca().xaxis.set_minor_locator(mdates.DayLocator(interval=12))

    plt.show()

def plot_temporal_result(timestamps, time_series):

    plt.bar(timestamps, time_series, color ='maroon', 
        width = 0.2)
    plt.show()


def plot_image_results(events, region_width, region_height, timestamp_index):
    fig, ax = plt.subplots(1,1, figsize=(5,5))
    # get the change magnitude of the last epoch
    change_vals = analysis.smoothed_distances[:, timestamp_index]
    cloud = analysis.corepoints.cloud
    # plot coordinates colored by change values 
    d = ax.scatter(cloud[:,0], cloud[:,1], c = change_vals, cmap='seismic_r', vmin=-1.0, vmax=1.0, s=1)
    ax.set_aspect('equal')
    plt.colorbar(d, format=('%.2f'), label='Change value [m]', ax=ax)

    # add plot elements
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    for event in events:
        shape = Rectangle(event[1:3],
                    width=region_width,
                    height=region_height,
                    angle=0,
                    color=(0,0.8,0,event[0]))
        ax.add_patch(shape)
    plt.show()


def get_idxs_from_koords(x1,y1,x2,y2):
    
    """ 
    Eingabe: 2 (x,y) Koordinaten
    Ausgabe: Array mit gewählten Indexes 
    """
    # create Array with interested x,y and z as zero
    x = range(x1,x2)
    y = range(y2,y1,-1)
    X, Y = np.meshgrid(x, y)
    z=np.zeros((x2-x1)*(y2-y1))
    region=np.column_stack((X.flatten(),Y.flatten(),z.flatten()))

    # get indexes of these points
    corepoints_cloud = analysis.corepoints.cloud
    tree = KDTree(np.c_[corepoints_cloud[:,0].ravel(), corepoints_cloud[:,1].ravel()])
    dd, cp_sel_idxs = tree.query(region[:,:2], k=1)
    return cp_sel_idxs

# unweighted
def calc_weighted_mean_difference(number_values_below_list, start, changepoint, end):
    mean_before_cp = statistics.mean(number_values_below_list[0:changepoint])
    mean_after_cp = statistics.mean(number_values_below_list[changepoint:None])
    mean_difference = mean_after_cp-mean_before_cp
    if(mean_difference <= 0):
        return 0
    return mean_difference

overall_changepoints = 0
events = []

# Request User Input
timespan_start = int(input("Enter timespan start (Index):"))
timespan_end = int(input("Enter timespan end (Index):"))
if(timespan_start < 0 or timespan_start > 908 or timespan_end <0 or timespan_end>908 or timespan_end<timespan_start):
    print("invalid timespan")
    quit()
window_width = int(input("Enter window size:"))
window_height = window_width
if(window_height < 0 or window_height >300):
    print("invalid window size")
    quit()


# iterate over picture from from left to right
for i in range(0,image_width-window_width,window_width):
    # iterate over picture from bottom to top
    for j in range(150,image_height-window_height,window_height):
        selected_idx = get_idxs_from_koords(i,j, i+window_width,j+window_height)
        changepoints = []
        number_values_below_list = []
        # get the wanted pixels in the wanted timespan
        region_distances =  analysis.smoothed_distances[selected_idx, timespan_start:timespan_end]
        number_values_below_old = -1
        for imageindex in range(timespan_end-timespan_start):
            # single picture
            image = region_distances[:,imageindex]
            number_values_below = 0
            
            # get number of values below threshold
            for pixel in image:
                if(pixel<=height_threshhold):
                    number_values_below+=1

            number_values_below_list.append(number_values_below/len(image))

            # initialy set old value
            if(number_values_below_old == -1):
                number_values_below_old = number_values_below

            # register changepoints
            if((number_values_below/len(image))>=occurence_threshold and (number_values_below-number_values_below_old)/len(image)>=occurence_threshold/2):
                changepoints.append([imageindex, number_values_below-number_values_below_old])

            number_values_below_old = number_values_below

        # filter and score changepoints
        if(len(changepoints) == 1):
                # prove Changepoint signifikance by difference of mean of values before and after changepoint
                mean_difference = calc_weighted_mean_difference(number_values_below_list, 0, changepoints[0][0], None)
                if(mean_difference >= mean_threshold):
                    score =  mean_difference  
                    events.append([score, i,j, timestamps[changepoints[0][0]]])
        elif (changepoints): 
            # split at changepoints and score regions seperatly:
            for k in range(len(changepoints)-1):
                if(k==0):
                    mean_difference = calc_weighted_mean_difference(number_values_below_list, 0, changepoints[k][0], changepoints[k+1][0])
                else :
                    mean_difference = calc_weighted_mean_difference(number_values_below_list, changepoints[k-1][0], changepoints[k][0], changepoints[k+1][0])
                # prove Changepoint signifikance by difference of mean of values before and after changepoint
                if(mean_difference >= mean_threshold):
                    score = mean_difference
                    events.append([score, i,j, timestamps[changepoints[k][0]]])
            
            # last changepoint until end of timeseries
            mean_difference = calc_weighted_mean_difference(number_values_below_list, changepoints[-2][0], changepoints[-1][0], None)
            if(mean_difference >= mean_threshold):
                score = mean_difference #changepoints[-1][1] * 
                events.append([score, i,j, timestamps[changepoints[-1][0]]])
        
        overall_changepoints += len(changepoints)

print(overall_changepoints)
events = np.array(events)
if(events.any()):
    sorted_events = events[events[:,0].argsort()]
    print(sorted_events[:,])
    print(len(sorted_events))

    # plot spatial results
    plot_image_results(events, window_width, window_height, timespan_end)
    
    # plot temporal results
    timeseries = np.zeros(timespan_end-timespan_start)
    for event in events:
        # sum up scores for timestamps
        timeseries[timestamps.index(event[3])] = timeseries[timestamps.index(event[3])] + event[0]
    plot_time_series(timestamps[timespan_start:timespan_end], timeseries)
    plot_temporal_result(timestamps[timespan_start:timespan_end],timeseries)














