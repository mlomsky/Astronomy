import astropy.units as u
import numpy as np
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, solar_system, get_body


def check_sky_tonight(obj):
    sky_obj = SkyCoord.from_name(obj)
    my_house = EarthLocation(lat=41*u.deg, lon=-73*u.deg, height=85*u.m)
    utcoffset = -4*u.hour  # Eastern Daylight Time
    time = Time('2020-10-11 20:00:00') - utcoffset
    midnight = Time('2020-10-11 00:00:00') - utcoffset
    delta_midnight = np.linspace(-12, 12, 1000)*u.hour
    times_october = midnight + delta_midnight
    frame_october = AltAz(obstime=times_october, location=my_house)
    sky_objaltazs_october = sky_obj.transform_to(frame_october)

    for altaz in sky_objaltazs_october:
        altitude = altaz.alt
        (sign, d, m, s)  = altitude.signed_dms
        (zsign, zd, zm, zs) = altaz.az.signed_dms
        zstr = zsign + zd
        ohour = str(altaz.obstime)[11:13]
        omin = str(altaz.obstime)[14:16]
        if altitude.is_within_bounds(25 * u.deg, 90 * u.deg) and omin == '00':
            print("{3} - a:{0} z:{1} o:{2} - {4} - {5} - {6}".format(d, zstr, altaz.obstime, obj, d, ohour, omin))
        # if int(altitude) > 25:
        # print("a:{0} z:{1} o:{2}".format(altaz.alt, altaz.az, altaz.obstime))


def try_sat():
    # need to try to tune this for multiple planets and times
    midnight = Time('2020-10-11 00:00:00')
    saturn = get_body('saturn', midnight)
    my_house = EarthLocation(lat=41.16 * u.deg, lon=-73.42 * u.deg, height=85 * u.m)
    utcoffset = -4 * u.hour  # Eastern Daylight Time
    midnight = Time('2020-10-11 00:00:00') - utcoffset
    delta_midnight = np.linspace(-12, 12, 1000) * u.hour
    times_october = midnight + delta_midnight
    frame_october = AltAz(obstime=times_october, location=my_house)
    sky_objaltazs_october = saturn.transform_to(frame_october)
    for altaz in sky_objaltazs_october:
        altitude = altaz.alt
        (sign, d, m, s) = altitude.signed_dms
        (zsign, zd, zm, zs) = altaz.az.signed_dms
        zstr = zsign + zd
        ohour = str(altaz.obstime)[11:13]
        omin = str(altaz.obstime)[14:16]
        if altitude.is_within_bounds(25 * u.deg, 90 * u.deg) and omin == '00':
            print("{3} - a:{0} z:{1} o:{2} - {4} - {5} - {6}".format(d, zstr, altaz.obstime, 'saturn', d, ohour, omin))


def main():
    sky_objects = ['M5', 'M7', 'M33', 'M42']
    try_sat()
    for dso in sky_objects:
        check_sky_tonight(dso)


if __name__ == '__main__':
    main()
