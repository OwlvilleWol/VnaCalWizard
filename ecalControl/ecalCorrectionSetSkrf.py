
import math

from .abstract import ECalControlAbc
from .abstract import CorrectionSetScope
from .ecalCorrectionSetBase import ECalCorrectionSet
from .ecalStandardSkrf import ECalStandardSk

class ECalCorrectionSetSk (ECalCorrectionSet):
    '''
    Group of standards in the ECal
    E.g. Port1 standards, Port2 standards, Thru standard(s), Verify standard(s)
    Initialized standards to skrf derived class
    '''
    def __init__(self, ecal: ECalControlAbc, address: int, scope: CorrectionSetScope) -> None:
        super().__init__(ecal, address, scope)

    def _initStandards(self):
        self._Standards = dict()
        for i in range(self._numStandards):
            id = self._ecal.readValueFromFlash(self._standardsAddr + 2*i, "H")
            self._Standards.update({id : ECalStandardSk(self, id, i)})  