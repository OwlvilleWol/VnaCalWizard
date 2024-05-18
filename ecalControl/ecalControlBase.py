
import struct
from dataclasses import dataclass
import re
from pathlib import Path
from typing import List

from .abstract import ECalHalAbc
from .abstract import ECalControlAbc
from .abstract import ECalCorrectionSetAbc
from .abstract import ConnectorGender
from .abstract import CorrectionSetScope
from .abstract import RfPort
from .ecalCorrectionSetBase import ECalCorrectionSet



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
        
        self._ports = []

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

    def _readCorrectionSets(self):
        self._correctionSets.update({CorrectionSetScope.PORT_A, ECalCorrectionSet(self, ECalControl._EEPROM_ADDR_CORRSET1)})
        self._correctionSets.update({CorrectionSetScope.PORT_B, ECalCorrectionSet(self, ECalControl._EEPROM_ADDR_CORRSET2)})
        self._correctionSets.update({CorrectionSetScope.THRU_AB, ECalCorrectionSet(self, ECalControl._EEPROM_ADDR_CORRSET3)})
        self._correctionSets.update({CorrectionSetScope.VERIFY_AB, ECalCorrectionSet(self, ECalControl._EEPROM_ADDR_CORRSET4)})

    def readValueFromFlash(self, addr, format = "c"):
        valueBytes = bytes()
        noBytesPerValue = struct.calcsize(format)

        for j in range(noBytesPerValue):
            valueBytes += bytes([self.hal._readByteFromFlash(addr + j)])
        return struct.unpack(format, valueBytes)[0]

    def readStringFromFlash(self, addr, maxlen = 255):        
        readBytes = bytes()
        for j in range(maxlen):
            readInt = self.hal._readByteFromFlash(addr + j)
            if readInt == 0: break
            readBytes += bytes([readInt])
        try:
            return readBytes.decode()
        except:
            return ""

    def readArrayFromFlash(self, addr, len, format = "i"):

        valueList = []
        noBytesPerValue = struct.calcsize(format)
        for i in range(len):
            valueList += self.readValueFromFlash(addr + i*noBytesPerValue, format)
        return valueList
    

    def _readECalInfo(self):
        self._numPoints = self.readValueFromFlash(ECalControl._EEPROM_ADDR_NOPOINTS,"H")
        self._warmupTime = self.readValueFromFlash(ECalControl._EEPROM_ADDR_WARMUP,"H")
        self._model = self.readStringFromFlash(ECalControl._EEPROM_ADDR_MODELNO, maxlen = 37)
        self._serialNo = self.readStringFromFlash(ECalControl._EEPROM_ADDR_SERNO, maxlen = 7)
        self._connectorType = self.readStringFromFlash(ECalControl._EEPROM_ADDR_CONNTYPE, maxlen = 21)
        self._lastCalibration = self.readStringFromFlash(ECalControl._EEPROM_ADDR_LASTCERT, maxlen = 33)
        self._numFrequencies = self.readValueFromFlash(ECalControl._EEPROM_ADDR_FREQ_NO,"H")

        tokens = re.split("([MF])",self.connectorType.split()[0])
        self._ports.append(RfPort("Port A", tokens[0], ConnectorGender.MALE if tokens[1] == "M" else ConnectorGender.FEMALE, device=self))
        self._ports.append(RfPort("Port B", tokens[2], ConnectorGender.MALE if tokens[3] == "M" else ConnectorGender.FEMALE, device=self))


    @property
    def ports(self) -> List[RfPort]:
        return self._ports

    @property
    def port_A(self) -> RfPort:
        try: return self._ports[0]
        except: return None

    @property
    def port_B(self) -> RfPort:
        try: return self._ports[1]
        except: return None

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