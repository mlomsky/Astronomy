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
from PyAstronomy import pyasl # Using this to get Lunar Phase
from Messier import Messier
from collections import defaultdict
import pdfkit


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
        self.moon_phase_pct = get_lunar_phase(self.date)
        self.viewing_date_evening = str(datetime.date(int(date[0:4]), int(date[5:7]), int(date[8:10])))
        self.site_name = name
        self.height = height
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
        self.plot_file_name = 'sun_moon_plot.png'
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
        self.summary_filename = 'astronomy_report_summary.html'
        self.summary_pdf_filename = 'astronomy_report_summary.pdf'
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
        dusktime = datetime.datetime.strptime(self.date + ' ' + self.dusk + ':00', '%Y-%m-%d %H:%M:%S')
        diff = midnight - dusktime
        self.half_dark_hours = round(diff.seconds / 3600)

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
        moon_data = get_moon(self.sun_moon_viewing_times)
        moonaltazs = moon_data.transform_to(self.sun_moon_viewing_frame)
        plt.plot(self.sun_moon_delta_midnight, moonaltazs.alt, color=[0.75] * 3, ls='--', label='Moon')
        plt.plot(self.sun_moon_delta_midnight, sunaltazs_viewing_date.alt, color='r', label='Sun')
        plt.fill_between(self.sun_moon_delta_midnight, 0 * u.deg, 90 * u.deg,
                         sunaltazs_viewing_date.alt < -0 * u.deg, color='0.5', zorder=0)
        plt.fill_between(self.sun_moon_delta_midnight, 0 * u.deg, 90 * u.deg,
                         sunaltazs_viewing_date.alt < -18 * u.deg, color='k', zorder=0)
        plt.legend(loc='upper left')
        plt.xlim(-12 * u.hour, 12 * u.hour)
        plt.xticks((np.arange(13) * 2 - 12) * u.hour)
        plt.ylim(0 * u.deg, 90 * u.deg)
        plt.xlabel('Hours from Midnight on {0}'.format(self.date))
        plt.ylabel('Altitude [deg]')
        plt.title('Sun & Moon Details at {0} with {1}% Moon '.format(self.site_name, self.moon_phase_pct))
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
        # set summary base values for object
        self.viewing_summary_dictionary[obj]["rise"] = 999  # set rise time to a default num to compare to
        self.viewing_summary_dictionary[obj]["set"] = 0 # basically same as above
        self.viewing_summary_dictionary[obj]["max_az"] = 0

        # Move on to the calculation
        if obj in self.planet_list:
            midnight = Time(self.date + ' 00:00:00')
            sky_obj = get_body(obj, midnight)
        else:
            sky_obj = SkyCoord.from_name(obj)
        sky_objaltazs_viewing_date = sky_obj.transform_to(self.viewing_frame)

        last_hour = 999
        for altaz in sky_objaltazs_viewing_date:  # need to parallelize this at some point
            altitude = altaz.alt
            (sign, d, m, s) = altitude.signed_dms
            (zsign, zd, zm, zs) = altaz.az.signed_dms
            zstr = zsign + zd
            ohour = str(altaz.obstime)[11:13]
            omin = str(altaz.obstime)[14:16]
            odate = str(altaz.obstime)[0:10]
            oday = str(altaz.obstime)[8:10]
            omon = str(altaz.obstime)[5:7]

            object_type = 'Planet'
            suggested_filters = ''
            finder_link = ''
            difficulty_html = ''
            if obj not in self.planet_list:
                object_type = self.my_messier.object_type[obj]
                finder_link = "<a href=\"https://freestarcharts.com/images/Articles/Messier" \
                              "/Single/{0}_Finder_Chart.pdf\" target=\"_blank\">Finder Chart</a>".format(obj.upper())
                if obj in self.my_messier.messier_filters.keys():
                    suggested_filters = self.my_messier.messier_filters[obj]
                if obj in self.my_messier.messier_difficulty.keys() and self.my_messier.messier_difficulty[obj] == 'easy':
                    difficulty_html = '<span class="dotgreen"></span>'
                elif obj in self.my_messier.messier_difficulty.keys() and self.my_messier.messier_difficulty[obj] == 'medium':
                    difficulty_html = '<span class="dotorange"></span>'
                elif obj in self.my_messier.messier_difficulty.keys() and self.my_messier.messier_difficulty[obj] == 'hard':
                    difficulty_html = '<span class="dotred"></span>'
                #if self.viewing_summary_dictionary[obj]["rise"] == 999:
                    #continue

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
                if int(ohour) % 2 == 0:
                    tr_bgclr = "#d5f5e3"
                else:
                    tr_bgclr = "#d6eaf8"
                compass = return_sector(zstr)
                direction = str(zstr) + " - {0}".format(compass)
                table_row = "<tr bgcolor={6}><td>{0}</td><td>{5}</td><td>{1}</td><td>{2}</td><td>{3}&#730;</td>" \
                            "<td>{4}&#730;</td><td>{8}</td><td>{7}</td></tr>\n" \
                    .format(obj.upper(), obs_date, obs_hour, d, direction, object_type, tr_bgclr, suggested_filters,
                            finder_link)
                key = int(omon) * 10000 + int(oday) * 100 + int(ohour)
                self.viewing_index[self.v_i_ctr] = key
                self.viewing_dictionary[self.v_i_ctr] = table_row
                # Set summary info
                if self.viewing_summary_dictionary[obj]["rise"] == 999:
                    self.viewing_summary_dictionary[obj]["rise"] = obs_hour
                    self.viewing_summary_dictionary[obj]["type"] = object_type
                    self.viewing_summary_dictionary[obj]["date"] = obs_date
                    self.viewing_summary_dictionary[obj]["filters"] = suggested_filters
                    self.viewing_summary_dictionary[obj]["link"] = finder_link
                    self.viewing_summary_dictionary[obj]["difficulty"] = difficulty_html
                self.viewing_summary_dictionary[obj]["set"] = obs_hour  # set to hour found here as this will be the last
                if d > self.viewing_summary_dictionary[obj]["max_az"]:
                    self.viewing_summary_dictionary[obj]["max_az"] = d  # note d is altitude, not sure why i left that
                    self.viewing_summary_dictionary[obj]["max_az_hr"] = obs_hour
                # increment Counters
                self.v_i_ctr += 1

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
        filename = self.date + '_' + self.site_name + '_' + self.summary_filename
        filename = filename.replace(' ', '_')
        with open(filename, 'w') as f:
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
    html_head += "<h1 style=\"font-family:verdana;\">Viewing Information for {0} </h1>\n"\
                 " <h2>For the evening of {1} through the following morning</h2>\n".format(location_name, viewing_date)
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
    print(lunar_date)
    yr = int(lunar_date[0:4])
    m = int(lunar_date[5:7])
    d = int(lunar_date[8:10])
    new_date = datetime.datetime(yr, m, d)
    ph = pyasl.jdcnv(new_date)
    return int(pyasl.moonphase(ph) * 100)  # moon phase returns a float between 0 and 1
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
            for m_num in range(1, scan_sky.messier_max):
                m_id = "m" + str(m_num)
                print("Working on: {0}".format(m_id))
                scan_sky.check_sky_tonight(m_id)
                #if m_num > 3:
                     #break
                    #pass
                #   sys.exit()
    # Sort The found data
    scan_sky.sort_data()
    scan_sky.set_html()
    # Print out Results
    print("Printing Out Results")
    scan_sky.write_out_html()
    scan_sky.make_summary_html()
    scan_sky.write_out_summary_html()
    # Convert Summary HTML to pdf
    convert_html_to_pdf(scan_sky.summary_filename, scan_sky.summary_pdf_filename)
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
