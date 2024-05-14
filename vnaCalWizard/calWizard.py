from . import CalableVna
from ecalControl import ECalControlSk
from ecalControl import ECalStandardSk
from ecalControl import CorrectionSetScope as scope
import skrf as rf
from skrf.frequency import Frequency 
from typing import List, Callable, Tuple, overload, Literal


class ECalFreqCrossover:
    def __init__(self, crossoverFreq : float | Literal["center", "preferLo", "preferHi"] = "center", preferSingle : Literal[False, "onlyLo", "onlyHi", "hiOverLo", "loOverHi"] = "hiOverLo", softLimits : rf.Frequency = None) -> None:
        self._crossoverFreq = crossoverFreq
        self._preferSingle = preferSingle
        self._softLimits = softLimits

    def _frequencyOverlap(ranges: List[Frequency]) -> None | rf.Frequency:
        
        if len(ranges) == 0: return None
        elif len(ranges) == 1: return ranges[0]
        elif len(ranges) == 2: 
            a = ranges[0]
            b = ranges[1]
            if a == None:
                return None
            if (a.start > b.stop) | (b.start > a.stop):
                return None
            else:
                return Frequency(max(a.start, b.start), min(a.stop, b.stop))
        else:
            c = ECalFreqCrossover._frequencyOverlap(ranges[0:1])
            return ECalFreqCrossover._frequencyOverlap([c] + ranges[2:])
    
    def _splitAtF(f_range : Frequency, f_split: float) -> Tuple[Frequency, Frequency]:
        if f_split < f_range.start:
            return (None, f_range)
        elif f_split > f_range.stop:
            return (f_range, None)
        else:
            for i in range(f_range.npoints):
                if f_split >= f_range.f[i]:
                    return (Frequency.from_f(f_range.f[0:i]), Frequency.from_f(f_range[i:]))


    def splitFrequencyRange(self, measuredFreq : rf.Frequency, ecalLowFreq : rf.Frequency, ecalHiFreq : rf.Frequency) -> tuple[rf.Frequency, rf.Frequency]:
        

        if ecalLowFreq == None & ecalHiFreq == None:
            return (None, None)
        elif ecalLowFreq == None:
            if (measuredFreq.start >= ecalHiFreq.start) & (measuredFreq.stop <= ecalHiFreq.stop):
                return (None, ecalHiFreq)
            else:
                return (None, None)
        elif ecalHiFreq == None:
            if (measuredFreq.start >= ecalLowFreq.start) & (measuredFreq.stop <= ecalLowFreq.stop):
                return (ecalLowFreq ,None)
            else:
                return (None, None)


        softLimits : Frequency
        if self._softLimits != None:
            softLimits = self._softLimits
        else:
            softLimits = Frequency(ecalHiFreq.start, ecalLowFreq.stop)

        crossoverFreq: float
        if isinstance(self._crossoverFreq, float): 
            crossoverFreq = self._crossoverFreq
        elif self._crossoverFreq == "center":
            overlap : Frequency
            if (overlap := ECalFreqCrossover._frequencyOverlap(measuredFreq, ecalLowFreq, ecalHiFreq)) == None:
                crossoverFreq = ecalHiFreq.start
            else:
                crossoverFreq = overlap.center
                crossoverFreq = max(crossoverFreq, softLimits.start)
                crossoverFreq = min(crossoverFreq, softLimits.stop)
        elif self._crossoverFreq == "preferLo":
            crossoverFreq = ecalLowFreq.stop
        elif self._crossoverFreq == "preferHi":
            crossoverFreq = ecalHiFreq.start

        allCovered = True
        allCoveredByLoBelowSoftLimit = True
        allCoveredByHiAboveSoftLimit = True
        allCoveredByLoBelowCrossover = True
        allCoveredByHiAboveCrossover = True
        for f in measuredFreq.f:
            if not ((f >= ecalLowFreq.start & f <= ecalLowFreq.stop) | (f >= ecalHiFreq.start & f <= ecalHiFreq.stop)):
                allCovered = False
            if f > softLimits.stop:
                allCoveredByLoBelowSoftLimit = False
            if f < softLimits.start:
                allCoveredByHiAboveSoftLimit = False
            if f > ecalLowFreq.stop | f > crossoverFreq:
                allCoveredByLoBelowCrossover = False
            if f < ecalHiFreq.start | f < crossoverFreq:
                allCoveredByHiAboveCrossover = False 

        if not allCovered:
            #unable to cover measured frequency range
            return (None, None)

        if self._preferSingle == False:
            #always use both ECals split by crossoverFreq 
            if allCoveredByLoBelowCrossover:
                return (measuredFreq, None)
            elif allCoveredByHiAboveCrossover:
                return (None, measuredFreq)
            else:
                return ECalFreqCrossover._splitAtF(measuredFreq, crossoverFreq)

        else:
            if allCoveredByLoBelowSoftLimit & (not allCoveredByHiAboveSoftLimit):
                if self._preferSingle != "onlyHi":
                    return (measuredFreq, None)
            elif (not allCoveredByLoBelowSoftLimit) & allCoveredByHiAboveSoftLimit:
                if self._preferSingle != "onlyLo":
                    return (None, measuredFreq)
            elif allCoveredByHiAboveSoftLimit & allCoveredByLoBelowSoftLimit:
                if self._preferSingle == "loOverHi" | self._preferSingle == "onlyLo":
                    return (measuredFreq, None) 
                elif self._preferSingle == "hiOverLo" | self._preferSingle == "onlyHi":
                    return (None, measuredFreq)
            else:
                return ECalFreqCrossover._splitAtF(measuredFreq, crossoverFreq)





class VnaCalWizard():

    @overload
    def __init__(self, vna : CalableVna, ecal : ECalControlSk, operatorPrompt : Callable[[str],bool] = None) -> None:
        ...
    
    @overload
    def __init__(self, vna : CalableVna, ecals : Tuple[ECalControlSk, ECalControlSk], operatorPrompt : Callable[[str],bool] = None) -> None:
        ...

    def __init__(self, vna : CalableVna, ecal : ECalControlSk = None, ecals : Tuple[ECalControlSk, ECalControlSk] = None, operatorPrompt : Callable[[str],bool] = None) -> None:
        
        self._vna = vna
        self._ecals = ecal if isinstance(ecal, Tuple) else [ecal, None]

        if operatorPrompt == None:
            self._operatorPrompt = self._simpleConsolePrompt
        else: 
            self._operatorPrompt = operatorPrompt

        


    def _simpleConsolePrompt(message: str) -> bool:
        valid = {"yes": True, "y": True, "Y": True, "no": False, "n": False}
        while (response := input(message)) not in valid:
            print("Please answer [y/n] ")
        return valid[response]


    def _collectDataOnePort(self, port : int, ecal : ECalControlSk, ecalSet : scope) ->  rf.calibration.OnePort:

        self._vna.correction_on = False
        f: Frequency = self._vna.frequency

        measuredStds: List[rf.Network] = []
        idealStds: List[rf.Network] = []

        standard : ECalStandardSk
        for standard in ecal.correctionSets[ecalSet]:
            standard.activate()
            measured = self._vna.get_network([port])
            
            m, s = rf.network.overlap(measured, standard.network)
            
            measuredStds.append(m)
            idealStds.append(s)

        return rf.calibration.OnePort(measuredStds,idealStds)


    def _collectDataTwoPort(self, ports : tuple[int, int], ecal : ECalControlSk, portMappringReverse : bool = False) ->  rf.calibration.TwelveTerm:

        self._vna.correction_on = False
        f: Frequency = self._vna.frequency

        measuredStds: List[rf.Network] = []
        idealStds: List[rf.Network] = []

        onePort1: rf.OnePort = self._collectDataOnePort(1, scope.PORT_A if not portMappringReverse else scope.PORT_B)
        onePort2: rf.OnePort = self._collectDataOnePort(2, scope.PORT_B if not portMappringReverse else scope.PORT_A)
        
        standard : ECalStandardSk
        for standard in ecal.correctionSets[scope.THRU_AB]:
            standard.activate()
            measured = self._vna.get_network([ports[0], ports[1]])
            
            m, s = rf.network.overlap(measured, standard.network)
            
            measuredStds.append(m)
            if portMappringReverse: s.flip()
            idealStds.append(s)

        for opm in zip(onePort1.measured, onePort2.measured):
            measuredStds.append(rf.two_port_reflect(opm[0], opm[1]))

        for ops in zip(onePort1.ideals, onePort2.ideals):
            idealStds.append(rf.two_port_reflect(ops[0], ops[1]))

        return rf.calibration.TwelveTerm(measuredStds,idealStds, n_thrus=1)