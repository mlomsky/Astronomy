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
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class Mail:  # need to add lots of error checking in the functions here
    data = {}
    json_file_name = 'location.json'
    mail_exists = True
    sender_email_address = ''
    sender_email_password = ''
    receiver_email_address = ''
    port = 465

    def __init__(self):
        self.verify_json_exists()
        if self.mail_exists:
            self.load_json()
            self.set_email_password()
            self.context = ssl.create_default_context()

    def send_email(self, html_msg, plain_msg):
        # create html message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Astronomy Email"  # add infomation related to site and date
        message["From"] = self.sender_email_address
        message["To"] = self.receiver_email_address
        part1 = MIMEText(plain_msg, "plain")
        part2 = MIMEText(html_msg, "html")
        message.attach(part1)
        message.attach(part2)

        with smtplib.SMTP_SSL("smtp.gmail.com", self.port, context=self.context) as server:
            server.login(self.sender_email_address, self.sender_email_password)
        server.sendmail(self.sender_email_address, self.receiver_email_address, message.as_string())

    def set_email_password(self):
        self.sender_email_address = self.data['sender_email']
        self.sender_email_password = self.data['sender_password']
        self.receiver_email_address = self.data['receiver_email']

    def verify_json_exists(self):
        if not os.path.isfile(self.json_file_name):
            print("Can not load Location file, {0}".format(self.json_file_name))
            self.mail_exists = False

    def load_json(self):
        with open(self.json_file_name, 'r') as loc_json_file:
            self.data = json.load(loc_json_file)


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
        self.delta_midnight = np.linspace(-6, 6, 500)*u.hour  # tune this to actual sunrise / sunset ... get that
        self.viewing_times = self.midnight + self.delta_midnight
        self.viewing_frame = AltAz(obstime=self.viewing_times, location=self.viewing_location)
        self.html = html_header(self.site_name, self.date)

    def check_sky_tonight(self, obj):
        sky_obj = SkyCoord.from_name(obj)
        sky_objaltazs_viewing_date = sky_obj.transform_to(self.viewing_frame)

        last_hour = 999
        for altaz in sky_objaltazs_viewing_date: # need to parallelize this at some point
            altitude = altaz.alt
            (sign, d, m, s)  = altitude.signed_dms
            (zsign, zd, zm, zs) = altaz.az.signed_dms
            zstr = zsign + zd
            ohour = str(altaz.obstime)[11:13]   #  obs_time is in utc ... need to adjust that with utc ofset date and time
            omin = str(altaz.obstime)[14:16]
            odate = str(altaz.obstime)[0:10]
            # need to modify code here to limit to dark hours on day
            # possible enhancement to make code use times of sun to know when dark
            skip_print = True
            if 0 <= int(omin) < 5:
                if ohour == last_hour:
                    skip_print = True
                else:
                    skip_print = False
            else:
                skip_print = True
            last_hour = ohour
            if altitude.is_within_bounds(20 * u.deg, 90 * u.deg) and not skip_print:
                self.html += "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}&#730;</td><td>{4}&#730;</td></tr>\n"\
                    .format(obj, odate, ohour, d, zstr)
                print("{3} - a:{0} z:{1} o:{2} - {4} - {5} - {6}".format(d, zstr, altaz.obstime, obj, d, ohour, omin))
                # make html report for this


    def write_out_html(self):
        with open('astronomy_report.html', 'w') as f:
            print(self.html, file=f)

    def add_footer(self):
        self.html += html_footer()


def html_footer():
    html_foot = "</table>\n</body>"
    return html_foot


def html_header(location_name, viewing_date):
    html_head = "<html><head><title>Astronomy Email</title><style> table, th,\
      td {\
        padding: 10px;\
        border: 1px solid black;\
        border-collapse: collapse;\
      }\
    </style></head>\n<body>\n"  # add location specific information
    html_head += "<h1>Viewing Items for {0} on {1}</h1>\n".format(location_name, viewing_date)
    html_head += "<table>\n"
    html_head += "<tr><td><b>Object</b></td><td><b>Date</b></td><td><b>Hour</b></td><td><b>Altitude</b></td>" \
                 "<td><b>Azimuth</b></td></tr>\n"
    return html_head


def main():
    # Load JSON data
    viewing_location = Location()
    viewing_targets = Targets()

    # Maybe add here get sun data and when sun alt < 0 degrees
    # use that to limit check sky to only those dark hours and mark twilight hours
    # to viewing program
    scan_sky = Viewing(viewing_location.data["lat"], viewing_location.data["long"],
                       viewing_location.data["viewing_date"], viewing_location.data["name"],
                       viewing_location.data["height"])

    if 'target_group' in viewing_targets.data:
        if viewing_targets.data["target_group"] == "messier":
            for m_num in range(1,scan_sky.messier_max):
                m_id = "m" + str(m_num)
                scan_sky.check_sky_tonight(m_id)
                if m_num > 1:
                    sys.exit()

    scan_sky.add_footer()
    scan_sky.write_out_html()
    # need to check API for caldwell list objects and other lists
    # for dso in viewing_targets.data["target_list"]:
        # scan_sky.check_sky_tonight(dso)


if __name__ == '__main__':
    main()
