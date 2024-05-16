from . import CalableVna
from ecalControl import ECalControlSk
from ecalControl import ECalStandardSk
from ecalControl import CorrectionSetScope as scope
from ecalControl import ECalPort
import skrf as rf
from skrf import Network
from skrf.frequency import Frequency 
from typing import List, Callable, Tuple, overload, Literal
import numpy as np
from ecalControl import RfAdapter


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
    def __init__(self, vna : CalableVna, ecal : ECalControlSk, operatorPrompt : Callable = None) -> None:
        ...
    
    @overload
    def __init__(self, vna : CalableVna, ecals : List[ECalControlSk], operatorPrompt : Callable = None) -> None:
        ...

    def __init__(self, vna : CalableVna, ecal : ECalControlSk = None, ecals : List[ECalControlSk] = None, operatorPrompt : Callable = None) -> None:
        
        self._vna = vna
        self._ecals = ecals if ecals != None else [ecal]

        if operatorPrompt == None:
            if self._vna.operatorPrompt == None:
                self._operatorPrompt = self._simpleConsolePrompt
            else:
                self._operatorPrompt = self._vna.operatorPrompt
        else: 
            self._operatorPrompt = operatorPrompt


    def _simpleConsolePrompt(prompt : str, options : List[tuple[str, str, List[str] | None] | None]) -> str:
        
        displayOptions = [f"[{option[1]}]{option[0]}" for option in options if option != None]
        prompt = prompt + " " + "/".join(displayOptions)

        while True:
            response = input(prompt)
            for option in options:
                if option == None:
                    continue
                elif response == option[1]:
                    return option[1]
                elif (option[2] != None) & (response in option[2]):
                    return option[1]
     


    def _collectDataOnePort(self, 
                            vnaPort : int, 
                            ecal : ECalControlSk, 
                            vnaToEcalPortMap : dict[int, ECalPort] = {1: ECalPort.A, 2: ECalPort.B}, 
                            isCorrected : bool = False,
                            adapter : Network = None,
                            fSubset : Frequency = None
                            ) ->  rf.calibration.OnePort:
        '''Collects data needed for a one port calibration with a single ECal module.'''

        #turn off error correction for normal calibration cases
        self._vna.correction_on = isCorrected
        
        #check if frequency subset argument is wihtin the vna frequency span
        f: Frequency = self._vna.frequency
        if fSubset != None:
            if fSubset.start < f.start | fSubset.stop > f.stop:
                raise Exception("Requested frequency subset is outside of currently set measurement range.") 
            else:
                f = fSubset

        measuredStds: List[Network] = []
        idealStds: List[Network] = []

        #measure all one port standards on the connected ECal port
        standard : ECalStandardSk
        for standard in ecal.correctionSets[vnaToEcalPortMap[vnaPort].value]:
            standard.activate()
            #get one port reading from vna, cropped to frequency subset (if given)
            measured = self._vna.get_network([vnaPort]).cropped(f.start, f.stop)
            
            #get s-parameter data subset within frequency overlap between standard characterization data and measured (and cropped) data
            m, s = rf.network.overlap(measured, standard.network)
            
            #if an adapter is connected between the ECal and the VNA port (end of the VNA test port cable)
            #connect the adapter network in between. 
            #Port 1 of the adapter network is facing the VNA
            #Port 2 of the adapter network is facing the ECal  
            if adapter != None:
                s = rf.network.cascade(adapter, s)

            measuredStds.append(m)
            idealStds.append(s)

        return rf.calibration.OnePort(measuredStds,idealStds)


    def _collectDataTwoPort(self, 
                            vnaPorts : tuple[int, int], 
                            ecal : ECalControlSk, 
                            vnaToEcalPortMap : dict[int, scope] = {1: ECalPort.A, 2: ECalPort.B}, 
                            isCorrected: bool = False,
                            adapterOnECalPort: dict[ECalPort, Network] = {},
                            fSubset : Frequency = None
                            ) ->  rf.calibration.TwelveTerm:
        '''Collects data needed for a full two port calibration with a single ECal module.'''

        #turn off error correction for normal calibration cases
        self._vna.correction_on = isCorrected

        #check if frequency subset argument is wihtin the vna frequency span
        f: Frequency = self._vna.frequency
        if fSubset != None:
            if fSubset.start < f.start | fSubset.stop > f.stop:
                raise Exception("Requested frequency subset is outside of currently set measurement range.") 
            else:
                f = fSubset

        measuredStds: List[Network] = []
        idealStds: List[Network] = []

        #measure one port standards
        onePort1: rf.OnePort = self._collectDataOnePort(1, ecal, vnaToEcalPortMap, isCorrected, adapterOnECalPort.get(vnaToEcalPortMap[1]), f)
        onePort2: rf.OnePort = self._collectDataOnePort(2, ecal, vnaToEcalPortMap, isCorrected, adapterOnECalPort.get(vnaToEcalPortMap[2]), f)
        
        #measured thru standards
        standard : ECalStandardSk
        for standard in ecal.correctionSets[scope.THRU_AB]:
            standard.activate()
            #get two port reading from vna, cropped to frequency subset (if given)
            measured = self._vna.get_network([vnaPorts[0], vnaPorts[1]]).cropped(f)
            
            #get s-parameter data subset within frequency overlap between standard characterization data and measured (and cropped) data
            m, s = rf.network.overlap(measured, standard.network)
            
            measuredStds.append(m)

            #cascade adapters if present
            #adapter's port 1 is always facing the VNA
            #adapter's port 2 is always facing the ECal
            if vnaToEcalPortMap[1] == ECalPort.A: 
                if ECalPort.A in adapterOnECalPort:
                    s = rf.network.cascade(adapterOnECalPort[ECalPort.A], s)
                if ECalPort.B in adapterOnECalPort:
                    s = rf.network.cascade(s, adapterOnECalPort[ECalPort.B].flipped())
            else:
                s.flip()
                if ECalPort.B in adapterOnECalPort:
                    s = rf.network.cascade(adapterOnECalPort[ECalPort.B], s)
                if ECalPort.A in adapterOnECalPort:
                    s = rf.network.cascade(s, adapterOnECalPort[ECalPort.A].flipped())
            
            idealStds.append(s)

        #pair one port measurements into fake two port networks (needed for skrf cal routine)
        for opm in zip(onePort1.measured, onePort2.measured):
            measuredStds.append(rf.two_port_reflect(opm[0], opm[1]))

        #pair one port standard characterization data into fake two port networks (needed for skrf cal routine)
        for ops in zip(onePort1.ideals, onePort2.ideals):
            idealStds.append(rf.two_port_reflect(ops[0], ops[1]))

        return rf.calibration.TwelveTerm(measuredStds,idealStds, n_thrus=1)
    

    def _orientOnePort(self, port : int, ecal : ECalControlSk, frequency : float = None) -> ECalPort:
        '''Returns the ECal port more likely to be connected to the given vna port.'''

        #save vna frequency settings
        fBackup: Frequency = self._vna.frequency

        #select orientation frequency as input argument if present or the vna center frequency
        fOrient = Frequency().from_f([fBackup.center]) if frequency == None else Frequency().from_f([frequency])
        self._vna.frequency = fOrient

        #measure all 1 port standards in the ecal Port A at the orientation frequency
        std : ECalStandardSk
        readingsA : List[complex] = []
        for std in ecal.correctionSets[scope.PORT_A]:
            std.activate()
            readingsA.append(self._vna.get_network([port]).s[0,0,0])
        #calculate variance of the list of 1 port complex measurement results
        varianceA = np.var(readingsA)

        #measure all 1 port standards in the ecal Port B at the orientation frequency
        readingsB : List[complex] = []
        for std in ecal.correctionSets[scope.PORT_B]:
            std.activate()
            readingsB.append(self._vna.get_network([port]).s[0,0,0])
        #calculate variance of the list of 1 port complex measurement results
        varianceB = np.var(readingsB)

        #restore vna frequency settings
        self._vna.frequency = fBackup

        #deceide which measurement list had higher vairability vs cal standard change
        return ECalPort.A if varianceA > varianceB else ECalPort.B
    
