#!/usr/bin/env python

import time
import datetime
import requests
import sqlite3
import Adafruit_DHT
from twilio.rest import Client


dbname = 'temperature.db'
frequency_seconds = 120

WARM = 25.0  # ~77*f - warm enough to alert
COOL = 24.0  # ~75*f - cool enough to stop alerts
MAX_FAILED = 3

sensor = Adafruit_DHT.DHT22
pin = 14

TWILLO_ACCOUNT = 'TBD'
TWILLO_TOKEN = 'TBD'
SMS_FROM = 'TBD'
SMS_TO = 'TBD'


def roundtime(dt=None, round_to=60):
    if dt is None:
        dt = datetime.datetime.now()
    seconds = (dt.replace(tzinfo=None) - dt.min).seconds
    rounding = (seconds+round_to/2) // round_to * round_to
    return dt + datetime.timedelta(0, rounding-seconds, -dt.microsecond)



def send_alert(current_time, message):
    print('{} {}'.format(current_time, message))
    send_sms_alert(current_time, message)



def send_sms_alert(current_time, message):
    try:
        account = TWILLO_ACCOUNT
        token = TWILLO_TOKEN
        client = Client(account, token)
        message = client.messages.create(
            to=SMS_TO, from_=SMS_FROM,
            body='{} {}'.format(current_time, message))
    except:
        pass


with sqlite3.connect(dbname) as db:
    db.execute('CREATE TABLE IF NOT EXISTS readings (ts TIMESTAMP, temperature REAL, humidity REAL)')

warm_alerted = False
failed_readings = 0
alert_throttle = 0
while True:
    time.sleep(frequency_seconds - time.time() % frequency_seconds)
    now = roundtime(round_to=frequency_seconds)
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    # Note that sometimes you won't get a reading and the results will be null (because Linux can't
    # guarantee the timing of calls to read the sensor). If this happens try again!
    if not humidity or not temperature:
        print('Failed to get reading. Trying again after delay...')
        failed_readings += 1
        if failed_readings > MAX_FAILED:
            send_alert(now, 'Failed to read temperature sensor {}x'.format(failed_readings))
        continue
    failed_readings = 0
    if temperature > WARM and not warm_alerted:
        send_alert(now, 'Hey! It''s getting warm ({:0.1f}) in here...'.format(temperature * 9/5 + 32))
        warm_alerted = True
        alert_throttle = 1
    elif temperature > WARM and warm_alerted:
        alert_throttle = (alert_throttle + 1) % 6
        if alert_throttle == 0:
            send_alert(now, 'Hey! It''s still warm ({:0.1f}) in here...'.format(temperature * 9 / 5 + 32))
    elif temperature < COOL and warm_alerted:
        send_alert(now, 'Phew! It''s back to normal ({:0.1f}) in here. Carry on.'.format(temperature * 9 / 5 + 32))
        warm_alerted = False
    with sqlite3.connect(dbname) as db:
        db.execute('INSERT INTO readings VALUES (?,?,?)', (now, round(temperature, 1), round(humidity, 1)))
        db.commit()
    print('{} Temp: {:0.1f}*C {:0.1f}*F Humidity: {:0.1f}%'.format(
        now, temperature, temperature * 9/5 + 32, humidity))
