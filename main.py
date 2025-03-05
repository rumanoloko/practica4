#1.- Importación de librerías
from network import LoRa
from lib.pysense import Pysense # Placa base para sensores
from lib.SI7006A20 import SI7006A20 # Import para sensores de temperatura y humedad
from lib.LTR329ALS01 import LTR329ALS01 # Import para sensor de luminosidad
import socket
import time
import pycom # Control del LED RGB
import json
import ubinascii # Manejo de datos binarios
import struct # Para empaquetar datos
from lib.CayenneLPP import CayenneLPP # Protocolo de datos para IoT

#2.- Variables globales
py = Pysense() # Objeto que se usa para leer los sensores de la placa Pysense. Inicializa la placa Pysense.
color_led = 0xFF0000 # Color por defecto del LED (rojo), encender con pycom.rgbled(color_led) 
led_on = False # Booleano para imprimir por consola si se enciende y se apaga solo cuando cambia
umbral_luminosidad = 15.0 # Umbral a partir del cual se enciende el LED en modo AUTO
intervalo_sec = 1 # Intervalo entre lectura de sensores y envío al broker. Cada cuánto tiempo (en segundos) se leen los sensores.
intervalo_envio_recepcion = 5 # Cada cuántas iteraciones del bucle principal se envía. Cada cuántas lecturas se envían los datos por LoRa.
contador = intervalo_envio_recepcion # Empezamos directamente enviando y recibiendo


#3.- Configuración para LoRaWAN
dev_eui = ubinascii.unhexlify('70B3D57ED006E8E2') #Identificador único del dispositivo LoRa.
app_eui = ubinascii.unhexlify('0000000000000000') # Identificador de la aplicación en la red LoRaWAN.
app_key = ubinascii.unhexlify('22F98CA3501C2C0D41A0D9ECA0A7E27C') #Clave de seguridad para autenticarse en la red.

#4.- Funciones para leer sensores
# ========== FUNCIÓN PARA LECTURA DE SENSORES ==========
def leer_temperatura():
    si = SI7006A20(py) # Inicializar sensor de temperatura
    temperatura = si.temperature() #Lectura de temperatura
    humidity = si.humidity() #Lectura de humedad
    return temperatura, humidity

def leer_luminosidad():
    li = LTR329ALS01(py) # Inicializar sensor de luminosidad
    luz = li.light() # Lectura de la luminosidad
    return luz

# 5.- Inicialización de LoRa
pycom.heartbeat(False) # Apagar el heartbeat del LED. Detienes ese parpadeo ( automáticamente en color azul cada pocos segundos), permitiendo que puedas controlar manualmente el color del LED pycom.rgbled(color).
# Inicialización de LoRa en modo LORAWAN.
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868) # Inicializar antena LoRa
# Unir a la red usando OTAA (Over the Air Activation)
lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_eui, app_key), timeout=0)
# Esperar hasta que el modulo se una a la red
while not lora.has_joined():
    time.sleep(2.5)
    print('Conectando con red LoRa...')
print('Contectado a red LoRa')

#6. Creación del socket LoRa
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)


#7- Bucle Principal
# Bucle principal: cada segundo lectura de sensores, control del led si está en modo automático
while True:
    temp, humidity = leer_temperatura()
    lum = leer_luminosidad()

#8.- Control del LED según la luminosidad
    if lum[0] < umbral_luminosidad: #""" and lum[1] < umbral_luminosidad """
         # Solo se imprime cuando cambia de False a True en modo AUTO
        print("Encendiendo LED")
        led_on = True
        pycom.rgbled(color_led) #controlar manualmente el color del LED
    if lum[0] > umbral_luminosidad: #""" and lum[1] < umbral_luminosidad """
        # Solo se imprime cuando cambia de False a True en modo AUTO
        print("Apagando LED")
        led_on = False
        pycom.rgbled(0x0) 
 

    print("Enviando/recibiendo en",intervalo_envio_recepcion-contador,"s.")
#9.- Envío de datos cada 5 ciclos
    if contador == intervalo_envio_recepcion: # Cada 5 segundos del bucle enviamos y recibimos
        contador = 0
        # Formar mensaje binario con los datos tomados de los sensores
        # Empaquetar los datos en el formato CayenneLPP
        lpp = CayenneLPP() # Objeto para empaquetar los datos a enviar segundo el protocolo CayenneLPP

        print('Temperatura: ',temp,'\tHumedad:',humidity,'\tLuminosidad: ',lum[0],' - ',lum[1])
        lpp.add_temperature(1,temp)
        lpp.add_relative_humidity(2,humidity)
        # dos canales diferentes:
        lpp.add_luminosity(3,lum[0]) #Mide la intensidad de luz en el espectro visible e infrarrojo.
        lpp.add_luminosity(4,lum[1]) #Mide solo la luz infrarroja.
        bytes_enviar = lpp.get_buffer() #Obtener los datos empaquetados

    #Cada 5 iteraciones, empaqueta los datos usando CayenneLPP
        # Enviar los datos al broker
        print("Bytes a enviar: ",bytes_enviar)
        s.setblocking(False) # Evitar bloquearse para siempre si no recibe datos
        s.send(bytes_enviar)
    #Envía los datos al servidor LoRa.
        data = s.recv(64) # Recibir hasta 64 bytes de datos desde el socket LoRa. 
                          #Si no hay datos disponibles, devuelve una cadena de bytes vacía (b'').
                          
        
        if data != b'': # Comprueba si la variable data no está vacía. Si hemos recibido un color nuevo
            print('Recibido color',data)
            color_led = int.from_bytes(data,"big") # Decodificar como entero
        print('Color recibido ',color_led)
            #Si data contiene algún valor, significa que se ha recibido información desde el servidor LoRa.
            #Si data está vacía (b''), significa que no se ha recibido ninguna respuesta y no se ejecutará el bloque de código dentro del if.
    #Si recibe datos, los interpreta como un nuevo color para el LED.
    contador = contador + 1
    time.sleep(intervalo_sec)