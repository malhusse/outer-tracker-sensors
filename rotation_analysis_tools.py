import pandas as pd
import numpy as np
from scipy import stats
from math import atan
import seaborn as sns
import matplotlib.pyplot as plt

def read_and_clean(point):
    temp = pd.read_csv(point,  header=None, names = ['x','y','z','d'])
    temp = temp[temp.z != 0]
    temp = temp[temp.z < 97.0]
    temp = temp[~np.isinf(temp.d)]
    temp = temp.reset_index(drop=True)
    return temp

def reject_outliers(data, m=.15):
    temp = data
    temp = temp[abs(temp.d - np.mean(temp.d)) < m * np.std(temp.d)]
    temp = temp.reset_index(drop=True)
    return temp

def find_sensors_helper(data):
    data = data.reset_index(drop=True)
    minz = np.min(data.z)
    maxz = np.max(data.z)
    
    window_bounds = np.linspace(minz, maxz, int(np.ceil((maxz-minz)/0.016)))
    z_min = 0
    z_max = 0
    minimum_std = 99
    for i_min in range(len(window_bounds)-12):
        j = np.std(data[(data.z > window_bounds[i_min]) & (data.z < window_bounds[i_min+12])]["d"])
        if j < minimum_std:
            z_min = window_bounds[i_min]
            z_max = window_bounds[i_min+12]
            minimum_std = j
    sensor = data[(data.z > z_min) & (data.z < z_max)]
    sensor = sensor.reset_index(drop=True)
    return sensor

def find_sensors(data):
    topDF = data.iloc[:int(len(data)/2)]
    botDF = data.iloc[int(len(data)*3/4):]

    return find_sensors_helper(topDF), find_sensors_helper(botDF)
    
def calculate_rotation(point1_name, point2_name, point3_name, point4_name):
        
    point1 = read_and_clean(point1_name)
    point2 = read_and_clean(point2_name)
    point3 = read_and_clean(point3_name)
    point4 = read_and_clean(point4_name)
    
    p1dc1, p1dc2 = find_sensors(point1)
    p2dc1, p2dc2 = find_sensors(point2)
    p3dc1, p3dc2 = find_sensors(point3)
    p4dc1, p4dc2 = find_sensors(point4)

    y_top = [np.mean(p1dc1.y), np.mean(p2dc1.y), np.mean(p3dc1.y), np.mean(p4dc1.y)]
    d_top = [np.mean(p1dc1.d), np.mean(p2dc1.d), np.mean(p3dc1.d), np.mean(p4dc1.d)]

    y_bottom = [np.mean(p1dc2.y), np.mean(p2dc2.y), np.mean(p3dc2.y), np.mean(p4dc2.y)]
    d_bottom = [np.mean(p1dc2.d), np.mean(p2dc2.d), np.mean(p3dc2.d), np.mean(p4dc2.d)]

    offset = np.mean([x-y for x,y in zip(d_top,d_bottom)])
    
    top = stats.linregress(y_top,d_top)
    bot = stats.linregress(y_bottom,d_bottom)

    s1 = top.slope
    s2 = bot.slope
    
    angleMicroRads = atan((s1-s2)/(1+s1*s2)) * 10**6

    x = sns.regplot(x=y_top, y=d_top, label="Top Sensor, R^2 = {:.4f} \n Angle= {:.0f} μrad".format(top.rvalue**2,atan(top.slope)*1E6))
    x = sns.regplot(x=y_bottom,y=d_bottom, label="Bottom, R^2 = {:.4f} \n Angle= {:.0f} μrad".format(bot.rvalue**2,atan(bot.slope)*1E6))
    scan = point1_name.split("/")[1].split("_ScanPoint")[0]
    x.set_title("{}".format(scan.split("_")[0]))
    x.set(xlabel="Y (mm)", ylabel="D (mm)")
    plt.legend()
    fig = x.get_figure()
    fig.savefig("assets/fit_plots/{}_sensor_fits.svg".format(scan))
    fig.clear()

    return offset, angleMicroRads
