from .abstract import ECalHalAbc
from .abstract import CorrectionSetScope
from .ecalCorrectionSetSkrf import ECalCorrectionSetSk
from .ecalControlBase import ECalControl
from skrf import Frequency, Network
from typing import List
from rfUtils import RfPort, ConnectorGender, RfNPort, RfPath, FrequencyEx
import re

class ECalControlSk(ECalControl, RfNPort):
    def __init__(self, hal: ECalHalAbc):
        ECalControl.__init__(self, hal)
        RfNPort.__init__(self)

        self._ports : dict[str, RfPort] = {}


    def _readECalInfo(self) -> None:
        super()._readECalInfo()

        tokens = re.split("([MF])",self.connectorType.split()[0])
        self.ports["A"] = RfPort("Port A", tokens[0], ConnectorGender.MALE if tokens[1] == "M" else ConnectorGender.FEMALE, device=self)
        self.ports["B"] = RfPort("Port B", tokens[2], ConnectorGender.MALE if tokens[3] == "M" else ConnectorGender.FEMALE, device=self)


    def _readCorrectionSets(self) -> None:
        self._correctionSets[CorrectionSetScope.PORT_A] = ECalCorrectionSetSk(self, ECalControl._EEPROM_ADDR_CORRSET1, CorrectionSetScope.PORT_A)
        self._correctionSets[CorrectionSetScope.PORT_B] = ECalCorrectionSetSk(self, ECalControl._EEPROM_ADDR_CORRSET2, CorrectionSetScope.PORT_B)
        self._correctionSets[CorrectionSetScope.THRU_AB] = ECalCorrectionSetSk(self, ECalControl._EEPROM_ADDR_CORRSET3, CorrectionSetScope.THRU_AB)
        self._correctionSets[CorrectionSetScope.VERIFY_AB] = ECalCorrectionSetSk(self, ECalControl._EEPROM_ADDR_CORRSET4, CorrectionSetScope.VERIFY_AB)

    
    @property
    def correctionSets(self) -> dict[CorrectionSetScope, ECalCorrectionSetSk]:
        return self._correctionSets
    
    @property
    def port(self) -> dict[str, RfPort]:
        return self._ports

    @property
    def ports(self) -> List[RfPort]:
        return list(self._ports.values)

    def network(self, path : RfPath) -> Network:
        ...

    def frequency(self, path : RfPath) -> FrequencyEx:
        ...

    @property
    def paths(self) -> List[RfPath]:
        ...