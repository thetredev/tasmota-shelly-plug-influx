import json
import re
from typing import NamedTuple

import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient


##########
# CONFIG #
##########
# Dennis: ich hab die aus der Vorlage NICHT angepasst, hier sollten natuerlich deine Daten rein!

INFLUXDB_ADDRESS = '192.168.0.8'
INFLUXDB_USER = 'mqtt'
INFLUXDB_PASSWORD = 'mqtt'
INFLUXDB_DATABASE = 'weather_stations'

MQTT_ADDRESS = '192.168.0.8'
MQTT_USER = 'cdavid'
MQTT_PASSWORD = 'cdavid'
MQTT_TOPIC = 'home/+/+'
MQTT_REGEX = 'home/([^/]+)/([^/]+)'
MQTT_CLIENT_ID = 'MQTTInfluxDBBridge'


# kann vmtl. noch erweitert werden, aber eins nach dem anderen
MQTT_TARGET = 'ENERGY'

MQTT_FIELDS = [
    'ApparentPower',
    # hier weitere relevante auflisten
]

##############
# CONFIG END #
##############
influxdb_client = InfluxDBClient(INFLUXDB_ADDRESS, 8086, INFLUXDB_USER, INFLUXDB_PASSWORD, None)


class SensorData(NamedTuple):
    location: str
    measurement: str
    value: float


def on_connect(client, userdata, flags, rc):
    """ The callback for when the client receives a CONNACK response from the server."""
    print(f'Connected with result code {str(rc)}')
    client.subscribe(MQTT_TOPIC)


def _parse_mqtt_message(topic, payload):
    match = re.match(MQTT_REGEX, topic)

    if not match:
        return

    location = match.group(1)
    measurement = match.group(2)

    if measurement == 'status':
        return

    # Payload => JSON object
    payload = json.loads(payload)

    # Wir interessieren uns nur fuer <MQTT_TARGET> ("ENERGY")
    if MQTT_TARGET not in payload:
        return

    # ... also auch nur den Teil, bitte.
    payload_target = payload[MQTT_TARGET]

    # Hier wird's spannend. Kommentar lesen, vllt. stimmt das noch nicht so ganz.
    for field in MQTT_FIELDS:
        # Ich weiss nicht genau, was hier genau in die InfluxDB geschrieben wird.
        # Vielleicht muss hier <measurement> auch mit <field> ersetzt werden.

        # <field> ist jeweils ein String aus <MQTT_FIELDS>, also "ApparentPower", usw.

        # Also theoretisch so:
        # yield SensorData(location, field, float(payload_target[field]))

        # Einfach mal ausprobieren!
        yield SensorData(location, measurement, float(payload_target[field]))


def _send_sensor_data_to_influxdb(sensor_data):
    json_body = [
        {
            'measurement': sensor_data.measurement,
            'tags': {
                'location': sensor_data.location
            },
            'fields': {
                'value': sensor_data.value
            }
        }
    ]

    influxdb_client.write_points(json_body)


def on_message(client, userdata, msg):
    """The callback for when a PUBLISH message is received from the server."""
    print(f'{msg.topic} {str(msg.payload)}')

    sensor_data_sets = _parse_mqtt_message(msg.topic, msg.payload.decode('utf-8'))

    if sensor_data_sets is None:
        print("Couldn't parse sensor data!")
        return

    for sensor_data in sensor_data_sets:
        _send_sensor_data_to_influxdb(sensor_data)


def _init_influxdb_database():
    databases = influxdb_client.get_list_database()

    if len(list(filter(lambda x: x['name'] == INFLUXDB_DATABASE, databases))) == 0:
        influxdb_client.create_database(INFLUXDB_DATABASE)

    influxdb_client.switch_database(INFLUXDB_DATABASE)


def main():
    _init_influxdb_database()

    mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(MQTT_ADDRESS, 1883)
    mqtt_client.loop_forever()


if __name__ == '__main__':
    print('MQTT to InfluxDB bridge')
    main()
