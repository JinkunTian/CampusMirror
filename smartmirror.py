#	Smart Mirror With QiangZhi Educational Management System
#	Author: JinkunTian
#	QQ    : 2961165914
#	GitHub: https://github.com/JinkunTian
#	date  : 2018-10-7 
#	Description:Smart Mirror With QiangZhi Educational 
#				Management System.You can config your
#				school's API address to check your curriculum
#				schedule.
#	Requirements:requests, feedparser, traceback, Pillow
#	

from Tkinter import *
import locale
import threading
import time
import requests
import json
import traceback
import feedparser

from PIL import Image, ImageTk
from contextlib import contextmanager


# Config your info at here

ui_locale = '' # e.g. 'fr_FR' fro French, '' as default
time_format = 24 # 12 or 24

# check python doc for strftime() for options
date_format = "%b %d, %Y"

# create account at https://darksky.net/dev/
weather_api_token = ''

# see https://darksky.net/dev/docs/forecast for full list of language parameters values
weather_lang = 'zh'

# see https://darksky.net/dev/docs/forecast for full list of unit parameters values
weather_unit = 'si'

# Set this if IP location lookup does not work for you (must be a string)
latitude = ''
longitude = ''

# QiangZhi Educational Management System API Address of your school
school_url="http://cquccjw.minghuaetc.com/cqdxcskjxy/app.do"

#Your QiangZhi Educational Management System UserName
school_user=""

#Your QiangZhi Educational Management System PassWord
school_password=""


LOCALE_LOCK = threading.Lock()

xlarge_text_size = 94
large_text_size = 48
medium_text_size = 28
small_text_size = 18

@contextmanager
def setlocale(name): #thread proof function to work with locale
	with LOCALE_LOCK:
		saved = locale.setlocale(locale.LC_ALL)
		try:
			yield locale.setlocale(locale.LC_ALL, name)
		finally:
			locale.setlocale(locale.LC_ALL, saved)

# maps open weather icons to
# icon reading is not impacted by the 'lang' parameter
icon_lookup = {
	'clear-day': "assets/Sun.png",  # clear sky day
	'wind': "assets/Wind.png",   #wind
	'cloudy': "assets/Cloud.png",  # cloudy day
	'partly-cloudy-day': "assets/PartlySunny.png",  # partly cloudy day
	'rain': "assets/Rain.png",  # rain day
	'snow': "assets/Snow.png",  # snow day
	'snow-thin': "assets/Snow.png",  # sleet day
	'fog': "assets/Haze.png",  # fog day
	'clear-night': "assets/Moon.png",  # clear sky night
	'partly-cloudy-night': "assets/PartlyMoon.png",  # scattered clouds night
	'thunderstorm': "assets/Storm.png",  # thunderstorm
	'tornado': "assests/Tornado.png",	# tornado
	'hail': "assests/Hail.png"  # hail
}


class Clock(Frame):
	def __init__(self, parent, *args, **kwargs):
		Frame.__init__(self, parent, bg='black')
		# initialize time label
		self.time1 = ''
		self.timeLbl = Label(self, font=('Helvetica', large_text_size), fg="white", bg="black")
		self.timeLbl.pack(side=TOP, anchor=E)
		# initialize day of week
		self.day_of_week1 = ''
		self.dayOWLbl = Label(self, text=self.day_of_week1, font=('Helvetica', small_text_size), fg="white", bg="black")
		self.dayOWLbl.pack(side=TOP, anchor=E)
		# initialize date label
		self.date1 = ''
		self.dateLbl = Label(self, text=self.date1, font=('Helvetica', small_text_size), fg="white", bg="black")
		self.dateLbl.pack(side=TOP, anchor=E)
		self.tick()

	def tick(self):
		with setlocale(ui_locale):
			if time_format == 12:
				time2 = time.strftime('%I:%M %p') #hour in 12h format
			else:
				time2 = time.strftime('%H:%M') #hour in 24h format

			day_of_week2 = time.strftime('%A')
			date2 = time.strftime(date_format)
			# if time string has changed, update it
			if time2 != self.time1:
				self.time1 = time2
				self.timeLbl.config(text=time2)
			if day_of_week2 != self.day_of_week1:
				self.day_of_week1 = day_of_week2
				self.dayOWLbl.config(text=day_of_week2)
			if date2 != self.date1:
				self.date1 = date2
				self.dateLbl.config(text=date2)
			# calls itself every 200 milliseconds
			# to update the time display as needed
			# could use >200 ms, but display gets jerky
			self.timeLbl.after(200, self.tick)


class Weather(Frame):
	def __init__(self, parent, *args, **kwargs):
		Frame.__init__(self, parent, bg='black')
		self.temperature = ''
		self.forecast = ''
		self.location = ''
		self.currently = ''
		self.icon = ''
		self.degreeFrm = Frame(self, bg="black")
		self.degreeFrm.pack(side=TOP, anchor=W)
		self.temperatureLbl = Label(self.degreeFrm, font=('Helvetica', xlarge_text_size), fg="white", bg="black")
		self.temperatureLbl.pack(side=LEFT, anchor=N)
		self.iconLbl = Label(self.degreeFrm, bg="black")
		self.iconLbl.pack(side=LEFT, anchor=N, padx=20)
		self.currentlyLbl = Label(self, font=('Helvetica', medium_text_size), fg="white", bg="black")
		self.currentlyLbl.pack(side=TOP, anchor=W)
		self.forecastLbl = Label(self, font=('Helvetica', small_text_size), fg="white", bg="black")
		self.forecastLbl.pack(side=TOP, anchor=W)
		self.locationLbl = Label(self, font=('Helvetica', small_text_size), fg="white", bg="black")
		self.locationLbl.pack(side=TOP, anchor=W)
		self.get_weather()

	def get_ip(self):
		try:
			ip_url = "http://jsonip.com/"
			req = requests.get(ip_url)
			ip_json = json.loads(req.text)
			return ip_json['ip']
		except Exception as e:
			traceback.print_exc()
			return "Error: %s. Cannot get ip." % e

	def get_weather(self):
		try:

			if latitude is None and longitude is None:
				# get location
				location_req_url = "http://freegeoip.net/json/%s" % self.get_ip()
				r = requests.get(location_req_url)
				location_obj = json.loads(r.text)

				lat = location_obj['latitude']
				lon = location_obj['longitude']

				location2 = "%s, %s" % (location_obj['city'], location_obj['region_code'])

				# get weather
				weather_req_url = "https://api.darksky.net/forecast/%s/%s,%s?lang=%s&units=%s" % (weather_api_token, lat,lon,weather_lang,weather_unit)
			else:
				location2 = ""
				# get weather
				weather_req_url = "https://api.darksky.net/forecast/%s/%s,%s?lang=%s&units=%s" % (weather_api_token, latitude, longitude, weather_lang, weather_unit)

			r = requests.get(weather_req_url)
			weather_obj = json.loads(r.text)

			degree_sign= u'\N{DEGREE SIGN}'
			temperature2 = "%s%s" % (str(int(weather_obj['currently']['temperature'])), degree_sign)
			currently2 = weather_obj['currently']['summary']
			forecast2 = weather_obj["hourly"]["summary"]

			icon_id = weather_obj['currently']['icon']
			icon2 = None

			if icon_id in icon_lookup:
				icon2 = icon_lookup[icon_id]

			if icon2 is not None:
				if self.icon != icon2:
					self.icon = icon2
					image = Image.open(icon2)
					image = image.resize((100, 100), Image.ANTIALIAS)
					image = image.convert('RGB')
					photo = ImageTk.PhotoImage(image)

					self.iconLbl.config(image=photo)
					self.iconLbl.image = photo
			else:
				# remove image
				self.iconLbl.config(image='')

			if self.currently != currently2:
				self.currently = currently2
				self.currentlyLbl.config(text=currently2)
			if self.forecast != forecast2:
				self.forecast = forecast2
				self.forecastLbl.config(text=forecast2)
			if self.temperature != temperature2:
				self.temperature = temperature2
				self.temperatureLbl.config(text=temperature2)
			if self.location != location2:
				if location2 == ", ":
					self.location = "Cannot Pinpoint Location"
					self.locationLbl.config(text="Cannot Pinpoint Location")
				else:
					self.location = location2
					self.locationLbl.config(text=location2)
		except Exception as e:
			traceback.print_exc()
			print "Error: %s. Cannot get weather." % e

		self.after(600000, self.get_weather)

	@staticmethod
	def convert_kelvin_to_fahrenheit(kelvin_temp):
		return 1.8 * (kelvin_temp - 273) + 32
class News(Frame):
	def __init__(self, parent, *args, **kwargs):
		Frame.__init__(self, parent, *args, **kwargs)
		self.config(bg='black')
		self.schedule = ''
		self.message = ''
		self.scheduleLbl = Label(self, text=self.schedule,wraplength=800,justify='left',font=('Helvetica', small_text_size), fg="white", bg="black")
		#self.messageLbl = Label(self, text=self.message,wraplength=800,justify='left',font=('Helvetica', small_text_size), fg="white", bg="black")
		self.scheduleLbl.pack(side=LEFT, anchor=S)
		#self.messageLbl.pack(side=LEFT, anchor=S)
		self.get_class_schedule()
		#self.get_message()

	def get_class_schedule(self):
		schedule_time=time.localtime()
		schedule_date=time.strftime("%Y-%m-%d",schedule_time)
		schedule_week=time.strftime("%w",schedule_time)

		payload={
			'method':'authUser',
			'xh':school_user,
			'pwd':school_password
		}

		# login and get token
		authUser=requests.get(school_url,params=payload)
		school_token=json.loads(authUser.text)

		headers={
			"token":school_token['token']
		}
		payload={
			'method':'getCurrentTime',
			'currDate':schedule_date
		}

		# get time schedule
		getCurrentTime=requests.post(school_url,params=payload,headers=headers)
		CurrentTime=json.loads(getCurrentTime.text)

		headers={
			"token":school_token['token']
		}
		payload={
			'method':'getKbcxAzc',
			'xh':school_user,
			'xnxqid':CurrentTime['xnxqh'],
			'zc':str(CurrentTime['zc'])
		}

		# get curriculum data and decode
		data=requests.post(school_url,params=payload,headers=headers)
		school_schedule=json.loads(data.text)

		Today_class=[]
		Tomorrow_class=[]
		schedule_text=""

		kcb_len=len(school_schedule)

		#extract curriculum which on today and tomorrow
		for x in xrange(0,kcb_len):
			if (int(school_schedule[x]['kcsj'][0:1])==(int(schedule_week))):
				Today_class.append(school_schedule[x])
			if (int(school_schedule[x]['kcsj'][0:1])==((int(schedule_week)+1))):
				Tomorrow_class.append(school_schedule[x])
		if len(Today_class)>0:
			schedule_text="Today\n"
			for z in xrange(0,len(Today_class)):
				if Today_class[z]['jsmc']:
					schedule_text=schedule_text+"   "+Today_class[z]['kssj']+" "+Today_class[z]['kcmc']+" ["+Today_class[z]['jsmc']+"]\n"
				else:
					schedule_text=schedule_text+"   "+Today_class[z]['kssj']+" "+Today_class[z]['kcmc']+"\n"
		if len(Tomorrow_class)>0:
			schedule_text=schedule_text+"Tomorrow\n"
			for z in xrange(0,len(Tomorrow_class)):
				if Tomorrow_class[z]['jsmc']:
					schedule_text=schedule_text+"   "+Tomorrow_class[z]['kssj']+" "+Tomorrow_class[z]['kcmc']+" ["+Tomorrow_class[z]['jsmc']+"]\n"
				else:
					schedule_text=schedule_text+"   "+Tomorrow_class[z]['kssj']+" "+Tomorrow_class[z]['kcmc']+"\n"

		# A message service,go to http://mirror.tianjintech.com to register and use
		headlines_url = "http://mirror.tianjintech.com/control/get.php?key=%s" % (weather_api_token)
		r = requests.get(headlines_url)
		message = ''
		message = r.text

		schedule_text=schedule_text+message

		self.scheduleLbl.config(text=schedule_text)
		self.after(30000, self.get_class_schedule)

class FullscreenWindow:

	def __init__(self):
		self.tk = Tk()
		self.tk.configure(background='black')
		self.topFrame = Frame(self.tk, background = 'black')
		self.bottomFrame = Frame(self.tk, background = 'black')
		self.topFrame.pack(side = TOP, fill=BOTH, expand = YES)
		self.bottomFrame.pack(side = BOTTOM, fill=BOTH, expand = YES)
		self.state = False

		self.tk.overrideredirect(True)
		self.tk.geometry("{0}x{1}+0+0".format(self.tk.winfo_screenwidth(), self.tk.winfo_screenheight()))
		self.tk.focus_set()
		self.tk.bind("<Escape>", lambda e: e.widget.quit())

		# clock
		self.clock = Clock(self.topFrame)
		self.clock.pack(side=RIGHT, anchor=N, padx=100, pady=60)
		# weather
		self.weather = Weather(self.topFrame)
		self.weather.pack(side=LEFT, anchor=N, padx=100, pady=60)
		# news
		self.news = News(self.bottomFrame)
		self.news.pack(side=LEFT, anchor=S, padx=100, pady=60)
		# calender - removing for now

	def toggle_fullscreen(self, event=None):
		self.state = not self.state  # Just toggling the boolean
		self.tk.attributes("-fullscreen", self.state)
		return "break"

	def end_fullscreen(self, event=None):
		self.state = False
		self.tk.attributes("-fullscreen", True)
		return "break"

if __name__ == '__main__':
	w = FullscreenWindow()
	w.tk.mainloop()
