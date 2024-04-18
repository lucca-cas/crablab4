import ugradio
import snap_spec
import sdr 
import numpy as np
import matplotlib.pyplot as plt
import astropy
from astropy.coordinates import SkyCoord
import time
from scipy.optimize import curve_fit
from scipy.optimize import leastsq
import glob
import argparse 
parser = argparse.ArgumentParser()
parser.add_argument('--filename', '-n', help='name to give file')
parser.add_argument('--LO', '-l', help='value of LO')

#parser to name files more conviniently
args = parser.parse_args()
file = args.filename
lo = float(args.LO)
#record_time = float(args.record_time)

#set the LO 
ag = ugradio.agilent.SynthClient() 
ag.set_frequency(lo)

#initialize the sdr object
sdr0 = ugradio.sdr.SDR(device_index=0, direct = False, center_freq = 1420e6, sample_rate = 3.2e6)
sdr1 = ugradio.sdr.SDR(device_index=1, direct = False, center_freq = 1420e6, sample_rate = 3.2e6)

#general process maybe
#convert galactic lingitudes to topocentric coordinates
#point the leusch 
#take the data 
#fft and square and average to get power spectrum 
#time.sleep(440)   tell the guy to chill for 440 secs idk cos max slew time is 220 secs which is rlly slow
#and then start pointing again ig 

# lat, lon and alt for leushcner
lat = 37.9183
lon = -122.1067
alt = 304. # m

#to get power spec 
def fft(signal):
	return np.fft.fft(signal)
	
def perform_power(signal):
	return np.abs((signal))**2
	
def shift(signal):
	return np.fft.fftshift(signal)
	
# -----------------------------------------
# -----------------------------------------
freqs = np.fft.fftshift(np.fft.fftfreq(1024, 1/3.2))

def power(collection_run, LO): 
    collection_run = collection_run - np.mean(collection_run)
    
    
    signal_agg = collection_run[...,0]+1j*collection_run[...,1]
    
    
    #signal_agg_final = signal_agg - np.mean(signal_agg)
    pwr = shift(np.mean(perform_power(fft(signal_agg)), axis=0))
    
    return pwr


#now pls lets start 
gal_lat = 0 
start_lon = -10 
end_lon = 250  #everything is in galactic coords 

#declare the dish object now
dish = ugradio.leusch.LeuschTelescope()

#this is an array of all of the different longitudes in galactic coords
g_lons = np.arange(-10, 252, 2)

#now lets try pointing and stuff 

#lets start our list of data values ig
spec = []


count = 0

for i in g_lons:
	count += 1
	s_galactic = SkyCoord(l= i, b=0, frame = 'galactic', unit='deg')
    s_topo = s_galactic.transform_to('icrs')
    alt, az = ugradio.get_altaz(ra = s_topo.ra, dec= s_topo.dec, jd = ugradio.julian_date(), lat = lat, lon = lon, alt = alt)

    #now we can point the big boi to the given alt az 
	dish.point(alt, az)

    #lets get the data and then make them power specs 
    data = ugradio.sdr.capture_data([sdr0, sdr1], 1024, 10000)

    first = power(data[sdr0], lo)
    second = power(data[sdr1], lo)
    spec = np.append(spec, [first, second])

    #now lets try to save the data 
	
    np.savez(f'{file}point{count}', data = spec)
    time.sleep(440)
# l is longitiude and b is latitude 