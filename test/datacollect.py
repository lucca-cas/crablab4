import ugradio
import snap_spec
from ugradio import sdr 
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
ag.set_frequency(lo, 'MHz')

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
s_galactics = [SkyCoord(l= i, b=0, frame = 'galactic', unit='deg') for i in g_lons]
s_topos = [s.transform_to('icrs') for s in s_galactics]

alts = []
azs =[]

for i in s_topos:
    alt, az = ugradio.coord.get_altaz(ra = i.ra, dec= i.dec, jd = ugradio.timing.julian_date(), lat = lat, lon = lon, alt = alt)
    if 15 < alt <85 and 5 < az < 350:
        alts.append(alt)
        azs.append(az)


#now lets try pointing and stuff 

#lets start our list of data values ig
spec = []


count = 0

for i in np.arange(72):
    count += 1

    #now we can point the big boi to the given alt az 
    dish.point(alts[i], azs[i])
    print("I do be pointing")

    #lets get the data and then make them power specs 
    data = ugradio.sdr.capture_data([sdr0, sdr1], 1024, 10000)

    first = power(data['sdr0'], lo)
    second = power(data['sdr1'], lo)
    spec = np.append(spec, [first, second])

    #now lets try to save the data 
	
    np.savez(f'{file}point{count}', data = spec)
    time.sleep(440)
# l is longitiude and b is latitude 
