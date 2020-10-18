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
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import datetime
from astropy.visualization import astropy_mpl_style, quantity_support
import matplotlib.pyplot as plt
from astropy.coordinates import get_sun
from astropy.coordinates import get_moon


class Mail:  # need to add lots of error checking in the functions here
    data = {}
    json_file_name = 'mail.json'
    mail_exists = True
    plot_exists = True
    sender_email_address = ''
    sender_email_password = ''
    receiver_email_address = ''
    port = 465
    marker = "Sun_Moon_Plot"
    encodedcontent = ''
    attachment_part = ''

    def __init__(self, plot_file_name):
        self.verify_json_exists()
        self.plot_file_name = plot_file_name
        if self.mail_exists:
            self.load_json()
            self.set_email_password()
            self.context = ssl.create_default_context()

    def send_email(self, html_msg, plain_msg):
        # create html message
        message = MIMEMultipart("related")
        message["Subject"] = "Astronomy Email"  # add infomation related to site and date
        message["From"] = self.sender_email_address
        message["To"] = self.receiver_email_address
        message.preamble = 'This is a multi-part message in MIME format.'
        msgAlternative = MIMEMultipart('alternative')
        message.attach(msgAlternative)
        part1 = MIMEText(plain_msg, "plain")
        part2 = MIMEText(html_msg, "html")
        message.attach(part1)
        msgAlternative.attach(part2)
        # Attach Plot if exists
        if self.plot_exists:
            msgText = MIMEText(html_msg, 'html')
            msgAlternative.attach(msgText)
            fo = open(self.plot_file_name, "rb")
            msgImage = MIMEImage(fo.read())
            fo.close()
            msgImage.add_header('Content-ID', '<{0}>'.format(self.plot_file_name))
            message.attach(msgImage)

        with smtplib.SMTP_SSL("smtp.gmail.com", self.port, context=self.context) as server:
            server.login(self.sender_email_address, self.sender_email_password)
            server.sendmail(self.sender_email_address, self.receiver_email_address, message.as_string())
            server.quit()

    def set_email_password(self):
        self.sender_email_address = self.data['sender_email']
        self.sender_email_password = self.data['sender_password']
        self.receiver_email_address = self.data['receiver_email']

    def verify_plot_exists(self):
        if not os.path.isfile(self.plot_file_name):
            print("Can not load Location file, {0}".format(self.plot_file_name))
            self.plot_exists = False

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
    planet_list = ['mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune']
    viewing_arr = []

    def __init__(self, lat, long, date, name, height):
        self.lat = lat
        self.long = long
        self.date = self.fix_date(date)
        self.site_name = name
        self.height = height
        self.viewing_location = EarthLocation(lat=self.lat * u.deg, lon=self.long * u.deg, height=self.height * u.m)
        self.utcoffset = -4 * u.hour  # Eastern Daylight Time
        self.viewing_date_midnight_time = self.date + ' 00:00:00'
        self.midnight = Time(self.viewing_date_midnight_time) - self.utcoffset
        self.delta_midnight = np.linspace(-6, 6, 500)*u.hour  # tune this to actual sunrise / sunset ... get that
        self.sun_moon_delta_midnight = np.linspace(-12, 12, 1000)*u.hour
        self.viewing_times = self.midnight + self.delta_midnight
        self.sun_moon_viewing_times = self.midnight + self.sun_moon_delta_midnight
        self.viewing_frame = AltAz(obstime=self.viewing_times, location=self.viewing_location)
        self.sun_moon_viewing_frame = AltAz(obstime=self.sun_moon_viewing_times, location=self.viewing_location)
        self.html = ''
        self.plot_file_name = 'sun_moon_plot.png'
        self.viewing_index = {}  # mon*10000+day*100+hour, dictionary index
        self.viewing_dictionary = {}  # key dictionary index, value html table line
        self.v_i_ctr = 0
        self.dusk = ''
        self.sunset = ''
        self.sunrise = ''
        self.dawn = ''
        self.half_dark_hours = 0

    def sort_data(self):
        viewing_copy = self.viewing_index
        self.viewing_arr = sorted((value, key) for (key, value) in viewing_copy.items())

    def set_html(self):
        for row in self.viewing_arr:
            self.html += self.viewing_dictionary[row[1]]
        self.html = html_header(self.site_name, self.date, self.plot_file_name) + self.html + html_footer()

    def adjust_delta_midnight(self):
        self.get_hours_sunset()
        if self.half_dark_hours != 0:
            self.delta_midnight = np.linspace(-self.half_dark_hours, self.half_dark_hours, 500) * u.hour

    def get_hours_sunset(self):
        midnight = datetime.datetime.strptime(self.viewing_date_midnight_time, '%Y-%m-%d %H:%M:%S')
        dusktime = datetime.datetime.strptime(self.date + ' ' + self.dusk +  ':00', '%Y-%m-%d %H:%M:%S')
        diff = midnight - dusktime
        self.half_dark_hours = round(diff.seconds/3600)

    def get_sunset(self, sunaltaz):
        # note hour is utc, not local
        last_alt = 0
        first = True
        for altaz in sunaltaz:
            if first:
                last_alt = altaz.alt
                first = False
            if altaz.alt.is_within_bounds(0 * u.deg, 1 * u.deg):
                ohour = int(str(altaz.obstime)[11:13]) - 4
                omin = str(altaz.obstime)[14:16]
                if last_alt > altaz.alt:
                    self.dusk = str(ohour) + ':' + omin
                else:
                    self.sunrise = str(ohour) + ':' + omin
            if altaz.alt.is_within_bounds(-20 * u.deg, -18 * u.deg):
                ohour = int(str(altaz.obstime)[11:13]) - 4
                omin = str(altaz.obstime)[14:16]
                if last_alt > altaz.alt:
                    self.sunset = str(ohour) + ':' + omin
                else:
                    self.dawn = str(ohour) + ':' + omin
            last_alt = altaz.alt

    def plot_sun_moon(self):
        plt.style.use(astropy_mpl_style)
        quantity_support()

        # Create Sun Moon Plot
        sunaltazs_viewing_date = get_sun(self.midnight).transform_to(self.sun_moon_viewing_frame)
        self.get_sunset(sunaltazs_viewing_date)
        moonaltazs_viewing_date = get_moon(self.midnight).transform_to(self.sun_moon_viewing_frame)
        plt.plot(self.sun_moon_delta_midnight, sunaltazs_viewing_date.alt, color='r', label='Sun')
        plt.plot(self.sun_moon_delta_midnight, moonaltazs_viewing_date.alt, color=[0.75] * 3, ls='--', label='Moon')
        plt.fill_between(self.sun_moon_delta_midnight, 0 * u.deg, 90 * u.deg,
                         sunaltazs_viewing_date.alt < -0 * u.deg, color='0.5', zorder=0)
        plt.fill_between(self.sun_moon_delta_midnight, 0 * u.deg, 90 * u.deg,
                         sunaltazs_viewing_date.alt < -18 * u.deg, color='k', zorder=0)
        plt.legend(loc='upper left')
        plt.xlim(-12 * u.hour, 12 * u.hour)
        plt.xticks((np.arange(13) * 2 - 12) * u.hour)
        plt.ylim(0 * u.deg, 90 * u.deg)
        plt.xlabel('Hours from EDT Midnight on {0}'.format(self.date))
        plt.ylabel('Altitude [deg]')
        plt.title('Sun and Moon plot for {0}'.format(self.site_name))
        plt.savefig(self.plot_file_name)

    def fix_date(self, date):
        # This function pushes the date forward 1 day to account for the fact that my calculations should be from
        # midnight on the date provided
        yr = int(date[0:4])
        m = int(date[5:7])
        d = int(date[8:10])
        return str(datetime.date(yr, m, d) + datetime.timedelta(1))

    def check_sky_tonight(self, obj):
        if obj in self.planet_list:
            midnight = Time(self.date + ' 00:00:00')
            sky_obj = get_body(obj, midnight)
        else:
            sky_obj = SkyCoord.from_name(obj)
        sky_objaltazs_viewing_date = sky_obj.transform_to(self.viewing_frame)

        last_hour = 999
        for altaz in sky_objaltazs_viewing_date: # need to parallelize this at some point
            altitude = altaz.alt
            (sign, d, m, s) = altitude.signed_dms
            (zsign, zd, zm, zs) = altaz.az.signed_dms
            zstr = zsign + zd
            ohour = str(altaz.obstime)[11:13]
            omin = str(altaz.obstime)[14:16]
            odate = str(altaz.obstime)[0:10]
            oday = str(altaz.obstime)[8:10]
            omon = str(altaz.obstime)[5:7]
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
                obs_date, obs_hour = un_utc(odate, ohour)
                table_row = "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}&#730;</td><td>{4}&#730;</td></tr>\n" \
                    .format(obj, obs_date, obs_hour, d, zstr)
                # mon*10000+day*100+hour
                key = int(omon)*10000 + int(oday)*100 + int(ohour)
                self.viewing_index[self.v_i_ctr] = key
                self.viewing_dictionary[self.v_i_ctr] = table_row
                self.v_i_ctr += 1

    def write_out_html(self):
        with open('astronomy_report.html', 'w') as f:
            print(self.html, file=f)

    def add_footer(self):
        self.html = html_header(self.site_name, self.date, self.plot_file_name) + self.html + html_footer()


def un_utc(date, hour):
    local_hour = int(hour) - 4
    if local_hour < 0:
        local_hour += 24
        yr = int(date[0:4])
        m = int(date[5:7])
        d = int(date[8:10])
        new_date = datetime.date(yr, m, d) - datetime.timedelta(1)
    else:
        new_date = date
    return str(new_date), local_hour


def html_footer():
    html_foot = "</table>\n</body>"
    return html_foot


def html_header(location_name, viewing_date, plot_file_name):
    html_head = "<html><head><title>Astronomy Email</title><style> table, th,\
      td {\
        padding: 10px;\
        border: 1px solid black;\
        border-collapse: collapse;\
      }\
    </style></head>\n<body>\n"  # add location specific information
    html_head += '<H1>Sun and Moon Plot </h1><br><img src="cid:{0}"><br>\n'.format(plot_file_name)
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
    # Plot Sun and Moon
    print("Plotting Sun and Moon")
    scan_sky.plot_sun_moon()
    scan_sky.adjust_delta_midnight()
    # Get data for Planets
    for planet in scan_sky.planet_list:
        print("Working on: {0}".format(planet))
        scan_sky.check_sky_tonight(planet)
    # Get data for Target group
    if 'target_group' in viewing_targets.data:
        if viewing_targets.data["target_group"] == "messier":
            for m_num in range(1,scan_sky.messier_max):
                m_id = "m" + str(m_num)
                print("Working on: {0}".format(m_id))
                scan_sky.check_sky_tonight(m_id)
                if m_num > 3:
                    # break
                    pass
                 #   sys.exit()
    # Sort The found data
    scan_sky.sort_data()
    scan_sky.set_html()
    # Print out Results
    print("Printing Out Results")
    scan_sky.write_out_html()
    # Send email if the mail JSON file is present
    print("Sending Email")
    email = Mail(scan_sky.plot_file_name)
    # if email.mail_exists:
        # email.send_email(scan_sky.html, "see html version")
    # need to check API for caldwell list objects and other lists
    # for dso in viewing_targets.data["target_list"]:
        # scan_sky.check_sky_tonight(dso)


if __name__ == '__main__':
    main()
