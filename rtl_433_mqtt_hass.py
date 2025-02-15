#!/usr/bin/env python3
# coding=utf-8

"""MQTT Home Assistant auto discovery for rtl_433 events."""

# It is strongly recommended to run rtl_433 with "-C si" and "-M newmodel".

# Needs Paho-MQTT https://pypi.python.org/pypi/paho-mqtt

# Option: PEP 3143 - Standard daemon process library
# (use Python 3.x or pip install python-daemon)
# import daemon

from __future__ import print_function
from __future__ import with_statement

import os
import socket
import time
import json
import paho.mqtt.client as mqtt

MQTT_HOST = os.environ['MQTT_HOST']
MQTT_PORT = os.environ['MQTT_PORT']
MQTT_USERNAME = os.environ['MQTT_USERNAME']
MQTT_PASSWORD = os.environ['MQTT_PASSWORD']
MQTT_TOPIC = os.environ['MQTT_TOPIC']
DISCOVERY_PREFIX = os.environ['DISCOVERY_PREFIX']
DISCOVERY_INTERVAL = os.environ['DISCOVERY_INTERVAL']

# Convert number environment variables to int
MQTT_PORT = int(MQTT_PORT)
DISCOVERY_INTERVAL = int(DISCOVERY_INTERVAL)

discovery_timeouts = {}

mappings = {
    "protocol": {
        "device_type": "sensor",
        "object_suffix": "Protocol",
        "config": {
            "name": "Protocol",
#            "value_template": "{{ value_json.protocol }}"
        }
    },
    "rssi": {
        "device_type": "sensor",
        "object_suffix": "RSSI",
        "config": {
            "name": "RSSI",
            "unit_of_measurement": "dB",
#            "value_template": "{{ value_json.rssi }}"
        }
    },
    "temperature_C": {
        "device_type": "sensor",
        "object_suffix": "Temperature",
        "config": {
            "device_class": "temperature",
            "name": "Temperature",
            "unit_of_measurement": "°C",
#            "value_template": "{{ value_json.temperature_C }}"
        }
    },
    "temperature_1_C": {
        "device_type": "sensor",
        "object_suffix": "Temperature 1",
        "config": {
            "device_class": "temperature",
            "name": "Temperature 1",
            "unit_of_measurement": "°C",
            "value_template": "{{ value_json.temperature_1_C }}"
        }
    },
    "temperature_2_C": {
        "device_type": "sensor",
        "object_suffix": "Temperature 2",
        "config": {
            "device_class": "temperature",
            "name": "Temperature 2",
            "unit_of_measurement": "°C",
            "value_template": "{{ value_json.temperature_2_C }}"
        }
    },
    "temperature_F": {
        "device_type": "sensor",
        "object_suffix": "Temperature",
        "config": {
            "device_class": "temperature",
            "name": "Temperature",
            "unit_of_measurement": "°F",
            "value_template": "{{ value_json.temperature_F }}"
        }
    },

    "battery_ok": {
        "device_type": "sensor",
        "object_suffix": "Battery",
        "config": {
            "device_class": "battery",
            "name": "Battery",
            "unit_of_measurement": "%",
            "value_template": "{{ float(value_json.battery_ok) * 99 + 1 }}"
        }
    },

    "humidity": {
        "device_type": "sensor",
        "object_suffix": "Humidity",
        "config": {
            "device_class": "humidity",
            "name": "Humidity",
            "unit_of_measurement": "%",
#            "value_template": "{{ value_json.humidity }}"
        }
    },

    "moisture": {
        "device_type": "sensor",
        "object_suffix": "Moisture",
        "config": {
            "device_class": "moisture",
            "name": "Moisture",
            "unit_of_measurement": "%",
            "value_template": "{{ value_json.moisture }}"
        }
    },

    "pressure_hPa": {
        "device_type": "sensor",
        "object_suffix": "Pressure",
        "config": {
            "device_class": "pressure",
            "name": "Pressure",
            "unit_of_measurement": "hPa",
            "value_template": "{{ value_json.pressure_hPa }}"
        }
    },

    "wind_speed_km_h": {
        "device_type": "sensor",
        "object_suffix": "WS",
        "config": {
            "device_class": "weather",
            "name": "Wind Speed",
            "unit_of_measurement": "km/h",
            "value_template": "{{ value_json.wind_speed_km_h }}"
        }
    },

    "wind_speed_m_s": {
        "device_type": "sensor",
        "object_suffix": "WS",
        "config": {
            "device_class": "weather",
            "name": "Wind Speed",
            "unit_of_measurement": "km/h",
            "value_template": "{{ float(value_json.wind_speed_m_s) * 3.6 }}"
        }
    },

    "gust_speed_km_h": {
        "device_type": "sensor",
        "object_suffix": "GS",
        "config": {
            "device_class": "weather",
            "name": "Gust Speed",
            "unit_of_measurement": "km/h",
            "value_template": "{{ value_json.gust_speed_km_h }}"
        }
    },

    "gust_speed_m_s": {
        "device_type": "sensor",
        "object_suffix": "GS",
        "config": {
            "device_class": "weather",
            "name": "Gust Speed",
            "unit_of_measurement": "km/h",
            "value_template": "{{ float(value_json.gust_speed_m_s) * 3.6 }}"
        }
    },

    "wind_dir_deg": {
        "device_type": "sensor",
        "object_suffix": "WD",
        "config": {
            "device_class": "weather",
            "name": "Wind Direction",
            "unit_of_measurement": "°",
            "value_template": "{{ value_json.wind_dir_deg }}"
        }
    },

    "rain_mm": {
        "device_type": "sensor",
        "object_suffix": "RT",
        "config": {
            "device_class": "weather",
            "name": "Rain Total",
            "unit_of_measurement": "mm",
            "value_template": "{{ value_json.rain_mm }}"
        }
    },

    "rain_mm_h": {
        "device_type": "sensor",
        "object_suffix": "RR",
        "config": {
            "device_class": "weather",
            "name": "Rain Rate",
            "unit_of_measurement": "mm/h",
            "value_template": "{{ value_json.rain_mm_h }}"
        }
    },

    # motion...

    # switches...

    "depth_cm": {
        "device_type": "sensor",
        "object_suffix": "D",
        "config": {
            "device_class": "depth",
            "name": "Depth",
            "unit_of_measurement": "cm",
            "value_template": "{{ value_json.depth_cm }}"
        }
    },
}


def mqtt_connect(client, userdata, flags, rc):
    """Callback for MQTT connects."""
    print("MQTT connected: " + mqtt.connack_string(rc))
    client.publish("/".join([MQTT_TOPIC, "status"]), payload="online", qos=0, retain=True)
    if rc != 0:
        print("Could not connect. Error: " + str(rc))
    else:
        client.subscribe("/".join([MQTT_TOPIC, "events"]))


def mqtt_disconnect(client, userdata, rc):
    """Callback for MQTT disconnects."""
    print("MQTT disconnected: " + mqtt.connack_string(rc))


def mqtt_message(client, userdata, msg):
    """Callback for MQTT message PUBLISH."""
    try:
        # Decode JSON payload
        data = json.loads(msg.payload.decode())
        bridge_event_to_hass(client, msg.topic, data)

    except json.decoder.JSONDecodeError:
        print("JSON decode error: " + msg.payload.decode())
        return

    except:
        print("Unhandled exception")
        print("JSON: " + msg.payload.decode())
        return



def sanitize(text):
    """Sanitize a name for Graphite/MQTT use."""
    return (text
            .replace(" ", "_")
            .replace("/", "_")
            .replace(".", "_")
            .replace("&", ""))


def publish_config(mqttc, topic, manmodel, instance, channel, mapping):
    """Publish Home Assistant auto discovery data."""
    global discovery_timeouts

    device_type = mapping["device_type"]
    object_id = "_".join([manmodel.replace("-", "_"), instance])
    object_suffix = mapping["object_suffix"]

    path = "/".join([DISCOVERY_PREFIX, device_type, object_id, object_suffix, "config"])

    # check timeout
    now = time.time()
    if path in discovery_timeouts:
        if discovery_timeouts[path] > now:
            return

    discovery_timeouts[path] = now + DISCOVERY_INTERVAL

    config = mapping["config"].copy()
    config["state_topic"] = "/".join([MQTT_TOPIC, manmodel, instance, channel, topic])
    config["name"] = " ".join([manmodel.replace("-", " "), instance, object_suffix])
    config["unique_id"] = "".join(["rtl433", device_type, instance, object_suffix])
    config["availability_topic"] = "/".join([MQTT_TOPIC, "status"])
    config["force_update"] = True

    # add Home Assistant device info

    manufacturer,model = manmodel.split("-", 1)

    device = {}
    device["identifiers"] = instance
    device["name"] = instance
    device["model"] = model
    device["manufacturer"] = manufacturer
    config["device"] = device
    
    mqttc.publish(path, json.dumps(config))
    # print(path, " : ", json.dumps(config))


def bridge_event_to_hass(mqttc, topic, data):
    """Translate some rtl_433 sensor data to Home Assistant auto discovery."""

    if "model" not in data:
        # not a device event
        return
    manmodel = sanitize(data["model"])

    if "id" not in data:
        # no unique device identifier
        return
    instance = str(data["id"])

    if "channel" not in data:
        # missing channel
        return
    channel = str(data["channel"])

    # detect known attributes
    for key in data.keys():
        if key in mappings:
            publish_config(mqttc, key, manmodel, instance, channel, mappings[key])


def rtl_433_bridge():
    """Run a MQTT Home Assistant auto discovery bridge for rtl_433."""
    mqttc = mqtt.Client()
    mqttc.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    mqttc.on_connect = mqtt_connect
    mqttc.on_disconnect = mqtt_disconnect
    mqttc.on_message = mqtt_message
    mqttc.will_set("/".join([MQTT_TOPIC, "status"]), payload="offline", qos=0, retain=True)
    mqttc.connect_async(MQTT_HOST, MQTT_PORT, 60)
    mqttc.loop_start()

    while True:
        time.sleep(1)


def run():
    """Run main or daemon."""
    # with daemon.DaemonContext(files_preserve=[sock]):
    #  detach_process=True
    #  uid
    #  gid
    #  working_directory
    rtl_433_bridge()


if __name__ == "__main__":
    run()