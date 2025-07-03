from __future__ import print_function

import time
import urllib
import json
from urllib.request import urlopen
from datetime import datetime, timedelta

apiKey = 'a4839c83-3c74-4513-beb0-c27eb2efe55e'
stationId = 44  

class WeatherData:
    def __init__(self, timeStamp, hourOfDay, relativeHumidity):
        self.timeStamp = timeStamp
        self.hourOfDay = hourOfDay
        self.relativeHumidity = relativeHumidity
       
    def getTimeStamp(self):
        return self.timeStamp
   
    def getHourOfDay(self):
        return self.hourOfDay
   
    def getRelativeHumidity(self):
        return self.relativeHumidity

def fetchWeatherDataForHour(hour):
    currentHour = time.localtime(time.time()).tm_hour
    if hour == 0 or hour > currentHour:
        dateToUse = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')
    else:
        dateToUse = datetime.now().strftime('%Y-%m-%d')

    weatherData = requestWeatherData(apiKey, stationId, dateToUse, dateToUse)

    if weatherData is None:
        return None
   
    weatherRecord = WeatherData(
        weatherData[hour - 1]['Date'],
        weatherData[hour - 1]['Hour'],
        weatherData[hour - 1]['HlyRelHum']['Value']
    )
    return weatherRecord

def retrieveDataFromUrl(apiUrl):
    try:
        responseContent = urlopen(apiUrl).read().decode('utf-8')
        assert(responseContent is not None)
        return json.loads(responseContent)
    except Exception as error:
        print("An error occurred while trying to fetch data:")
        print(error)
        return None

def requestWeatherData(apiKey, stationId, startDate, endDate):
    dataElements = ['hly-rel-hum']
    dataItems = ','.join(dataElements)

    apiUrl = (
        'http://et.water.ca.gov/api/data?appKey=' + apiKey + '&targets='
        + str(stationId) + '&startDate=' + startDate + '&endDate=' + endDate +
        '&dataItems=' + dataItems
    )

    weatherDataResponse = retrieveDataFromUrl(apiUrl)
    if weatherDataResponse is None:
        return None
    else:
        return weatherDataResponse['Data']['Providers'][0]['Records']