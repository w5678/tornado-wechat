#coding=utf-8

# tasks.py
import celery
import Update_Weather
from celery.schedules import crontab

app = celery.Celery('auto_tasks', broker='redis://localhost:6379')


@app.task
def update_allCityWeather(message):
    cw=Update_Weather.GetCityWeather()
    cw.update_all()
    return "had update all weather"

@app.task
def send():
    return "had update all weather"

app.conf.beat_schedule = {
    'send-every-10-seconds': {
        'task': 'auto_tasks.update_allCityWeather',
        'schedule': crontab(minute=0, hour=3),
        'args': ( )
    },
}



	
