# this is a scratch program to experiment with, and learn from the basic techniques shown on
# https://docs.astropy.org/en/stable/generated/examples/coordinates/plot_obs-planning.html

import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz


m33 = SkyCoord.from_name('M33')
bear_mountain = EarthLocation(lat=41.3*u.deg, lon=-74*u.deg, height=390*u.m)
my_house = EarthLocation(lat=41*u.deg, lon=-73*u.deg, height=85*u.m)
utcoffset = -4*u.hour  # Eastern Daylight Time
time = Time('2020-10-11 20:00:00') - utcoffset
m33altaz = m33.transform_to(AltAz(obstime=time,location=my_house))
print("M33's Altitude = {0.alt:.2}".format(m33altaz))


# Find the alt,az coordinates of M33 at 100 times evenly spaced between 10pm and 7am EDT:
import numpy as np
import matplotlib.pyplot as plt
from astropy.visualization import astropy_mpl_style, quantity_support
plt.style.use(astropy_mpl_style)
quantity_support()
# Use get_sun to find the location of the Sun at 1000 evenly spaced times between noon on July 12 and noon on July 13:

from astropy.coordinates import get_sun
midnight = Time('2020-10-11 00:00:00') - utcoffset
delta_midnight = np.linspace(-12, 12, 1000)*u.hour
times_July12_to_13 = midnight + delta_midnight
times_october = midnight + delta_midnight
frame_July12_to_13 = AltAz(obstime=times_July12_to_13, location=bear_mountain)
frame_october = AltAz(obstime=times_october, location=my_house)
sunaltazs_July12_to_13 = get_sun(times_october).transform_to(frame_october)
sunaltazs_october = get_sun(times_July12_to_13).transform_to(frame_July12_to_13)

# Do the same with get_moon to find when the moon is up. Be aware that this will need to download a 10MB file
# from the internet to get a precise location of the moon.

from astropy.coordinates import get_moon
moon_July12_to_13 = get_moon(times_July12_to_13)
moonaltazs_July12_to_13 = moon_July12_to_13.transform_to(frame_July12_to_13)
moon_october = get_moon(times_october)
moonaltazs_october = moon_october.transform_to(frame_october)
# Find the alt,az coordinates of M33 at those same times:

m33altazs_July12_to_13 = m33.transform_to(frame_July12_to_13)
m33altazs_october = m33.transform_to(frame_october)
for altaz in m33altazs_october:
    print("a:{0} z:{1} o:{2}".format(altaz.alt, altaz.az, altaz.obstime))
# Make a beautiful figure illustrating nighttime and the altitudes of M33 and the Sun over that time:

plt.plot(delta_midnight, sunaltazs_october.alt, color='r', label='Sun')
plt.plot(delta_midnight, moonaltazs_october.alt, color=[0.75]*3, ls='--', label='Moon')
plt.scatter(delta_midnight, m33altazs_october.alt,
            c=m33altazs_october.az, label='M33', lw=0, s=8,
            cmap='viridis')
plt.fill_between(delta_midnight, 0*u.deg, 90*u.deg,
                 sunaltazs_october.alt < -0*u.deg, color='0.5', zorder=0)
plt.fill_between(delta_midnight, 0*u.deg, 90*u.deg,
                 sunaltazs_october.alt < -18*u.deg, color='k', zorder=0)
plt.colorbar().set_label('Azimuth [deg]')
plt.legend(loc='upper left')
plt.xlim(-12*u.hour, 12*u.hour)
plt.xticks((np.arange(13)*2-12)*u.hour)
plt.ylim(0*u.deg, 90*u.deg)
plt.xlabel('Hours from EDT Midnight')
plt.ylabel('Altitude [deg]')
plt.show()