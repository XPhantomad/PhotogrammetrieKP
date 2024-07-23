# import required modules
import os
import py4dgeo
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from sklearn.cluster import KMeans
from scipy.spatial import KDTree
import statistics


image_width = 370
image_height = 459

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
distances = analysis.smoothed_distances

#Bereich: (250,150 bis 285,180)

locs_of_interest = np.array([[250,150, 1.78810005e+01],
       [285, 150, 1.85109997e+01],
       [250, 151, 1.85109997e+01],
       [250, 151, 1.85109997e+01],
       [250,152, 1.78810005e+01],
       [285,180, 1.78810005e+01]])

# WErte der Matrix: 370x460
        #y
#114580  150
#114210  151
#113840  152


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

def plot_image(region, cp_sel_idxs):
    fig, ax = plt.subplots(1,1, figsize=(5,5))
    # get the change magnitude of the last epoch
    change_vals = analysis.smoothed_distances[cp_sel_idxs, -1] # get last epoch
    # plot coordinates colored by change values 
    d = ax.scatter(region[:,0], region[:,1], c = change_vals, cmap='seismic_r', vmin=-1.0, vmax=1.0, s=1)
    ax.set_aspect('equal')
    plt.colorbar(d, format=('%.2f'), label='Change value [m]', ax=ax)

    # add plot elements
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')

    #print(cloud[:,0]) # gibt erste Spalte zurück!!--------------------
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
    #print(cp_sel_idxs)

    #plot_image(region, cp_sel_idxs)

    return cp_sel_idxs


overall_changepoints = 0
events = []

height_threshhold = -0.04
occurence_threshold = 0.2          # Prozent der Pixel unter dem Schwellwert, damit Event erkannt wird
event_length_threshold = 20        # Anzahl an Bilder, die das Event mindestens lang sein muss --> flackern beseitigen (TODO: alle registrieren und danach ordnen)

#TODO: diese Parameter iterativ durchgehen
window_width = 30
window_height = 30
timespan_start = 0      # index of image    
timespan_end = 909      # index of image max = 909

# iterate over picture from from left to right
for i in range(0,image_width-window_width,window_width):
    # iterate over picture from bottom to top
    for j in range(0,image_height-window_height,window_height):
        #TODO: Iterate over timeslices (FRAGE: Wie klein)
        selected_idx = get_idxs_from_koords(i,j, i+window_width,j+window_height)
        up = False
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
           

            ## Findet Sprung --> filtert zu kurze heraus (falls gefiltert, kann neuer gefunden werden)

            # register change point (UP)
            # zusätzlich prüfen, ob vorheriger Wert wesentlich kleiner war; 
            # nur großer Abtrag wird registriert
            # --> registriert plötzliche Ereignisse
            if((number_values_below/len(image))>=occurence_threshold and (number_values_below-number_values_below_old)/len(image)>=occurence_threshold/2):
                changepoints.append([imageindex, number_values_below-number_values_below_old])
                up = True            

            # register change point (DOWN)
            # --> filter out to short events 
            # ohne 564 changepoint Events
            if((number_values_below_old-number_values_below)/len(image)>=occurence_threshold/2 and up==True):
                if(imageindex - changepoints[-1][0] <= event_length_threshold):
                    changepoints.pop()
                up = False

            # filtern, wenn Anzahl wieder unter 0,1 geht
            if((number_values_below/len(image))<=occurence_threshold/2 and up==True):
                if(imageindex - changepoints[-1][0] <= event_length_threshold):
                    changepoints.pop()
                up = False

            number_values_below_old = number_values_below

        if(len(changepoints) == 1):
                # score ist Höhe des Sprunges * durchschnitt der werte nach dem ersten Changepoint
                score = changepoints[0][1] * statistics.mean(number_values_below_list[changepoints[0][0]:])  
                events.append([score, i,j, timestamps[changepoints[0][0]]])
        elif (changepoints): 
            pass
            # split at changepoints and score regions seperatly:
            for k in range(len(changepoints)-2):
                 # score ist Höhe des Sprunges * durchschnitt der werte nach dem ersten Changepoint
                score = changepoints[k][1] * statistics.mean(number_values_below_list[changepoints[k][0]:changepoints[k+1][0]])
                events.append([score, i,j, timestamps[changepoints[k][0]]])
        
        overall_changepoints += len(changepoints)
        # if(changepoints):

        #     # Klassifizierung 
        #     print(len(changepoints))      ## wenig changepoints im verhältnis zur Zeit: --> gutes Event            
        #     # Ausgabe Bereich und Zeitpunkt des ersten
        #     print(timestamps[changepoints[0][0]])      ## mehrer hintereinander mit gleichem Datum des ersten changepoint
        #     ## Punktesystem für Events
        #     # erstmal nur primäre Changepoints
        #     if(len(changepoints) == 1):
        #         # score ist Höhe des Sprunges * durchschnitt der werte nach dem ersten Changepoint
        #         score = changepoints[0][1] * statistics.mean(number_values_below_list[changepoints[0][0]:])  
        #         events.append([score, i,j, timestamps[changepoints[0][0]]])

        #     print(i,j)
        #     # durchschnitt der werte nach dem ersten Changepoint
        #     print(statistics.mean(number_values_below_list[changepoints[0][0]:]))    	    ## ab 0,26 signifikant
        #     # TODO: Tabellarische Ausgabe
        #     #plot_time_series(timestamps[timespan_start:timespan_end], number_values_below_list)


print(overall_changepoints)
events = np.array(events)
sorted_events = events[events[:,0].argsort()]
print(sorted_events[:,])



#### Ausgabe: Gravierendste Ereignisse --> weniger gravierenden Ereignissen
# --> Ereignis endet nicht













