#coding=utf-8

from SqlHandler import SqlHandler
from config import *
import urllib2
import  json
import time
import datetime
import random
class GetCityWeather():

    def __init__(self):
        self.mysql=SqlHandler()


    def get_allcitys_weather(self,citycode):
        # a=self.mysql.get_cityCode(cityname)
        # print a
        response=urllib2.urlopen(r"http://www.weather.com.cn/data/sk/%s.html"%citycode)
        data_dict= response.read()

        print data_dict,type(data_dict)
        data_dict=json.loads(data_dict)
        print data_dict, type(data_dict)
        data_dict1={}
        data_dict1=data_dict["weatherinfo"]

        if data_dict1.get("rain")=="0":
            weather_info = u'{0}的天气 :气温{1}摄氏度，湿度{2}，{3}{4}，无雨 '.format(
                data_dict1["city"], data_dict1["temp"],
                data_dict1["SD"], data_dict1["WD"],
                data_dict1["WS"]
            )
        elif  data_dict1.get("rain")=="1":
            weather_info = u'{0}的天气 :气温{1}摄氏度，湿度{2}，{3}{4}，有雨 '.format(
                data_dict1["city"], data_dict1["temp"],
                data_dict1["SD"], data_dict1["WD"],
                data_dict1["WS"]
            )
        else:
            weather_info = u'{0}的天气 :气温{1}摄氏度，湿度{2}，{3}{4} '.format(
                data_dict1["city"], data_dict1["temp"],
                data_dict1["SD"], data_dict1["WD"],
                data_dict1["WS"]
            )

        return weather_info

    def saveOneByCityCode(self,cityname):
        code = self.mysql.get_cityCodeByCityName(cityname)
        print code
        code=code[0]
        weather_info=self.get_allcitys_weather(code)
        self.write_WeatherInfo2Mysql(code,weather_info)

    def saveOneByIndex(self,index):
        code = self.mysql.get_cityCodeByIndex(index)
        print code
        code=code[0]
        weather_info=self.get_allcitys_weather(code)
        self.write_WeatherInfo2Mysql(code,weather_info)

    def write_WeatherInfo2Mysql(self,code,write_str):
        date_now = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        write_info=write_str+u"时间 :"+date_now
        write_cmd='update weather set weather.weather_info="%s" where weather.cityCode=%s'%(write_info,code)
        #write_cmd="abc中国"
        print  write_cmd
        self.mysql.write_mysql(write_cmd)

    def random_sleep(self):
        t=random.randint(1,10)
        return (t/100)

    def update_all(self):
        self.mysql.weather_count=self.mysql.read_mysql("select count(*) from weather")[0][0]
        start=1
        # try:
        for i in range(start,self.mysql.weather_count):
            try:
                self.saveOneByIndex(i)
                time.sleep(0.2)
                print "#####",i,"#####"
                star = i
            except BaseException:
                start = i






cw=GetCityWeather()
# #cw.random_sleep()
cw.update_all()
#

#cw.saveOneByCityCode(u"北京")
#cw.saveOneByCityCode(u"苏州")
# weather_info=cw.get_allcitys_weather(u"苏州")
# cw.write_WeatherInfo2Mysql(u"苏州",weather_info)
# date_now=time.strftime('%Y-%m-%d',time.localtime(time.time()))
# print date_now+weather_info
# response = urllib2.urlopen("http://www.weather.com.cn/data/sk/101190401.html")
# print response.read()
