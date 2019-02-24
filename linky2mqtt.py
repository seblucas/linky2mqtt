#!/usr/bin/env python3
#
#  linky2mqtt.py
#
#  Copyright 2019 Sébastien Lucas <sebastien@slucas.fr>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#

import os, re, time, json, argparse
from datetime import datetime as DateTime, timedelta as TimeDelta
from pylinky import LinkyClient
import requests                     # pip install requests
import paho.mqtt.publish as publish # pip install paho-mqtt

verbose = False

def debug(msg):
  if verbose:
    print (msg + "\n")

def environ_or_required(key):
  if os.environ.get(key):
    return {'default': os.environ.get(key)}
  else:
    return {'required': True}

def formatData(startDate, input):
  time = startDate.timestamp() + 15*60
  result =  []
  for data in input:
    result.append({ 'time': int(time), 'elec': data['valeur'] })
    time = time + 30*60
  return result

def getLinkyData(startDate):
  tstamp = int(time.time())
  try:
    client = LinkyClient(args.enedisUsername, args.enedisPassword)
    client.login()
    endDate = startDate + TimeDelta(days=1)
    data = client.get_data_per_period(start=startDate, end=endDate)
    print (data)
    client.close_session()
    formatedData = formatData(startDate, data['data'])
    return (True, formatedData)
  except Exception as e:
    return (False, {"time": tstamp, "message": "Enedis not available : " + str(e)})
  

parser = argparse.ArgumentParser(description='Read power consumption from Enedis pseudo API and send them to a MQTT broker.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-u', '--username', dest='enedisUsername', action="store", help='Enedis user name / Can also be read from ENEDIS_USER_NAME env var.',
                   **environ_or_required('ENEDIS_USER_NAME'))
parser.add_argument('-p', '--password', dest='enedisPassword', action="store", help='Enedis password / Can also be read from ENEDIS_PASSWORD env var.',
                   **environ_or_required('ENEDIS_PASSWORD'))
parser.add_argument('-m', '--mqtt-host', dest='host', action="store", default="127.0.0.1",
                   help='Specify the MQTT host to connect to.')
parser.add_argument('-d', '--day', dest='specificDay', action="store", default="",
                   help='Specify a specific day to transfer.')
parser.add_argument('-l', '--latest', dest='latestReadingUrl', action="store", default="",
                   help='Url with latest reading already stored.')
parser.add_argument('-n', '--dry-run', dest='dryRun', action="store_true", default=False,
                   help='No data will be sent to the MQTT broker.')
parser.add_argument('-o', '--last-time', dest='previousFilename', action="store", default="/tmp/linky_last",
                   help='The file where the last timestamp coming from Enedis API will be saved')
parser.add_argument('-t', '--topic', dest='topic', action="store", default="sensor/power",
                   help='The MQTT topic on which to publish the message (if it was a success).')
parser.add_argument('-T', '--topic-error', dest='topicError', action="store", default="error/sensor/power", metavar="TOPIC",
                   help='The MQTT topic on which to publish the message (if it wasn\'t a success).')
parser.add_argument('-v', '--verbose', dest='verbose', action="store_true", default=False,
                   help='Enable debug messages.')


args = parser.parse_args()
verbose = args.verbose

oldTimestamp = 0
if os.path.isfile(args.previousFilename):
  oldTimestamp = int(open(args.previousFilename).read(10))
else:
  if args.latestReadingUrl:
    r = requests.get(args.latestReadingUrl)
    oldTimestamp = int(r.text)


if args.specificDay:
  startDate = DateTime.strptime(args.specificDay, "%d/%m/%Y")
else:
  utc_time = DateTime.utcfromtimestamp(oldTimestamp).replace(hour=0, minute=0)
  startDate = utc_time + TimeDelta(days=1)

if DateTime.today().date() == startDate.date():
  print ("nothing new")
  exit()

status, dataArray = getLinkyData(startDate)

if status:
  for data in dataArray:
    jsonString = json.dumps(data)
    debug("Success with message (for current readings) <{0}>".format(jsonString))

    # save the last timestamp in a file
    with open(args.previousFilename, 'w') as f:
      f.write(str(data["time"]))

    if not args.dryRun:
      publish.single(args.topic, jsonString, hostname=args.host)
    time.sleep(1)
else:
  jsonString = json.dumps(dataArray)
  debug("Failure with message <{0}>".format(jsonString))
  if not args.dryRun:
    publish.single(args.topicError, jsonString, hostname=args.host)