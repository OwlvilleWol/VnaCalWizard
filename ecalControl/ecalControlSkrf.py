from .abstract import ECalHalAbc
from .abstract import CorrectionSetScope
from .ecalCorrectionSetSkrf import ECalCorrectionSetSk
from .ecalControlBase import ECalControl

class ECalControlSk(ECalControl):
    def __init__(self, hal: ECalHalAbc):
        super().__init__(hal)


    def _readCorrectionSets(self):
        self._correctionSets.update({CorrectionSetScope.PORT_A: ECalCorrectionSetSk(self, ECalControl._EEPROM_ADDR_CORRSET1, CorrectionSetScope.PORT_A)})
        self._correctionSets.update({CorrectionSetScope.PORT_B: ECalCorrectionSetSk(self, ECalControl._EEPROM_ADDR_CORRSET2, CorrectionSetScope.PORT_B)})
        self._correctionSets.update({CorrectionSetScope.THRU_AB: ECalCorrectionSetSk(self, ECalControl._EEPROM_ADDR_CORRSET3, CorrectionSetScope.THRU_AB)})
        self._correctionSets.update({CorrectionSetScope.VERIFY_AB: ECalCorrectionSetSk(self, ECalControl._EEPROM_ADDR_CORRSET4, CorrectionSetScope.VERIFY_AB)})

    
    @property
    def correctionSets(self) -> dict[CorrectionSetScope, ECalCorrectionSetSk]:
        return self._correctionSets