from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List
from pathlib import Path


class CorrectionSetScope(Enum):
    PORT_A = 1
    PORT_B = 2
    THRU_AB = 3
    VERIFY_AB = 4

class ECalPort(Enum):
    A = CorrectionSetScope.PORT_A
    B = CorrectionSetScope.PORT_B


class ECalHalAbc(ABC):

    _MUX_ADDR_FLASH_ADDR_0_7 = 2
    _MUX_ADDR_FLASH_ADDR_8_15 = 3
    _MUX_ADDR_FLASH_ADDR_16_17 = 4

    _MUX_ADDR_GATES_1_8 = 0
    _MUX_ADDR_GATES_9_16 = 1

    _MUX_ADDR_FLASH_DATA = 7

    @abstractmethod
    def __init__(self) -> None:
        pass 

    @abstractmethod
    def _writeByte(self,addr: int, value: int) -> None:
        pass

    @abstractmethod
    def _readByteFromFlash(self, addr: int) -> int:
        pass


class ECalControlAbc(ABC):

    _EEPROM_ADDR_NOPOINTS = 0x00DC
    _EEPROM_ADDR_WARMUP = 0x00DE
    _EEPROM_ADDR_MODELNO = 0x00F0
    _EEPROM_ADDR_SERNO = 0x0064
    _EEPROM_ADDR_CONNTYPE = 0x0070
    _EEPROM_ADDR_LASTCERT = 0x0084

    _EEPROM_ADDR_CORRSET1 = 0x0196
    _EEPROM_ADDR_CORRSET2 = 0x01A4
    _EEPROM_ADDR_CORRSET3 = 0x01B2
    _EEPROM_ADDR_CORRSET4 = 0x01C0

    _EEPROM_ADDR_FREQ_NO = 0x0190
    _EEPROM_ADDR_FREQ_ADDR = 0x0192


    @abstractmethod
    def __init__(self, hal: ECalHalAbc) -> None:
        pass

    @property
    @abstractmethod
    def frequencyList(self) -> list[float]:
        pass

    @abstractmethod
    def setGates(self, value: int) -> None:
        pass

    @abstractmethod
    def readValueFromFlash(self, addr, format = "c") -> any:
        pass

    @abstractmethod
    def readStringFromFlash(self, addr, maxlen = 255) -> str:  
        pass 

    @abstractmethod  
    def readArrayFromFlash(self, addr, len, format = "i") -> List[any]:
        pass

    @property
    @abstractmethod
    def numFrequencies(self) -> int:
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        pass

    @property
    @abstractmethod
    def serialNo(self) -> str:
        pass

    @property
    @abstractmethod
    def connectorType(self) -> str:
        pass

    @property
    @abstractmethod
    def dataFolderPath(self) -> Path:
        pass

    @property
    @abstractmethod
    def correctionSets(self) -> dict[CorrectionSetScope, "ECalCorrectionSetAbc"]:
        pass

    
class ECalCorrectionSetAbc(ABC):
    '''
    Group of standards in the ECal
    E.g. Port1 standards, Port2 standards, Thru standard(s), Verify standard(s)
    '''
    @abstractmethod
    def __init__(self, ecal: "ECalControlAbc" , address: int, scope: CorrectionSetScope) -> None:
        pass

    @abstractmethod
    def __iter__(self) -> "ECalCorrectionSetAbc":
        pass
    
    @abstractmethod
    def __next__(self) -> "ECalStandardAbc":
        pass
    
    @abstractmethod
    def __getitem__(self, standardId: int) -> "ECalStandardAbc":
        pass
    
    @abstractmethod
    def _initStandards(self) -> None:
        pass
            
    @property
    @abstractmethod
    def numPorts(self) -> int:
        pass

    @property
    @abstractmethod
    def ecal(self) -> ECalControlAbc:
        pass

    @property
    @abstractmethod
    def dataAddrInEEPROM(self) -> int:
        pass

    @property
    @abstractmethod
    def scope(self) -> CorrectionSetScope:
        pass

    @property
    @abstractmethod
    def paramsPerPoint(self) -> int:
        pass

    @property
    def paramsPerPointPerStandard(self) -> int:
        pass
    


class ECalStandardAbc(ABC):
    '''
    Represents a single one- or multi-port calibration standard in the ECal
    '''

    @abstractmethod
    def __init__(self, set: "ECalCorrectionSetAbc", id: int, index: int) -> None:
        pass

    @abstractmethod
    def activate(self) -> None:
        pass

    @property
    @abstractmethod
    def id(self) -> int:
        pass

    @abstractmethod
    def fetchDataFromEEPROM(self) -> List[List[complex]]:
        pass
