from network import LoRa
from pysense import Pysense # Import para lectura de temperatura
from SI7006A20 import SI7006A20 # Import para lectura de temperatura y humedad
from LTR329ALS01 import LTR329ALS01 # Import para sensor de luminosidad
import socket
import time
import pycom
import json
import ubinascii
import struct

from CayenneLPP import CayenneLPP

# Variables globales
py = Pysense() # Objeto que se usa para leer los sensores de la placa Pysense
color_led = 0xFF0000 # Color por defecto del LED (rojo), encender con pycom.rgbled(color_led) (se actualiza por sub)
led_on = False # Booleano para imprimir por consola si se enciende y se apaga solo cuando cambia
umbral_luminosidad = 50.0 # Umbral a partir del cual se enciende el LED en modo AUTO
intervalo_sec = 1 # Intervalo entre lectura de sensores y envío al broker
intervalo_envio_recepcion = 5 # Cada cuántas iteraciones del bucle principal se envía
contador_enviar = intervalo_envio_recepcion # Empezamos directamente enviando y recibiendo

# Configuración para LoRa
app_eui = ubinascii.unhexlify('0000000000000000')  # AppEUI en binario, este debe ser registrado en TTN
app_key = ubinascii.unhexlify('1DAEB0E97941F6B16CAE55CA2E585B4E')  # AppKey en binario, este debe ser registrado en TTN
dev_eui = ubinascii.unhexlify('EB0E40B3430876EA')  # AppEUI en binario, este debe ser registrado en TTN


def leer_temperatura():
    si = SI7006A20(py) # Inicializar sensor de temperatura
    temp = si.temperature() #Lectura de temperatura
    humidity = si.humidity() #Lectura de humedad
    #print("Temperatura:",temp,"C")
    return temp, humidity

def leer_luminosidad():
    li = LTR329ALS01(py) # Inicializar sensor de luminosidad
    lights = li.light() # Lectura de la luminosidad
    #print("Nivel de luz:",lights[0],lights[1])
    return lights

# Programa principal
pycom.heartbeat(False) # Apagar el heartbeat del LED
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868) # Inicializar antena LoRa
lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_eui, app_key), timeout=0)
while not lora.has_joined():
    time.sleep(2.5)
    print('Conectando con red LoRa...')
print('✅ Contectado a red LoRa')

# Crear socket LoRa
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
#s.setblocking(True)


# Bucle principal: cada segundo lectura de sensores, control del led si está en modo automático
while True:
    temp, humidity = leer_temperatura()
    lum = leer_luminosidad()

    if lum[0] > umbral_luminosidad or lum[1] > umbral_luminosidad:
        if not led_on: # Solo se imprime cuando cambia de False a True en modo AUTO
            print("Encendiendo LED")
        led_on = True
        pycom.rgbled(color_led)
    else:
        if led_on : # Solo se imprime cuando cambia de True a False en modo AUTO
            print("Apagando LED")
        led_on = False
        pycom.rgbled(0x0)

    print("Enviando/recibiendo en",intervalo_envio_recepcion-contador_enviar,"s.")

    if contador_enviar == intervalo_envio_recepcion: # Cada 5 segundos del bucle enviamos y recibimos
        contador_enviar = 0
        # Componer mensaje binario con los datos tomados de los sensores
        # Empaquetar los datos en el formato CayenneLPP
        lpp = CayenneLPP() # Objeto para empaquetar los datos a enviar segundo el protocolo CayenneLPP

        print('Temperatura🌡: ',temp,'\tHumedad Relativa:',humidity,'\tLuminosidad💡: ',lum[0],' - ',lum[1])
        lpp.add_temperature(1,temp)
        lpp.add_relative_humidity(2,humidity)
        lpp.add_luminosity(3,lum[0])
        lpp.add_luminosity(4,lum[1])
        bytes_enviar = lpp.get_buffer() #Obtener los datos empaquetados

        # Enviar los datos al broker
        print("Bytes a enviar: ",bytes_enviar)
        s.setblocking(False) # Evitar bloquearse para siempre si no recibe datos
        s.send(bytes_enviar)

        data = s.recv(64) # Recibir hasta 64 bytes
        if data != b'': # Si hemos recibido un color nuevo
            print('🆕 Recibido color',data)
            # color_led = int("0x"+data.decode("utf-8",64)) # Decodificar como base64
            color_led = int.from_bytes(data,"big") # Decodificar como entero

    contador_enviar = contador_enviar + 1
    time.sleep(intervalo_sec)