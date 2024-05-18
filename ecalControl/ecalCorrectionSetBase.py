import math

from .abstract import ECalControlAbc
from .abstract import ECalCorrectionSetAbc
from .abstract import ECalStandardAbc
from .abstract import CorrectionSetScope
from .ecalStandardBase import ECalStandard


class ECalCorrectionSet(ECalCorrectionSetAbc):
    '''
    Group of standards in the ECal
    E.g. Port1 standards, Port2 standards, Thru standard(s), Verify standard(s)
    '''

    def __init__(self, ecal: "ECalControlAbc" , address: int, scope: CorrectionSetScope) -> None:

        self._ecal = ecal
        self._numStandards = ecal.readValueFromFlash(address, "H")
        self._pointsPerStandard = ecal.readValueFromFlash(address + 2, "H")
        self._paramsPerPoint = ecal.readValueFromFlash(address + 4, "H")
        self._standardsAddr = ecal.readValueFromFlash(address + 6, "I")
        self._dataAddr = ecal.readValueFromFlash(address + 10, "I")
        self._scope : CorrectionSetScope = scope

        self._initStandards()

        self._StandardsIterator = None

    @property
    def ecal(self) -> ECalControlAbc:
        return self._ecal

    def __iter__(self):
        self._StandardsIterator = iter(self._Standards)
        return self
    
    def __next__(self) -> ECalStandardAbc:
        return self._Standards[next(self._StandardsIterator)]
    
    def __getitem__(self, standardId: int) -> ECalStandardAbc:
        return self._Standards[standardId]
    
    def _initStandards(self):
        self._Standards = dict()
        for i in range(self._numStandards):
            id = self._ecal.readValueFromFlash(self._standardsAddr + 2*i, "H")
            self._Standards.update({id : ECalStandard(self, id)})
    
    @property
    def paramsPerPointPerStandard(self) -> int:
        return int(self._paramsPerPoint / self._numStandards)
            
    @property
    def numPorts(self) -> int:
        numP = int(math.sqrt(self.paramsPerPointPerStandard))
        if (numP != math.sqrt(self.paramsPerPointPerStandard)): raise Exception("Invalid number of ports")
        return numP 

    @property
    def dataAddrInEEPROM(self) -> int:
        return self._dataAddr

    @property
    def scope(self) -> CorrectionSetScope:
        return self._scope
    
    @property
    def paramsPerPoint(self) -> int:
        return self._paramsPerPoint
