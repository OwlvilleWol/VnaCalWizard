from .abstract import ECalCorrectionSetAbc
from .abstract import ECalStandardAbc

class ECalStandard(ECalStandardAbc):
    '''
    Represents a single one- or multi-port calibration standard in the ECal
    '''

    def __init__(self, set: "ECalCorrectionSetAbc", id: int, index: int) -> None:
        self._id = id
        self._set = set
        self._indexInEEPROM = index

    def activate(self) -> None:
        self._set.ecal.setGates(self._id)

    @property
    def id(self) -> int:
        return self._id


    def fetchDataFromEEPROM(self):
        numFrequencies = self._set.ecal.numFrequencies

        baseAddress = self._set.dataAddrInEEPROM + self._indexInEEPROM * self._set.paramsPerPointPerStandard * numFrequencies * 8

        table = []
        for i in range(numFrequencies):
            row = []
            for j in range((self._set.numPorts)**2):
                real, imag = self._set.ecal.readValueFromFlash(baseAddress + j*numFrequencies*8 + i*8,'f') , self._set.ecal.readValueFromFlash(baseAddress + j*numFrequencies*8 + i*8 + 4,'f')
                row.append(complex(real, imag))
            table.append(row)

        return table