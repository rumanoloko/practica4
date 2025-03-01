from network import LoRa
from pysense import Pysense
from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01
import socket
import time
import pycom
import ubinascii
import json
from CayenneLPP import CayenneLPP

# Variables globales
py = Pysense()
color_led = 0xFF0000  # Color por defecto del LED (rojo)
led_on = False  # Estado del LED
umbral_luminosidad = 50.0  # Umbral para encender el LED
intervalo_sec = 1  # Intervalo de lectura de sensores
intervalo_envio_recepcion = 5  # Cada cuántas iteraciones se envía un mensaje
contador_enviar = intervalo_envio_recepcion  # Empezar enviando

# Configuración LoRa (OTAA)
app_eui = ubinascii.unhexlify('0101010101010101')  # JoinEUI (AppEUI)
app_key = ubinascii.unhexlify('2AC0958B5EE8D8D891B1FC013F917001')  # AppKey
dev_eui = ubinascii.unhexlify('70B3D549927AC394')  # DevEUI

# Función para leer temperatura y humedad
def leer_temperatura():
    si = SI7006A20(py)
    temp = si.temperature()
    humidity = si.humidity()
    return temp, humidity

# Función para leer luminosidad
def leer_luminosidad():
    li = LTR329ALS01(py)
    lights = li.light()
    return lights

# Inicializar LoRaWAN en modo OTAA
pycom.heartbeat(False)  # Apagar el heartbeat del LED
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)

print("🔗 Intentando conectar con la red LoRa...")
lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_eui, app_key), timeout=0)

while not lora.has_joined():
    time.sleep(2.5)
    print('⏳ Conectando con red LoRa...')
print('✅ Conectado a la red LoRa')

# Crear socket LoRa
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)  # Configurar Data Rate

# Bucle principal
while True:
    temp, humidity = leer_temperatura()
    lum = leer_luminosidad()

    # Control del LED basado en la luminosidad
    if lum[0] > umbral_luminosidad or lum[1] > umbral_luminosidad:
        if not led_on:
            print("🔴 Encendiendo LED (Baja luminosidad)")
        led_on = True
        pycom.rgbled(color_led)
    else:
        if led_on:
            print("⚫ Apagando LED (Suficiente luz)")
        led_on = False
        pycom.rgbled(0x000000)

    print("📡 Enviando/recibiendo en", intervalo_envio_recepcion - contador_enviar, "s.")

    if contador_enviar == intervalo_envio_recepcion:  # Cada 5 iteraciones se envía
        contador_enviar = 0

        # Empaquetar los datos en CayenneLPP
        lpp = CayenneLPP()
        lpp.add_temperature(1, temp)
        lpp.add_relative_humidity(2, humidity)
        lpp.add_luminosity(3, lum[0])
        lpp.add_luminosity(4, lum[1])
        bytes_enviar = lpp.get_buffer()

        # Enviar los datos
        print("📤 Enviando datos LoRa:", bytes_enviar)
        s.setblocking(False)
        s.send(bytes_enviar)

        # Recibir datos
        data = s.recv(64)
        if data:
            print("📥 Mensaje recibido:", data)

            # Simular la decodificación del Join Accept Message
            try:
                join_accept_msg = {
                    "end_device_ids": {
                        "device_id": "dev1",
                        "application_ids": {"application_id": "app1"},
                        "dev_eui": dev_eui.hex().upper(),
                        "join_eui": app_eui.hex().upper(),
                        "dev_addr": "00BCB929"
                    },
                    "correlation_ids": ["as:up:01..."],
                    "received_at": "2025-02-28T15:15:00Z",
                    "join_accept": {
                        "session_key_id": "AXBSH1Pk6Z0G166...",
                        "received_at": "2025-02-28T15:20:00Z",
                        "attributes": {
                            "key1": "value1",
                            "key2": "value2"
                        }
                    }
                }

                print("🔗 Join Accept Message recibido:")
                print(json.dumps(join_accept_msg, indent=4))

            except Exception as e:
                print("⚠️ Error al procesar el mensaje:", e)

    contador_enviar += 1
    time.sleep(intervalo_sec)
