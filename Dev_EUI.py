import ubinascii
from machine import unique_id

devo = ubinascii.hexlify(unique_id()).decode().upper()
print("DevEUI completo:", devo)

def Devo():
    return devo