from skrf import Network, Frequency
import numpy as np
from pathlib import Path

from .ecalStandardBase import ECalStandard
from .abstract import ECalCorrectionSetAbc


class ECalStandardSk(ECalStandard):
    '''
    Represents a single one- or multi-port calibration standard in the ECal
    '''
        
    def __init__(self, set: "ECalCorrectionSetAbc", id: int, index: int) -> None:
        super().__init__(set, id, index)
        self.fetchDataFromTouchstoneFile()

    def fetchDataFromEEPROM(self) -> Network:
        table = super().fetchDataFromEEPROM()

        freq = Frequency.from_f(self._set.ecal.frequencyList)           
        s = np.stack([ np.reshape(row, (self._set.numPorts, self._set.numPorts)) for row in table])
        self._network = Network(f=freq.f, s=s)
        return self._network

    def fetchDataFromTouchstoneFile(self, explicitFilePath: Path = None) -> Network:
        try:
            if explicitFilePath != None:
                self._network = Network(str(explicitFilePath))
            else:
                self._network = Network(str(self._touchstoneFilePath))
            return self._network
        except:
            self._network = None
            return None

    def saveDataToTouchstoneFile(self, explicitFilePath: Path = None):
        path : Path
        if explicitFilePath != None:
            path = explicitFilePath
        else:
            path = self._touchstoneFilePath

        i : int = 0
        if path.exists():
            backup = path.with_suffix(".bak")
            while backup.exists():
                i += 1
                backup = path.with_suffix(".bak" + str(i))
            path.rename(backup)

        self._network.write_touchstone(filename=str(path.stem), dir=str(path.parent))

    @property
    def _touchstoneFilePath(self) -> Path:
        model = self._set.ecal.model
        serno = self._set.ecal.serialNo
        id = "0x{0:04x}".format(self._id)
        fileName = "ECal " + model + " s_n " + serno + " set " + self._set.scope.name + " std " + id + ".s" + str(self._set.numPorts) + "p"

        return self._set.ecal.dataFolderPath.joinpath(fileName)

    @property
    def network(self) -> Network:
        if self._network == None:
            try:
                self._network = self.fetchDataFromTouchstoneFile(self._set.ecal.dataFolderPath)
            except:
                return None
        return self._network
    