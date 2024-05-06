from .calableVna import CalableVna
from ecalControl import ECalControlSk
from ecalControl import ECalStandardSk
from ecalControl import CorrectionSetScope as scope
import skrf as rf
from skrf.frequency import Frequency 
from typing import List


class VnaCalWizard():

    def __init__(self, vna : CalableVna, ecal : ECalControlSk) -> None:
        
        self._vna = vna
        self._ecal = ecal


    def collectDataOnePort(self, port : int, ecalSet : scope) ->  rf.calibration.OnePort:

        self._vna.correction_on = False
        f: Frequency = self._vna.frequency

        measuredStds: List[rf.Network] = []
        idealStds: List[rf.Network] = []

        standard : ECalStandardSk
        for standard in self._ecal.correctionSets[ecalSet]:
            standard.activate()
            measured = self._vna.get_network([port])
            
            m, s = rf.network.overlap(measured, standard.network)
            
            measuredStds.append(m)
            idealStds.append(s)

        return rf.calibration.OnePort(measuredStds,idealStds)
