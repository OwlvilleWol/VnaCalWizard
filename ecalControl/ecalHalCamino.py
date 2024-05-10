import camino
import time
from typing import List

from .ecalHalBase import ECalHal

class TypedArduino(camino.Arduino):
    def __init__(self, serial, address=0):
        super().__init__(serial, address)

    def resetECalT(self) -> None:
        return self.resetECal()

    def readByteFromFlashT(self, address: int) -> int:
        b = self.readByteFromFlash(list(address.to_bytes(3,byteorder='little',signed=False)), out=bytes)
        i = int.from_bytes(b, byteorder="little", signed=False)
        return i
    
    def readNextByteFromFlashT(self) -> int:
        b = self.readNextByteFromFlash(out=bytes)
        i = int.from_bytes(b, byteorder="little", signed=False)
        return i
    
    def writeByteT(self, address: int, value: int) -> None:
        return self.writeByte(address, value)
    
    

class ECalHalCamino(ECalHal):

    def __init__(self, serialPort: str, baud: int=115200):

        self._connection = None
        self._arduino = None
        
        try:
            self._connection = camino.SerialConnection(serialPort, baud)
            self._arduino = TypedArduino(self._connection)
                
        except Exception as e:
            self._connection = None
            self._arduino = None
            raise e
        
        self._last_eeprom_address = 0xffff
        self._arduino.resetECalT()
            

    def __del__(self) -> None:
        pass

    def _reset(self):
        self._arduino.resetECalT()
        
    def _writeByte(self,addr: int, value: int) -> None:
        self._arduino.writeByteT(addr,value)

    def _readByteFromFlash(self, addr) -> int:
        if addr == self._last_eeprom_address + 1:
            self._last_eeprom_address += 1
            return self._arduino.readNextByteFromFlashT()
        else:
            self._last_eeprom_address = addr
            return self._arduino.readByteFromFlashT(addr)
        
