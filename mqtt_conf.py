from paho.mqtt import client as mqtt_client
from os import getenv
from itertools import product

BROKER = getenv("MQTT_BROKER")
PORT = int(getenv("MQTT_PORT"))
BASE_TOPIC = 'aclearn/qlearning/'
USERNAME = getenv("MQTT_USER")
PASSWORD = getenv("MQTT_PASS")

ocupancia_list = ['POCA', 'MEDIA', 'MUCHA']
temp_in_list = ['T1', 'T2']
temp_ac_list = ['FRIO', 'NEUTRAL', 'CALOR']
periodo_list = ['P1', 'P2', 'P3']
consumo_ac = ['ALTO', 'BAJO']

ACTION = {0: "MANTUVO", 1: "DISMINUCIÓN", 2: "AUMENTO"}
ESTADOS = list(product(ocupancia_list, temp_in_list, temp_ac_list, periodo_list, consumo_ac))

def connect_mqtt() -> mqtt_client:
    def on_connect(client, usedata, flags, rc):
        if rc == 0:
            pass
        else:
            print('La conexion al Broker ha fallado')

    client = mqtt_client.Client("mqtt_aclearn_id")
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.connect(BROKER, PORT)
    return client


def publish(client: mqtt_client, ea,  at):
    client.publish(BASE_TOPIC + "estado_actual", ",".join(map(str, ESTADOS[ea - 1])))
    client.publish(BASE_TOPIC + "accion_realizada", ACTION[at])


def run_publisher(estado_actual, acciones, accion_tomada):
    client = connect_mqtt()
    publish(client, estado_actual, accion_tomada)
    client.loop_start()
