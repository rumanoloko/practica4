from network import LoRa
from pysense import Pysense
from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01
import socket
import time
import pycom
import json
import ubinascii
import struct

from CayenneLPP import CayenneLPP

# Variables globales
py = Pysense()
color_led = 0xFF0000
led_on = False
umbral_luminosidad = 50.0
intervalo_sec = 1
intervalo_envio_recepcion = 5
contador_enviar = intervalo_envio_recepcion

# Configuración para LoRa
app_eui = ubinascii.unhexlify('0000000000000000')
app_key = ubinascii.unhexlify('1DAEB0E97941F6B16CAE55CA2E585B4E')
dev_eui = ubinascii.unhexlify('EB0E40B3430876EA')

def leer_temperatura():
    si = SI7006A20(py)
    temp = si.temperature()
    humidity = si.humidity()
    return temp, humidity

def leer_luminosidad():
    li = LTR329ALS01(py)
    lights = li.light()
    return lights

pycom.heartbeat(False)
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_eui, app_key), timeout=0)
while not lora.has_joined():
    time.sleep(2.5)
    print('Conectando con red LoRa...')
print('Contectado a red LoRa')

s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

while True:
    temp, humidity = leer_temperatura()
    lum = leer_luminosidad()

    if lum[0] > umbral_luminosidad or lum[1] > umbral_luminosidad:
        if not led_on:
            print("Encendiendo LED")
        led_on = True
        pycom.rgbled(color_led)
    else:
        if led_on:
            print("Apagando LED")
        led_on = False
        pycom.rgbled(0x0)

    print("Enviando/recibiendo en", intervalo_envio_recepcion - contador_enviar, "s.")

    if contador_enviar == intervalo_envio_recepcion:
        contador_enviar = 0
        lpp = CayenneLPP()
        print('Temperatura: ', temp, '\tHumedad Relativa:', humidity, '\tLuminosidad💡: ', lum[0], ' - ', lum[1])
        lpp.add_temperature(1, temp)
        lpp.add_relative_humidity(2, humidity)
        lpp.add_luminosity(3, lum[0])
        lpp.add_luminosity(4, lum[1])
        bytes_enviar = lpp.get_buffer()

        print("Bytes a enviar: ", bytes_enviar)
        s.setblocking(False)
        s.send(bytes_enviar)

        data = s.recv(64)
        if data != b'':
            print('Recibido color', data)
            color_led = int.from_bytes(data, "big")

    contador_enviar += 1
    time.sleep(intervalo_sec)