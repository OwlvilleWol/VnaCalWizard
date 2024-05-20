
import struct

from pathlib import Path
from .abstract import ECalHalAbc
from .abstract import ECalControlAbc
from .abstract import ECalCorrectionSetAbc
from .abstract import CorrectionSetScope
from .ecalCorrectionSetBase import ECalCorrectionSet
from typing import List, Any



class ECalControl(ECalControlAbc):

    def __init__(self, hal: ECalHalAbc):
        self.hal = hal

        self._numPoints = 0
        self._numFrequencies = 0
        self._warmupTime = 0
        self._model = ""
        self._serialNo = ""
        self._connectorType = ""
        self._lastCalibration = ""
        self._correctionSets = dict()
        self._frequencyList = []
        self._dataFolderPath = Path(__file__).parent.resolve().joinpath("data")

        self._readECalInfo()
        self._readCorrectionSets()


    @property
    def frequencyList(self) -> list[float]:
        if (len(self._frequencyList) == 0): #frequency list is empty, read it
            freqListAddr = self.readValueFromFlash(ECalControl._EEPROM_ADDR_FREQ_ADDR,"I")
            self._frequencyList = [self.readValueFromFlash(freqListAddr + i*8,"d") for i in range(self.numFrequencies)]
        return self._frequencyList

    def setGates(self, value: int) -> None:
        self.hal._writeByte(ECalHalAbc._MUX_ADDR_GATES_1_8, value & 0x00ff)
        self.hal._writeByte(ECalHalAbc._MUX_ADDR_GATES_9_16, (value & 0xff00) >> 8)

    def isolate(self) -> None:
        self.setGates(0xffff)

    def _readCorrectionSets(self) -> None:
        self._correctionSets[CorrectionSetScope.PORT_A] = ECalCorrectionSet(self, ECalControl._EEPROM_ADDR_CORRSET1)
        self._correctionSets[CorrectionSetScope.PORT_B] = ECalCorrectionSet(self, ECalControl._EEPROM_ADDR_CORRSET2)
        self._correctionSets[CorrectionSetScope.THRU_AB] = ECalCorrectionSet(self, ECalControl._EEPROM_ADDR_CORRSET3)
        self._correctionSets[CorrectionSetScope.VERIFY_AB] = ECalCorrectionSet(self, ECalControl._EEPROM_ADDR_CORRSET4)

    def readValueFromFlash(self, addr, format = "c") -> Any:
        valueBytes = bytes()
        noBytesPerValue = struct.calcsize(format)

        for j in range(noBytesPerValue):
            valueBytes += bytes([self.hal._readByteFromFlash(addr + j)])
        return struct.unpack(format, valueBytes)[0]

    def readStringFromFlash(self, addr, maxlen = 255) -> str:        
        readBytes = bytes()
        for j in range(maxlen):
            readInt = self.hal._readByteFromFlash(addr + j)
            if readInt == 0: break
            readBytes += bytes([readInt])
        try:
            return readBytes.decode()
        except:
            return ""

    def readArrayFromFlash(self, addr, len, format = "i") -> List[Any]:

        valueList = []
        noBytesPerValue = struct.calcsize(format)
        for i in range(len):
            valueList += self.readValueFromFlash(addr + i*noBytesPerValue, format)
        return valueList
    

    def _readECalInfo(self) -> None:
        self._numPoints = self.readValueFromFlash(ECalControl._EEPROM_ADDR_NOPOINTS,"H")
        self._warmupTime = self.readValueFromFlash(ECalControl._EEPROM_ADDR_WARMUP,"H")
        self._model = self.readStringFromFlash(ECalControl._EEPROM_ADDR_MODELNO, maxlen = 37)
        self._serialNo = self.readStringFromFlash(ECalControl._EEPROM_ADDR_SERNO, maxlen = 7)
        self._connectorType = self.readStringFromFlash(ECalControl._EEPROM_ADDR_CONNTYPE, maxlen = 21)
        self._lastCalibration = self.readStringFromFlash(ECalControl._EEPROM_ADDR_LASTCERT, maxlen = 33)
        self._numFrequencies = self.readValueFromFlash(ECalControl._EEPROM_ADDR_FREQ_NO,"H")


    @property
    def model(self) -> str:
        return self._model

    @property
    def serialNo(self) -> str:
        return self._serialNo

    @property
    def connectorType(self) -> str:
        return self._connectorType
    
    @property
    def numFrequencies(self) -> int:
        return self._numFrequencies
    
    @property
    def correctionSets(self) -> dict[CorrectionSetScope, ECalCorrectionSetAbc]:
        return self._correctionSets
    
    @property
    def dataFolderPath(self) -> Path:
        return self._dataFolderPath