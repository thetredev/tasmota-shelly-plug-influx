import json
import pydoc
import random
import re
import string
from pathlib import Path
from typing import NamedTuple

import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient


def is_container():
    """Are we running as container?"""
    if Path("/run/.containerenv").exists():
        return True

    if Path("/.dockerenv").exists():
        return True

    cgroup_path = Path('/proc/self/cgroup')

    if cgroup_path.exists() and cgroup_path.is_file():
        with cgroup_path.open() as f:
            return any('docker' in line for line in f)

    return False


# Parse config file
config_json = Path("config/shelly2influxdb.json")

if is_container():
    config_json = Path("/").joinpath(config_json)


# Panic if no config was found
if not config_json.exists():
    raise FileNotFoundError(f"Config file {config_json.as_posix()} does not exist!")


# Read config file
with config_json.open() as config_file:
    config = json.load(config_file)


# Create InfluxDB client
influxdb_client = InfluxDBClient(**config["influxdb"] | {"database": None})


# Do the magic...
class SensorData(NamedTuple):
    location: str
    measurement: str
    value: float


def on_connect(client: mqtt.Client, _, __, rc: int):
    """The callback for when the client receives a CONNACK response from the server."""
    print(f'Connected with result code {rc}')
    client.subscribe(config["mqtt"]["topic"])


def _parse_mqtt_message(topic: bytes, payload: str):
    mqtt_config = config["mqtt"]

    match = re.match(mqtt_config["message_prefix"], topic)

    if not match:
        return

    location = match.group(1)
    measurement = match.group(2)

    if measurement == 'status':
        return

    # Payload => JSON object
    payload = json.loads(payload)

    if mqtt_config["target"] not in payload:
        return

    for target in mqtt_config["targets"]:
        if target not in payload:
            continue

        payload_target = payload[target]

        for field in target:
            field_name = field["name"]
            field_type = pydoc.locate(field["type"])
            field_value = field_type(payload_target[field_name])

            yield SensorData(location, measurement, field_value)


def _send_sensor_data_to_influxdb(sensor_data: SensorData):
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


def on_message(_, __, msg: mqtt.MQTTMessage):
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
    influxdb_database = config["influxdb"]["database"]

    if len(list(filter(lambda x: x['name'] == influxdb_database, databases))) == 0:
        influxdb_client.create_database(influxdb_database)

    influxdb_client.switch_database(influxdb_database)


def main():
    _init_influxdb_database()

    mqtt_config = config["mqtt"]
    mqtt_client_id_prefix = mqtt_config["client_id_prefix"]
    mqtt_client_id_suffix = "".join(random.choices(f"{string.ascii_letters}{string.digits}", k=16))
    mqtt_client_id = f"{mqtt_client_id_prefix}-{mqtt_client_id_suffix}"

    mqtt_client = mqtt.Client(mqtt_client_id)
    mqtt_client.username_pw_set(mqtt_config["username"], mqtt_config["password"])
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(mqtt_config["host"], mqtt_config["port"])
    mqtt_client.loop_forever()


if __name__ == '__main__':
    print('MQTT to InfluxDB bridge')
    main()
