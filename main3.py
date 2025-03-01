import time
import pycom
from pysense import Pysense
from LIS2HH12 import LIS2HH12
from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01
from MPL3115A2 import MPL3115A2, ALTITUDE, PRESSURE

# Inicializar la placa PySense y los sensores
py = Pysense()
si = SI7006A20(py)
lt = LTR329ALS01(py)
li = LIS2HH12(py)

# Desactivar el LED de heartbeat
pycom.heartbeat(False)

# Ciclo principal para obtener y mostrar datos de los sensores
while True:
    # Imprimir valores del acelerómetro
    print('\n** Acelerómetro 3-ejes (LIS2HH12):')
    print('Aceleración X: %.2f' % li.acceleration()[0])
    print('Aceleración Y: %.2f' % li.acceleration()[1])
    print('Aceleración Z: %.2f' % li.acceleration()[2])
    print('Rol: %.2f' % li.roll())
    print('Pitch: %.2f' % li.pitch())

    # Imprimir valores del sensor de luminosidad (LTR-329ALS-01)
    print('\n** Sensor de Luminosidad Digital (LTR-329ALS-01):')
    print('Luminosidad canal 1: %.2f' % lt.light()[0])
    print('Luminosidad canal 2: %.2f' % lt.light()[1])

    # Imprimir valores del sensor de temperatura y humedad (SI7006A20)
    print('\n** Sensor de Temperatura y Humedad (SI7006A20):')
    print('Humedad: %.2f %%' % si.humidity())
    print('Temperatura: %.2f °C' % si.temperature())

    # Imprimir valores del sensor de presión barométrica (MPL3115A2)
    mpPress = MPL3115A2(py, mode=PRESSURE)
    print('\n** Sensor de Presión Barométrica (MPL3115A2):')
    print('Presión (hPa): %.2f' % (mpPress.pressure() / 100))

    # Imprimir valores de altitud
    mpAlt = MPL3115A2(py, mode=ALTITUDE)
    print('Altitud (m): %.2f' % mpAlt.altitude())
    print('Temperatura (de altitud): %.2f °C' % mpAlt.temperature())

    print("\nEsperando 30 segundos antes de tomar nuevas lecturas...\n")
    time.sleep(30)  # Esperar 30 segundos antes de la próxima lectura
