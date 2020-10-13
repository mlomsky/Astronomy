# Viewing Tonight Program
# #### Basic program
# * command line location and object
# * return AltAZ table at a few key times in HTML document
#     * key times meaning +10deg above horizon, 30deg, 45deg
#     * altitude at key times??
# * email document option
#
# program steps
# make json file to store location viewing date email address
# parse json
# make json to show target list
# parse json
# default viewing session from 7pm to 7am
# show alt az hourly for all targets in above 20alt
# print out html and email to email address
# add image of sun and moon to show when they will impact

import json
import os.path
import sys
import astropy.units as u
import numpy as np
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, solar_system, get_body

class Location:
    data = {}
    json_file_name = 'location.json'

    def __init__(self):
        self.verify_json_exists()
        self.load_json()

    def verify_json_exists(self):
        if not os.path.isfile(self.json_file_name):
            print("Can not load Location file, {0}".format(self.json_file_name))
            sys.exit("Program is existing")

    def load_json(self):
        with open(self.json_file_name, 'r') as loc_json_file:
            self.data = json.load(loc_json_file)


class Targets:
    data = {}
    json_file_name = 'viewing_targets.json'

    def __init__(self):
        self.load_json()

    def verify_json_exists(self):
        if not os.path.isfile(self.json_file_name):
            print("Can not load Targets file, {0}".format(self.json_file_name))
            sys.exit("Program is existing")

    def load_json(self):
        with open(self.json_file_name, 'r') as loc_json_file:
            self.data = json.load(loc_json_file)


class Viewing:
    messier_max = 110

    def __init__(self, lat, long, date, name, height):
        self.lat = lat
        self.long = long
        self.date = date
        self.site_name = name
        self.height = height
        self.viewing_location = EarthLocation(lat=self.lat * u.deg, lon=self.long * u.deg, height=self.height * u.m)
        self.utcoffset = -4 * u.hour  # Eastern Daylight Time
        self.viewing_date_midnight_time = self.date + ' 00:00:00'
        self.midnight = Time(self.viewing_date_midnight_time) - self.utcoffset
        self.delta_midnight = np.linspace(-12, 12, 1000)*u.hour
        self.viewing_times = self.midnight + self.delta_midnight
        self.viewing_frame = AltAz(obstime=self.viewing_times, location=self.viewing_location)

    def check_sky_tonight(self, obj):
        sky_obj = SkyCoord.from_name(obj)
        sky_objaltazs_viewing_date = sky_obj.transform_to(self.viewing_frame)

        for altaz in sky_objaltazs_viewing_date:
            altitude = altaz.alt
            (sign, d, m, s)  = altitude.signed_dms
            (zsign, zd, zm, zs) = altaz.az.signed_dms
            zstr = zsign + zd
            ohour = str(altaz.obstime)[11:13]
            omin = str(altaz.obstime)[14:16]
            if altitude.is_within_bounds(25 * u.deg, 90 * u.deg) and omin == '00':
                print("{3} - a:{0} z:{1} o:{2} - {4} - {5} - {6}".format(d, zstr, altaz.obstime, obj, d, ohour, omin))


def main():
    # Load JSON data
    viewing_location = Location()
    viewing_targets = Targets()

    # try viewing program
    scan_sky = Viewing(viewing_location.data["lat"], viewing_location.data["long"],
                       viewing_location.data["viewing_date"], viewing_location.data["name"],
                       viewing_location.data["height"])

    if 'target_group' in viewing_targets.data:
        if viewing_targets.data["target_group"] == "messier":
            for m_num in range(1,scan_sky.messier_max):
                m_id = "m" + str(m_num)
                scan_sky.check_sky_tonight(m_id)

    # for dso in viewing_targets.data["target_list"]:
        # scan_sky.check_sky_tonight(dso)


if __name__ == '__main__':
    main()
