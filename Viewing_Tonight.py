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
import astropy
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
from astropy.coordinates import get_body
from PyAstronomy import pyasl # Using this to get Lunar Phase
from Messier import Messier
from collections import defaultdict
import pdfkit
import time
import threading
import multiprocessing
import PySimpleGUI as sg
from geopy.geocoders import Nominatim
import requests
import pandas as pd


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
        print("\n\nRunning for " + self.data["name"] + " on " + self.data["viewing_date"])

    def verify_json_exists(self):
        if not os.path.isfile(self.json_file_name):
            print("Can not load Location file, {0}".format(self.json_file_name))
            sys.exit("Program is existing")

    def load_json(self):
        with open(self.json_file_name, 'r') as loc_json_file:
            self.data = json.load(loc_json_file)


class UserDataApp:
    def __init__(self):
        sg.theme('dark grey 9')
        self.layout = [
            [sg.Text('Name:'), sg.Input(key='name')],
            [sg.Text('Address:'), sg.Input(key='address')],
            [sg.Text('City:'), sg.Input(key='city')],
            [sg.Text('State:'), sg.Input(key='state')],
            [sg.Button('Save Location'), sg.Button('Load Location'), sg.Button('Exit')]
        ]
        self.window = sg.Window('User Information', self.layout)
        self.folder_path = 'user_data_folder'  # Subfolder name
        self.geolocator = Nominatim(user_agent='user_data_app')
        self.user_data = {}

    def create_subfolder(self):
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)

    def get_coordinates(self, address):
        location = self.geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None

    def read_json_data(self):
        # please note I know I am recaculating the lat and long here, but I am doing it in case the data changes. 
        # this may be dumb, but I am tired and it makes sense to me right now.
        # suspect I will chnage this later
        filenames = os.listdir(self.folder_path)
        if filenames:
            selected_file = sg.popup_get_file('Choose a file to read data', file_types=(("JSON Files", "*.json"),), initial_folder=self.folder_path)
            if selected_file:
                try:
                    with open(selected_file, 'r') as json_file:
                        self.user_data = json.load(json_file)
                        self.window['name'].update(self.user_data.get('name', ''))
                        self.window['address'].update(self.user_data.get('address', ''))
                        self.window['city'].update(self.user_data.get('city', ''))
                        self.window['state'].update(self.user_data.get('state', ''))
                        geo_locate = self.user_data['address'] + ', ' + self.user_data['city'] + ', ' + self.user_data['state']
                        lat, lon = self.get_coordinates(geo_locate) # these next 3 lines should be cleaned up... tired now later...
                        self.user_data['latitude'] = lat
                        self.user_data['longitude'] = lon
                        sg.popup(f'Data loaded successfully!  Lat:{lat} long:{lon}', title='Success')
                except FileNotFoundError:
                    sg.popup_error(f'Error reading data from {selected_file}', title='Error')
        else:
            sg.popup_error('No existing JSON files found in the subfolder!', title='Error')

    def run(self):
        self.create_subfolder()
        while True:
            event, values = self.window.read()
            if event == sg.WINDOW_CLOSED or event == 'Exit':
                break
            elif event == 'Save Location':
                filename = sg.popup_get_file('Choose a file to save data', save_as=True, initial_folder=self.folder_path)
                if filename:
                    # Collect user input
                    self.user_data = {
                        'name': values['name'],
                        'address': values['address'],
                        'city': values['city'],
                        'state': values['state'],
                        'latitude': '',
                        'longitude': ''
                    }
                    geo_locate = self.user_data['address'] + ', ' + self.user_data['city'] + ', ' + self.user_data['state']
                    lat, lon = self.get_coordinates(geo_locate) # again need to clean up the next 3 lines but want to finish my idea first
                    self.user_data['latitude'] = lat
                    self.user_data['longitude'] = lon
                    # Write data to a JSON file
                    with open(filename, 'w') as json_file:
                        json.dump(self.user_data, json_file, indent=4)

                        sg.popup(f'Data saved successfully in {filename}!', title='Success')
            elif event == 'Load Location':
                self.read_json_data()

        self.window.close()
        


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


class Timing:
    start_time = time.time()
    end_time = time.time()
    elapsed_time = ''

    def __init__(self, label):
        self.start_time = time.time()
        self.label = label

    def end_now(self):
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time

    def print_delta(self):
        print(f"{self.label} Elapsed time: {self.elapsed_time:.2f} seconds")


class Viewing:
    messier_max = 110
    planet_list = ['mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune']
    viewing_arr = []

    def __init__(self, location_lat, location_long, location_name):
        # Load JSON data
        viewing_location = Location()
        date = viewing_location.data["viewing_date"]

        self.lat = location_lat
        self.long = location_long
        self.date = self.fix_date(date)
        self.file_date = date
        self.moon_phase_pct = get_lunar_phase(self.date)
        self.viewing_date_evening = str(datetime.date(int(date[0:4]), int(date[5:7]), int(date[8:10])))
        self.site_name = location_name
        self.site_file_name = self.site_name.replace(' ', '-')
        self.height = get_elevation_in_feet(location_lat, location_long)
        self.viewing_location = EarthLocation(lat=self.lat * u.deg, lon=self.long * u.deg, height=self.height * u.m)
        self.utcoffset_int = -4  # need to make this loadable from the viewing location
        self.utcoffset = self.utcoffset_int * u.hour  # Eastern Daylight Time
        self.viewing_date_midnight_time = self.date + ' 00:00:00'
        self.midnight = Time(self.viewing_date_midnight_time) - self.utcoffset
        self.delta_midnight = np.linspace(-6, 6, 500) * u.hour  # this is the default value that is tuned later
        self.sun_moon_delta_midnight = np.linspace(-12, 12, 1000) * u.hour
        self.viewing_times = self.midnight + self.delta_midnight
        self.sun_moon_viewing_times = self.midnight + self.sun_moon_delta_midnight
        self.viewing_frame = AltAz(obstime=self.viewing_times, location=self.viewing_location)
        self.sun_moon_viewing_frame = AltAz(obstime=self.sun_moon_viewing_times, location=self.viewing_location)
        self.html = ''
        self.html_summary = ''
        self.plot_file_name = 'sun_moon_plot' + self.date + self.site_file_name + '.png'
        self.viewing_index = {}  # mon*10000+day*100+hour, dictionary index
        self.viewing_dictionary = {}  # key dictionary index, value html table line
        self.viewing_summary_dictionary = {}  # key dictionary index, value html table line
        self.v_i_ctr = 0
        self.dusk = ''
        self.sunset = ''
        self.sunrise = ''
        self.dawn = ''
        self.half_dark_hours = 0
        self.viewing_summary_dictionary = defaultdict(dict)  # calculate general info for summary view
        self.summary_page_information = self.set_summary_page_information()
        self.summary_filename = self.file_date + '_' + self.site_name.replace(' ', '_') + '_' +\
                                'astronomy_report_summary.html'
        self.summary_pdf_filename = 'astronomy_report_summary' + self.file_date + self.site_file_name + '.pdf'
        self.my_messier = Messier.MessierData()

    def set_summary_page_information(self):
        pageinfo = """<h2> What is this page for?</h2>
        The information on this page is intended to help you plan your observing session for the date
         shown at the top of this page by providing a list of objects which will be visible in the sky over the course
        of the evening.  The information provided here is applicable to the location shown at the very top of this page.
        <br>
        <h3>How to read the chart to the left </h3>
        <ul>
        <li>The time axis at the bottom of the chart presents midnight as 0. </li>
        <li>The red line indicates the sun’s altitude over the course of the charted period.  Sunset (left) and sunrise 
        (right) occur at the two points where the red line touches the bottom of the chart.</li>
        <li>The grey shaded areas on the chart indicate twilight periods.  These are the periods when the sun continues
         to illuminate sky after sunset or begins illuminating the sky before sunrise.</li>
        <li>The grey dashed line indicates the moon’s altitude over the course of the charted period.  The current 
        amount of lunar illumination is displayed as a percentage above the chart, with 0% indicating new moon, and 
        100% indicating a full moon. </li>
        <li>Ideal conditions for observing deep sky objects will most commonly take place during the period indicated 
        by the black portion of the chart and with as little moon as possible.</li>
        </ul>
        <h2>What is the table below for?</h2>
        The table below displays a list of planets and Messier objects which will be above the horizon between sunset 
        and sunrise. 
        <h3>Below Table Column Explanation</h3>
        <ul>
        <li><b>Rise Hour</b> indicates the earliest time at which the object may be observed.  The earliest time indicated by
         the Rise Hour column will be sunset; this is because you (typically) won't be able to see the object earlier
         than sundown.</li> 
        <li><b>Set Hour</b> indicates the latest time at which the object may be observed.  The latest time indicated by
         the Set Hour column will be sunrise; this is because you (typically) will no longer be able to see the object 
         after sunrise.</li> 
        <li><b>Max Altitude</b> provides the time at which the object will be highest in the sky and how high it will be at
         that time. </li>  
        <li><b>Finder Chart</b> contains a link to a star map to help you know what stars are near the object. </li>
        <li><b>Suggested Filter</b> contains information regarding the filter(s) we believe will help reveal the most 
         detail for an object, but this can be rather subjective.  Brighter objects typically do not require a filter.  
         Fainter objects may be observed without a filter in ideal conditions, but the right filter can often bring 
         out additional detail, especially when observing from light-polluted locations.</li>
         </ul>"""

        return pageinfo

    def sort_data(self):
        viewing_copy = self.viewing_index
        self.viewing_arr = sorted((value, key) for (key, value) in viewing_copy.items())

    def set_html(self):
        last_hour = -1
        for row in self.viewing_arr:
            if 0 < (row[0] % 100) + self.utcoffset_int < 25:
                hour = (row[0] % 100) + self.utcoffset_int
            elif ((row[0] % 100) + self.utcoffset_int) < 0:
                hour = (row[0] % 100) + self.utcoffset_int + 24
            else:
                hour = (row[0] % 100) + self.utcoffset_int
            if hour != last_hour:
                last_hour = hour
                self.html += "<tr><td><a href=\"#top\">Top</td><td colspan=7><a id=\"{0}\">Viewing hour starting at" \
                             " {0}</a> </td></tr>".format(hour)
                self.html += header_row()
            self.html += self.viewing_dictionary[row[1]]
        self.html = html_header(self.site_name, self.viewing_date_evening, self.plot_file_name, self.half_dark_hours) \
                    + self.html + html_footer()

    def adjust_delta_midnight(self):
        self.get_hours_sunset()
        if self.half_dark_hours != 0:
            self.delta_midnight = np.linspace(-self.half_dark_hours, self.half_dark_hours, 500) * u.hour

    def get_hours_sunset(self):
        midnight = datetime.datetime.strptime(self.viewing_date_midnight_time, '%Y-%m-%d %H:%M:%S')
        if int(self.dusk[1:2]) < 0:
            self.dusk = str(24 + int(self.dusk))
        dusktime = datetime.datetime.strptime(self.date + ' ' + self.dusk + ':00', '%Y-%m-%d %H:%M:%S')
        diff = midnight - dusktime
        self.half_dark_hours = round(diff.seconds / 3600)

    def get_sunset(self, sunaltaz):
        # note hour is utc, not local
        from dateutil import tz
        from datetime import datetime
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('America/New_York')
        last_alt = 0
        for altaz in sunaltaz:
            if altaz.alt.is_within_bounds(0 * u.deg, 1 * u.deg):
                utc = datetime.strptime(str(altaz.obstime), '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=from_zone)
                ny_zone = utc.astimezone(to_zone)
                time = str(ny_zone)[11:16]
                date = str(ny_zone)[0:10]
                if last_alt > altaz.alt:
                    self.dusk = time
                    self.date = date
                else:
                    self.sunrise = time
                    self.date = date
            elif altaz.alt.is_within_bounds(-20 * u.deg, -18 * u.deg):
                utc = datetime.strptime(str(altaz.obstime), '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=from_zone)
                ny_zone = utc.astimezone(to_zone)
                time = str(ny_zone)[11:16]
                date = str(ny_zone)[0:10]
                if last_alt > altaz.alt:
                    self.sunset = time
                    self.date = date
                else:
                    self.dawn = time
                    self.date = date
            last_alt = altaz.alt

    def plot_sun_moon(self):
        plt.style.use(astropy_mpl_style)
        quantity_support()

        # Create Sun Moon Plot
        sunaltazs_viewing_date = get_sun(self.midnight).transform_to(self.sun_moon_viewing_frame)
        moonaltazs = get_body("moon", self.sun_moon_viewing_times).transform_to(self.sun_moon_viewing_frame)

        plt.plot(self.sun_moon_delta_midnight, moonaltazs.alt, '--', color='gray', label='Moon')
        plt.plot(self.sun_moon_delta_midnight, sunaltazs_viewing_date.alt, color='red', label='Sun')
        plt.fill_between(self.sun_moon_delta_midnight, 0 * u.deg, 90 * u.deg,
                         sunaltazs_viewing_date.alt < -0 * u.deg, color='gray', alpha=0.5, zorder=0)
        plt.fill_between(self.sun_moon_delta_midnight, 0 * u.deg, 90 * u.deg,
                         sunaltazs_viewing_date.alt < -18 * u.deg, color='black', alpha=0.5, zorder=0)
        plt.legend(loc='upper left')
        plt.xlim(-12 * u.hour, 12 * u.hour)
        plt.xticks((np.arange(13) * 2 - 12) * u.hour)
        plt.ylim(0 * u.deg, 90 * u.deg)
        plt.xlabel(f'Hours from Midnight on {self.date}')
        plt.ylabel('Altitude [deg]')
        plt.title(f'Sun & Moon Details at {self.site_name} with {self.moon_phase_pct}% Moon')
        plt.savefig(self.plot_file_name)
        self.get_sunset(sunaltazs_viewing_date)

    def fix_date(self, date):
        # This function pushes the date forward 1 day to account for the fact that my calculations should be from
        # midnight on the date provided
        yr = int(date[0:4])
        m = int(date[5:7])
        d = int(date[8:10])
        return str(datetime.date(yr, m, d) + datetime.timedelta(1))

    def check_sky_tonight(self, obj):
        # Set summary base values for object
        self.viewing_summary_dictionary[obj] = {"rise": 999, "set": 0, "max_az": 0}

        # Move on to the calculation
        check_time = Timing('check time')
        if obj in self.planet_list:
            sky_obj = get_body(obj, Time(self.date + ' 00:00:00'))
        else:
            sky_obj = SkyCoord.from_name(obj)
        sky_objaltazs_viewing_date = sky_obj.transform_to(self.viewing_frame)

        last_hour = 999
        for altaz in sky_objaltazs_viewing_date:  # need to parallelize this at some point
            altitude = altaz.alt
            (sign, d, m, s) = altitude.signed_dms
            (zsign, zd, zm, zs) = altaz.az.signed_dms
            zstr = zsign + zd
            ohour, omin, odate, oday, omon = str(altaz.obstime)[11:13], str(altaz.obstime)[14:16], str(altaz.obstime)[0:10], str(altaz.obstime)[8:10], str(altaz.obstime)[5:7]

            object_type = 'Planet'
            suggested_filters = ''
            finder_link = ''
            difficulty_html = ''
            if obj not in self.planet_list:
                object_type = self.my_messier.object_type[obj]
                finder_link = f'<a href="https://freestarcharts.com/images/Articles/Messier/Single/{obj.upper()}_Finder_Chart.pdf" target="_blank">Finder Chart</a>'
                suggested_filters = self.my_messier.messier_filters.get(obj, '')
                difficulty = self.my_messier.messier_difficulty.get(obj, '')
                difficulty_html = f'<span class="dot{"green" if difficulty == "easy" else "orange" if difficulty == "medium" else "red"}"></span>' if difficulty else ''


            skip_print = not (0 <= int(omin) < 5 and ohour != last_hour)
            last_hour = ohour
            if altitude.is_within_bounds(20 * u.deg, 90 * u.deg) and not skip_print:
                obs_date, obs_hour = un_utc(odate, ohour)
                tr_bgclr = "#d5f5e3" if int(ohour) % 2 == 0 else "#d6eaf8"
                compass = return_sector(zstr)
                direction = f'{zstr} - {compass}'
                table_row = f'<tr bgcolor="{tr_bgclr}"><td>{obj.upper()}</td><td>{object_type}</td><td>{obs_date}</td><td>{obs_hour}</td><td>{d}&#730;</td><td>{direction}&#730;</td><td>{suggested_filters}</td><td>{finder_link}</td></tr>\n'
                key = int(omon) * 10000 + int(oday) * 100 + int(ohour)
                self.viewing_index[self.v_i_ctr] = key
                self.viewing_dictionary[self.v_i_ctr] = table_row
                # Set summary info
                summary = self.viewing_summary_dictionary[obj]
                if summary["rise"] == 999:
                    summary.update({"rise": obs_hour, "type": object_type, "date": obs_date, "filters": suggested_filters, "link": finder_link, "difficulty": difficulty_html})
                summary.update({"set": obs_hour})   # set to hour found here as this will be the last
                if d > summary["max_az"]:
                    summary.update({"max_az": d, "max_az_hr": obs_hour})  # note d is altitude, not sure why I left that
                self.viewing_summary_dictionary[obj] = summary
                # increment Counters
                self.v_i_ctr += 1
        check_time.end_now()
        # check_time.print_delta()

    def write_out_html(self):
        with open('astronomy_report.html', 'w') as f:
            print(self.html, file=f)

    def make_summary_html(self):
        for obj in self.viewing_summary_dictionary:
            if self.viewing_summary_dictionary[obj]['rise'] == 999 and self.viewing_summary_dictionary[obj]['set'] == 0:
                continue
            self.html_summary += '<tr><td>' + obj.capitalize() + '</td><td>' + \
                                 self.viewing_summary_dictionary[obj]['type'].capitalize() + \
                                 '</td><td style="text-align:center">' + \
                                 self.viewing_summary_dictionary[obj]['difficulty'] + '</td><td>' + \
                                 str(self.viewing_summary_dictionary[obj]['rise']) + '</td><td>' + \
                                 str(self.viewing_summary_dictionary[obj]['set']) + '</td><td>' + \
                                 str(int(self.viewing_summary_dictionary[obj]['max_az'])) + '&#0176 @ ' + \
                                 str(self.viewing_summary_dictionary[obj]['max_az_hr']) + '</td><td>' + \
                                 self.viewing_summary_dictionary[obj]['link'] + '</td><td>' + \
                                 self.viewing_summary_dictionary[obj]['filters'] + '</td></tr>' + "\n"
        self.html_summary = html_header(self.site_name, self.viewing_date_evening, self.plot_file_name,
                                        self.half_dark_hours, 'true', self.summary_page_information) + \
                                        self.html_summary + html_footer()
        # note true means summary html

    def write_out_summary_html(self):
        with open(self.summary_filename, 'w') as f:
            print(self.html_summary, file=f)

    def add_footer(self):
        self.html = html_header(self.site_name, self.viewing_date_evening, self.plot_file_name, self.half_dark_hours,
                                self.utcoffset_int) + self.html + html_footer()


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
    html_foot = "</table>\n" \
                "<h5> Finder Charts provided by https://freestarcharts.com/ </h5>\n" \
                "</body>"
    return html_foot


def return_sector(degree):
    if 0 <= degree < 90:
        return "N"
    elif 90 <= degree < 180:
        return "E"
    elif 180 <= degree < 270:
        return "S"
    elif 270 <= degree < 3590:
        return "W"


def html_header(location_name, viewing_date, plot_file_name, half_dark_hours, summary='false', summary_page_info = ''):
    html_head = "<html><head><title>Astronomy Observation Suggestions</title>\n" \
                "<style>table, th,\n \
      td {\n \
        padding: 3px; \n \
        border: 1px solid black; \n \
        border-collapse: collapse; \n \
      } \n \
    .dotgreen {\n\
      height: 15px;\n\
      width: 15px;\n\
      background-color: #008000;\n\
      border-radius: 50%;\n\
      display: inline-block;\n\
    }\n\
    .dotred{\n\
      height: 15px;\n\
      width: 15px;\n\
      background-color: #FF0000;\n\
      border-radius: 50%;\n\
      display: inline-block;\n\
    }\n\
    .dotorange{\n\
      height: 15px;\n\
      width: 15px;\n\
      background-color: #FF8C00;\n\
      border-radius: 50%;\n\
      display: inline-block;\n\
    }\n\
    </style></head>\n<body>\n"  # add location specific information
    html_head += "<h2 style=\"font-family:verdana;\">Viewing Information for {0} On the evening of {1} through the "\
            "following morning</h2>\n".format(location_name, viewing_date)
    html_head += "<table> <tr><td>\n"
    html_head += '<img src="{0}">\n'.format(plot_file_name)
    html_head += "</td><td> " + summary_page_info + " </td></tr>\n</table>\n"
    #  html_head += "<h2>Viewing Items for {0} on {1}</h2>\n".format(location_name, viewing_date)
    if summary == 'false':
        html_head += "<h3>Azimuth Chart</h3>\n"
        html_head += "<table style=\"font-family:verdana;\">\n" \
                     "<tr><td>Direction</td><td>From</td><td>To</td></tr>\n" \
                     "<tr><td> North</td>  <td>0&deg;  </td><td>89&deg;  </td></tr>\n"
        html_head += "<tr><td> East </td>  <td>90&deg; </td><td>179&deg;  </td></tr>\n"
        html_head += "<tr><td> South</td>  <td>180&deg;</td><td>269&deg;  </td></tr>\n"
        html_head += "<tr><td> West </td>  <td>270&deg;</td><td>359&deg;  </td></tr> </table> <br>\n"
        html_head += "<b>Jump to Hour: </b><a id=\"#Top\"></a>"
        for hour in range((24 - half_dark_hours), 24, 1):
            html_head += "<a href = \"#{0}\"> {0} </a> - ".format(hour)
        for hour in range(0, half_dark_hours, 1):
            html_head += "<a href = \"#{0}\"> {0} </a> - ".format(hour)
        html_head += "<a href = \"#{0}\"> {0} </a> ".format(half_dark_hours)
        html_head += "<table>\n"
        html_head += header_row()
    else:
        html_head += "<table style=\"font-family:verdana;\">\n"
        html_head += summary_header_row()
    return html_head


def summary_header_row():
    return "<tr><td colspan=9> </td></tr>\n "\
            "<tr bgcolor=lightgrey><td><b>Object</b></td><td><b>Type</b></td><td><b>Difficulty</b></td>"\
            "<td><b>Rise Hour</b></td><td><b>Set Hour</b></td>" \
            "<td><a href=\"https://en.wikipedia.org/wiki/Horizontal_coordinate_system\"><b>Max Altitude</b></a>" \
            "</td><td><b>Finder Chart</b><br></td><td><b>Suggested Filter</b></td></tr>\n"


def header_row():
    return "<tr><td><b>Object</b></td><td><b>Type</b></td><td><b>Date</b></td><td><b>Hour</b></td>" \
           "<td><b>Altitude</b></td><td><b>Azimuth</b></td><td><b>Finder Chart</b><br></td><td><b>Suggested Filter" \
           "</b></td></tr>\n"


def get_lunar_phase(lunar_date):
    yr, m, d = map(int, lunar_date.split('-'))
    new_date = datetime.datetime(yr, m, d)
    ph = int(pyasl.jdcnv(new_date))
    return int((pyasl.moonphase(ph) * 100)[0]) # moon phase returns a float between 0 and 1
#  pyasl.jdconv converts the date to the date format that moonphase needs to use


def convert_html_to_pdf(html_filename, pdf_filename):
    # Define path to wkhtmltopdf.exe
    path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'

    # Point pdfkit configuration to wkhtmltopdf.exe
    config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

    # set options
    # orientation makes it look better landscape vs portrait
    # enable-external-links was key to enable them to work
    # enable-local-file-access is needed to alllow the local image of the sun moon chart to be used
    options = {
        'enable-external-links': None,
        "enable-local-file-access": None,
        'orientation': 'Landscape'
    }

    # Convert HTML file to PDF
    pdfkit.from_file(html_filename, output_path=pdf_filename, configuration=config, options=options)


def set_main_layout():
    location_text = 'Enter Location Address, City, State: '
    date_text = 'Enter Date: '
    time_text = 'Enter Time: '
    layout = [
        [sg.Button('Load or Save a Location for Reuse')],
        [sg.Text(location_text), sg.Input(key='-INPUTLOC-')],
        [sg.Text(date_text), sg.Input(key='-INPUTDATE-')],
        [sg.Text(time_text), sg.Input(key='-INPUTTIME-')],
        [sg.Button('Save Location'), sg.Button('Generate PDF and HTML')],
        [sg.Text('Working on:'), sg.Text('Not Started', key='-TEXTSTATUS-', text_color='red', visible=False)],
        [sg.Button('Close')]
        ]
    return layout

def get_elevation_in_feet(lat, long):
    query = f'https://api.open-elevation.com/api/v1/lookup?locations={lat},{long}'
    r = requests.get(query).json()
    elevation_meters = r['results'][0]['elevation']
    elevation_feet = elevation_meters * 3.28084
    rounded_elevation_feet = round(elevation_feet)
    return rounded_elevation_feet

def main():

    # Set up the window
    sg.theme('DarkBlue')
    layout = set_main_layout()
    window = sg.Window('Viewing Tonight', layout, finalize=True)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Close':
            break
        elif event == 'Load or Save a Location for Reuse':
            location_data= UserDataApp()
            location_data.run()
        elif event == 'Generate PDF and HTML':
            # Maybe add here get sun data and when sun alt < 0 degrees
            # use that to limit check sky to only those dark hours and mark twilight hours
            # to viewing program
            main_time = Timing('Main Time')
            scan_sky = Viewing(location_data.user_data['latitude'], location_data.user_data['longitude'], location_data.user_data['name'])
            # Plot Sun and Moon
            print("Plotting Sun and Moon")
            filename = scan_sky.site_name.replace(' ', '-')
            scan_sky.plot_sun_moon()
            scan_sky.adjust_delta_midnight()
            # Get data for Planets
            print("Working on: ", end='', flush=True)
            planets_time = Timing('Planets Time')


            window['-TEXTSTATUS-'].update(visible=True)
            for planet in scan_sky.planet_list:
                window['-TEXTSTATUS-'].update(planet, text_color='green')
                window.refresh()
                print("{0}, ".format(planet), end='', flush=True)
                scan_sky.check_sky_tonight(planet)

            print(' ')  # output logging cleaner to screen
            planets_time.end_now()
            planets_time.print_delta()
            

       

            # Get data for Target group
            print("Starting Target Group ", flush=True)
            viewing_targets = Targets()
            targets_time = Timing('Targets Time')
            short_run = False
            if 'target_group' in viewing_targets.data:
                if viewing_targets.data["target_group"] == "messier":
                    print("Working on: ", end='', flush=True)
                    for m_num in range(1, scan_sky.messier_max):
                        m_id = "m" + str(m_num)
                        if m_num % 10 == 0:
                            print("{0}, ".format(m_id), end='', flush=True)
                            window['-TEXTSTATUS-'].update(f'Messier {m_id}')
                            window.refresh()
                        scan_sky.check_sky_tonight(m_id)
                        if m_num > 3 and short_run == True:
                            break
                        #sys.exit()
                    print("Finished with Messier", flush=True)
            targets_time.end_now()
            targets_time.print_delta()

            # Sort The found data
            print("Sorting The Data", flush=True)
            scan_sky.sort_data()
            scan_sky.set_html()

            # Print out Results
            print("Printing Out Results", flush=True)
            scan_sky.write_out_html()
            scan_sky.make_summary_html()
            scan_sky.write_out_summary_html()

            # Convert Summary HTML to pdf
            print("Making PDF", flush=True)
            convert_html_to_pdf(scan_sky.summary_filename, scan_sky.summary_pdf_filename)
            # Send email if the mail JSON file is present
            #print("Sending Email")
            #email = Mail(scan_sky.plot_file_name)
            # if email.mail_exists:
            # email.send_email(scan_sky.html, "see html version")
            # need to check API for caldwell list objects and other lists
            # for dso in viewing_targets.data["target_list"]:
            # scan_sky.check_sky_tonight(dso)
            main_time.end_now()
            main_time.print_delta()


if __name__ == '__main__':
    main()
