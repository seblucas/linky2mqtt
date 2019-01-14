# linky2mqtt

Get the measures from your Linky through your Enedis account and send it to your MQTT broker 

# Usage

## Prerequisite

You simply need Python3 (never tested with Python2.7) and the dependencies are in the requirements file with __ONE__ exception (see below)  :

```bash
pip3 install -r requirements.txt
```

I first intended to use directly [pylinky](https://github.com/Pirionfr/pyLinky) that is available on [Pypi](https://pypi.org/) but unfortunately the function that I need `_get_data_per_hour` is private there. There is fork done by [Ludovic Rousseau](https://github.com/LudovicRousseau/pyLinky) that make this function public. It's not available with `pip` so I have to install it manually in my [Dockerfile](./Dockerfile). No really cool I know, but as the Enedis pseudo API is already in maintenance almost every day, I don't want to hammer its API with things I don't need and make it worse. 

## Getting your Enedis ids

Create a new account and you're done.

## Using the script

Easy, first try a dry-run command (which will get the data from 03/01/2019 and dump them to your screen) :

```bash
./linky2mqtt.py -u '<USER_NAME>' -p '<PASSWORD>' -d '03/01/2019' -n -v
```

and then a real command to add to your crontab :

```bash
./linky2mqtt.py -u '<USER_NAME>' -p '<PASSWORD>' -l 'URL WITH LATEST TIMESTAMP RECEIVED' -v
```

The secrets can also be set with environment variables, see the help for more detail.

## Help

```bash
/ # linky2mqtt.py --help
usage: linky2mqtt.py [-h] -u ENEDISUSERNAME -p ENEDISPASSWORD [-m HOST]
                     [-d SPECIFICDAY] [-l LATESTREADINGURL] [-n]
                     [-o PREVIOUSFILENAME] [-t TOPIC] [-T TOPIC] [-v]

Read power consumption from Enedis pseudo API and send them to a MQTT broker.

optional arguments:
  -h, --help            show this help message and exit
  -u ENEDISUSERNAME, --username ENEDISUSERNAME
                        Enedis user name / Can also be read from
                        ENEDIS_USER_NAME env var. (default: None)
  -p ENEDISPASSWORD, --password ENEDISPASSWORD
                        Enedis password / Can also be read from
                        ENEDIS_PASSWORD env var. (default: None)
  -m HOST, --mqtt-host HOST
                        Specify the MQTT host to connect to. (default:
                        127.0.0.1)
  -d SPECIFICDAY, --day SPECIFICDAY
                        Specify a specific day to transfer. (default: )
  -l LATESTREADINGURL, --latest LATESTREADINGURL
                        Url with latest reading already stored. (default: )
  -n, --dry-run         No data will be sent to the MQTT broker. (default:
                        False)
  -o PREVIOUSFILENAME, --last-time PREVIOUSFILENAME
                        The file where the last timestamp coming from Enedis
                        API will be saved (default: /tmp/linky_last)
  -t TOPIC, --topic TOPIC
                        The MQTT topic on which to publish the message (if it
                        was a success). (default: sensor/power)
  -T TOPIC, --topic-error TOPIC
                        The MQTT topic on which to publish the message (if it
                        wasn't a success). (default: error/sensor/power)
  -v, --verbose         Enable debug messages. (default: False)

```

## Other things to know

I personaly use cron to start this program so as I want to keep the latest timestamp received from the API so that only new data is downloaded, I store it by default in `/tmp/linky_last` (you can change it through a command line parameter.

## Docker

I added a sample Dockerfile, I personaly use it with a `docker-compose.yml` like this one :

```yml
version: '3'

services:
  linky2mqtt:
    build: https://github.com/seblucas/linky2mqtt.git
    image: linky-python3-cron:latest
    restart: always
    environment:
      ENEDIS_USER_NAME: XXX
      ENEDIS_PASSWORD: XXX
      CRON_STRINGS: "05 14,19 * * * linky2mqtt.py -l 'https://my.domain.com/getLastDate?q=linky' -m mosquitto -t sensor/linky"
      CRON_LOG_LEVEL: 8
```


# Limits

 * I start this program two times a day to mitigate Enedis website numerous problems (normally one time should be enough). Sometimes I have to start it manually if the site is down too long.
 * Fortunately nothing else ;).

# License

This program is licenced with GNU GENERAL PUBLIC LICENSE version 3 by Free Software Foundation, Inc.
