import numpy as np
#import cv2
from matplotlib import pyplot as plt

from setuptools import setup

setup()

data_folder= "/home/adrian/Dokumente/PhotogrammetrieKP/"

with np.load(data_folder+'4dfilt.npy') as data:
    plt.plot(data)
    plt.show()