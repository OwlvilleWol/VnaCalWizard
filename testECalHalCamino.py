import camino


serialPort = "COM5"
baud = 115200


connection = camino.SerialConnection(serialPort, baud)
arduino = camino.Arduino(connection)

addr : int = 225

b = arduino.readByteFromFlash(list(addr.to_bytes(3, byteorder='little')), out=bytes)
print(int.from_bytes(b,byteorder='little', signed=False))
