#!/bin/sh
rtl_433 \
-F mqtt://$MQTT_HOST:$MQTT_PORT,user=$MQTT_USERNAME,pass=$MQTT_PASSWORD,events=$MQTT_TOPIC/events,states=$MQTT_TOPIC/states,devices=$MQTT_TOPIC[/model][/id][/channel:0] \
-M time \
-M protocol \
-M level \
| python3 /scripts/rtl_433_mqtt_hass.py