from . import CalableVna
from ecalControl import ECalControlSk
from ecalControl import ECalStandardSk
from ecalControl import CorrectionSetScope as scope
from ecalControl import ECalPort, Port
import skrf as rf
from skrf import Network
from skrf.frequency import Frequency 
from typing import List, Callable, Tuple, overload, Literal
import numpy as np
from ecalControl import RfAdapter


class FrequencyEx(Frequency):

    class FrequencyExNonContiguousResultException(Exception): ...
    class FrequencyExEmptyResultException(Exception): ...
    class FrequencyExIncompleteCoverageException(Exception): ...
    class FrequencyExRequestedSubsetExtendsBeyondMeasurementRangeException(Exception): ...

    def __init__(self, start: float = 0, stop: float = 0, npoints: int = 0, unit: str = None, sweep_type: str = 'lin') -> None:
        super().__init__(start, stop, npoints, unit, sweep_type)
            
    def isDisjointFrom(self, other: Frequency) -> bool:
        return (self.start > other.stop) | (self.stop < other.start)

    def isSubsetOf(self, other : Frequency) -> bool:
        return (self.start >= other.start) & (self.stop <= other.stop)

    def isSupersetOf(self, other : Frequency) -> bool:
        return (self.start <= other.start) & (self.stop >= other.stop)

    def copy(self) -> 'FrequencyEx':
        f = FrequencyEx.from_f(self.f)
        f.unit = self.unit
        return f

    def toEx(freq : Frequency) -> 'FrequencyEx':
        if freq == None:
            return FrequencyEx.empty()
        fex = FrequencyEx.from_f(freq.f)
        fex.unit = freq.unit
        return fex


    def copyFromStartTo(self, frequency: float, includeF: bool = True) -> 'FrequencyEx':
        for i in range(self.npoints):
            if includeF & (self.f[i] <= frequency) : continue
            elif (not includeF) & (self.f[i] < frequency) : continue
            else:
                f = FrequencyEx.from_f(self.f[:i])
                f.unit = self.unit
                return f    
            
        return self.copy()


    def copyToEndFrom(self, frequency: float, includeF: bool = True) -> 'FrequencyEx':
        for i in range(self.npoints):
            if includeF & (self.f[i] < frequency): continue
            elif (not includeF) & (self.f[i] <= frequency): continue
            else:
                f = FrequencyEx.from_f(self.f[i:])
                f.unit = self.unit
                return f    
            
        return FrequencyEx.empty()


    def _or(a: 'FrequencyEx', b: 'FrequencyEx') -> 'FrequencyEx':
        if a.isDisjointFrom(b): return a.copy()
        if a.isSupersetOf(b): return a.copy()
        if a.isSubsetOf(b): return b.copy()
        
        if a.stop < b.stop:
            b = b.copyToEndFrom(a.stop)
            f = FrequencyEx.from_f(np.concatenate([a.f,b.f]))
            f.unit = a.unit
            return f
        
        if a.start > b.start:
            b = b.copyFromStartTo(a.start)
            f = FrequencyEx.from_f(b.f + a.f)
            f.unit = a.unit
            return f

    def _sub(a: 'FrequencyEx', b: 'FrequencyEx') -> 'FrequencyEx':
        if a.isDisjointFrom(b): return FrequencyEx.empty()
        if a.isSubsetOf(b): return FrequencyEx.empty()
        if a.isSupersetOf(b): 
            if a.start == b.start:
                return a.copyToEndFrom(b.stop)
            elif a.stop == b.stop:
                return a.copyFromStartTo(b.start)
            else:
                raise FrequencyEx.FrequencyExNonContiguousResultException()
        
        if a.stop < b.stop:
            return a.copyFromStartTo(b.start)
        
        if a.stop > b.stop:
            return a.copyToEndFrom(b.stop)

    def _and(a: 'FrequencyEx', b: 'FrequencyEx') -> 'FrequencyEx':
        if a.isDisjointFrom(b): return FrequencyEx.empty()
        if a.isSubsetOf(b): return a.copy()
        if a.isSupersetOf(b): return b.copy()

        if a.start < b.start:
            return a.copyToEndFrom(b.start)
        if a.stop > b.stop:
            return a.copyFromStartTo(b.stop)


    def split(self, f_split: float, fIsIn: Literal['low', 'high', 'both'] = 'both') -> Tuple['FrequencyEx', 'FrequencyEx']:
        '''Splits a Frequency object at a given frequency and returns the two parts
        In case the split falls exactly on a freqency point fIsIn dectermines which side that point is added to
        '''
        fLo = self.copyFromStartTo(f_split, (fIsIn == 'low') | (fIsIn == 'both'))
        fHi = self.copyToEndFrom(f_split, (fIsIn == 'high') | (fIsIn == 'both'))

        return (fLo,fHi)


    def coercing(self, single_f: float) -> float:
        if self.isEmpty: return 0
        
        if single_f > self.stop: return self.stop
        elif single_f < self.start: return self.start
        else: return single_f

    def empty():
        return FrequencyEx.from_f([])

    def __or__(self, other : Frequency) -> 'FrequencyEx':
        other = FrequencyEx.toEx(other)
        return FrequencyEx._or(self,other)

    def __ror__(self, other : Frequency) -> 'FrequencyEx':
        other = FrequencyEx.toEx(other)
        return FrequencyEx._or(other,self)
    
    def __sub__(self, other : Frequency) -> 'FrequencyEx':
        other = FrequencyEx.toEx(other)
        return FrequencyEx._sub(self,other)

    def __rsub__(self, other : Frequency) -> 'FrequencyEx':
        other = FrequencyEx.toEx(other)
        return FrequencyEx._sub(other,self)

    def __and__(self, other : Frequency | List[Frequency]) -> 'FrequencyEx':
        if isinstance(other, Frequency):
            other = FrequencyEx.toEx(other)
            return FrequencyEx._and(self, other)
        if isinstance(other, List):
            first : FrequencyEx = self.copy()
            for second in other:
                first = first & second
            return first

    def __rand__(self, other : Frequency) -> 'FrequencyEx':
        other = FrequencyEx.toEx(other)
        return FrequencyEx._and(other,self)
    
    def __contains__(self, other : Frequency | float) -> bool:
        if isinstance(other, float):
            other = FrequencyEx.from_f([other])
        else:
            other = FrequencyEx.toEx(other)
        return self.isSupersetOf(other)

    def __add__(self, other: Frequency) -> 'FrequencyEx':
        '''Dumb concatenate of f arrays'''
        return FrequencyEx.from_f(np.concatenate([self.f, other.f]), unit=self.unit)

    def __radd__(self, other: Frequency) -> 'FrequencyEx':
        '''Dumb concatenate of f arrays'''
        return FrequencyEx.from_f(np.concatenate([other.f, self.f]), unit=self.unit) 

    @property
    def isEmpty(self) -> bool:
        return len(self.f) == 0



class VnaCalWizard():


    def __init__(self, 
                 vna : CalableVna,
                 vnaPorts : dict[int, Port],
                 ecals : List[ECalControlSk],
                 adapters : List[RfAdapter] = None, 
                 operatorPrompt : Callable = None) -> None:
        
        self._vna = vna
        self._vnaPorts = vnaPorts
        self._ecals = ecals
        self._adapters = adapters

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
        f: FrequencyEx = FrequencyEx.toEx(self._vna.frequency)
        fSubset = FrequencyEx.toEx(fSubset)
        if not fSubset.isEmpty:
            if not f.isSupersetOf(fSubset):
                raise FrequencyEx.FrequencyExRequestedSubsetExtendsBeyondMeasurementRangeException() 
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
        f: FrequencyEx = FrequencyEx.toEx(self._vna.frequency)
        fSubset = FrequencyEx.toEx(fSubset)
        if not fSubset.isEmpty:
            if not f.isSupersetOf(fSubset):
                raise FrequencyEx.FrequencyExRequestedSubsetExtendsBeyondMeasurementRangeException() 
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
    

    def concatCals(calLo : rf.Calibration, calHi : rf.Calibration) -> rf.Calibration:
        '''Concatenate two skrf Calibration objects over frequency.
        This is used to merge the partial cal results from two ECal modules.'''

        if not (type(calLo) is type(calHi)):
            raise Exception("Provided calibration types don't match.")
        
        newCoefs : dict[str, np.ndarray] = {}
        for coef in calLo.coefs:
            arrLo : np.ndarray = calLo.coefs[coef]
            arrHi : np.ndarray = calHi.coefs[coef]
            newCoefs[coef] = np.concatenate([arrLo, arrHi])

        newF : FrequencyEx = FrequencyEx.toEx(calLo.frequency) + calHi.frequency

        calType = type(calLo)
        return calType.from_coefs(newF, newCoefs)


    def splitFreqBetweenECals(measuredFreq : Frequency, 
                            ecalLowFreq : Frequency, 
                            ecalHiFreq : Frequency,
                            allowIncomplete : bool = False,
                            crossoverFreq : float | Literal["center", "preferLo", "preferHi"] = "center", 
                            preferSingle : Literal[False, "onlyLo", "onlyHi", "hiOverLo", "loOverHi"] = "hiOverLo", 
                            softLimits : rf.Frequency = None
                            ) -> tuple[FrequencyEx, FrequencyEx]:
            '''Splits the measured frequency range based on the ranges of the low and high ecal modules and the provided rules.'''

            measuredFreq : FrequencyEx = FrequencyEx.toEx(measuredFreq)
            ecalLowFreq : FrequencyEx = FrequencyEx.toEx(ecalLowFreq)
            ecalHiFreq : FrequencyEx = FrequencyEx.toEx(ecalHiFreq)

        
            if ecalLowFreq.isEmpty:
                if measuredFreq.isSubsetOf(ecalHiFreq):
                    return (FrequencyEx.empty(), measuredFreq)
                else:
                    if allowIncomplete:
                        return (FrequencyEx.empty(), measuredFreq & ecalHiFreq)
                    else:
                        raise FrequencyEx.FrequencyExIncompleteCoverageException()

            if ecalHiFreq.isEmpty:
                if measuredFreq.isSubsetOf(ecalLowFreq):
                    return (measuredFreq, FrequencyEx.empty())
                else:
                    if allowIncomplete:
                        return (measuredFreq & ecalLowFreq, FrequencyEx.empty())
                    else:
                        raise FrequencyEx.FrequencyExIncompleteCoverageException()

            if not measuredFreq.isSubsetOf(ecalLowFreq | ecalHiFreq):
                if ecalLowFreq.isDisjointFrom(ecalHiFreq):
                    raise FrequencyEx.FrequencyExNonContiguousResultException()
                if not allowIncomplete:
                    raise FrequencyEx.FrequencyExIncompleteCoverageException() 

            softLimits = FrequencyEx.toEx(softLimits)
            if softLimits.isEmpty:
                softLimits = FrequencyEx.from_f([ecalHiFreq.start, ecalLowFreq.stop])


            if isinstance(crossoverFreq, float): 
                pass
            elif crossoverFreq == "center":
                overlap : FrequencyEx = measuredFreq & [ecalLowFreq, ecalHiFreq]
                if overlap.isEmpty:
                    crossoverFreq = ecalHiFreq.start
                else:
                    crossoverFreq = softLimits.coercing(overlap.center)
            elif crossoverFreq == "preferLo":
                crossoverFreq = ecalLowFreq.stop
            elif crossoverFreq == "preferHi":
                crossoverFreq = ecalHiFreq.start

            allSingleFCovered = True
            allSingleFCoveredByLoBelowSoftLimit = True
            allSingleFCoveredByHiAboveSoftLimit = True
            allSingleFCoveredByLoBelowCrossover = True
            allSingleFCoveredByHiAboveCrossover = True
            for f in measuredFreq.f:
                if not ((f in ecalLowFreq) | (f in ecalHiFreq)):
                    allSingleFCovered = False
                if f > softLimits.stop:
                    allSingleFCoveredByLoBelowSoftLimit = False
                if f < softLimits.start:
                    allSingleFCoveredByHiAboveSoftLimit = False
                if (f > ecalLowFreq.stop) | (f > crossoverFreq):
                    allSingleFCoveredByLoBelowCrossover = False
                if (f < ecalHiFreq.start) | (f < crossoverFreq):
                    allSingleFCoveredByHiAboveCrossover = False 

            if not allSingleFCovered:
                #unable to cover measured frequency range
                if not allowIncomplete:
                    raise FrequencyEx.FrequencyExIncompleteCoverageException()

            if preferSingle == False:
                #always use both ECals split by crossoverFreq 
                if allSingleFCoveredByLoBelowCrossover:
                    return (measuredFreq, FrequencyEx.empty())
                elif allSingleFCoveredByHiAboveCrossover:
                    return (FrequencyEx.empty(), measuredFreq)
                else:
                    return measuredFreq.split(crossoverFreq, 'low')

            else:
                if allSingleFCoveredByLoBelowSoftLimit & (not allSingleFCoveredByHiAboveSoftLimit):
                    if preferSingle != "onlyHi":
                        return (measuredFreq, FrequencyEx.empty())
                elif (not allSingleFCoveredByLoBelowSoftLimit) & allSingleFCoveredByHiAboveSoftLimit:
                    if preferSingle != "onlyLo":
                        return (FrequencyEx.empty(), measuredFreq)
                elif allSingleFCoveredByHiAboveSoftLimit & allSingleFCoveredByLoBelowSoftLimit:
                    if preferSingle == "loOverHi" | preferSingle == "onlyLo":
                        return (measuredFreq, FrequencyEx.empty()) 
                    elif preferSingle == "hiOverLo" | preferSingle == "onlyHi":
                        return (FrequencyEx.empty(), measuredFreq)
                else:
                    return measuredFreq.split(crossoverFreq, 'low')
                

    def _calibrateOnePortSingleECal(self, 
                                   vnaPort: int, 
                                   ecal: ECalControlSk, 
                                   freqSubset: FrequencyEx, 
                                   adapter: RfAdapter = None) -> rf.OnePort:
        
        operatorMessage = f"Connect VNA port {vnaPort} to {ecal.model} Ecal module."
        operatorOptions = [("Done","d",["D","Done","done"]), None, ("Abort","a",["A","Abort","abort"])]

        operatorResponse : str = self._operatorPrompt(operatorMessage,operatorOptions)
        if operatorResponse == "d": pass
        elif operatorResponse == "a": return
        else: raise Exception("Unexpected operator response.")

        ecalPortMap : dict[int, ECalPort] = {}
        ecalPortMap[vnaPort] = self._orientOnePort(vnaPort, ecal)

        cal = self._collectDataOnePort(vnaPort = vnaPort, 
                                        ecal = ecal, 
                                        vnaToEcalPortMap = ecalPortMap,
                                        isCorrected = False, 
                                        adapter = adapter.network, 
                                        fSubset = freqSubset)
        
        cal.run()

        return cal



    def calibrateOnePort(self, vnaPort: int) -> None:



        calibrationFreq : FrequencyEx = FrequencyEx.toEx(self._vna.frequency)

        ecalFreq : tuple[FrequencyEx, FrequencyEx] = [FrequencyEx.empty(), FrequencyEx.empty()]

        try: ecalFreq[0] = FrequencyEx.toEx(self._ecals[0].frequency) 
        except: pass

        try: ecalFreq[1] = FrequencyEx.toEx(self._ecals[1].frequency) 
        except: pass

        calLo : rf.OnePort = None
        calHi : rf.OnePort = None
        calFreqLo : FrequencyEx
        calFreqHi : FrequencyEx
        calFreqLo, calFreqHi = VnaCalWizard.splitFreqBetweenECals(measuredFreq = calibrationFreq,
                                                                  ecalLoFreq = ecalFreq[0], 
                                                                  ecalHiFreq = ecalFreq[1],
                                                                  allowIncomplete = False, 
                                                                  crossoverFreq = 'center',
                                                                  preferSingle = 'hiOverLo',
                                                                  softLimits = None)
        
        if not calFreqLo.isEmpty():
            calLo = self._calibrateOnePortSingleECal(vnaPort, self._ecals[0],calFreqLo, None)

        if not calFreqHi.isEmpty():
            calHi = self._calibrateOnePortSingleECal(vnaPort, self._ecals[1],calFreqHi, None)

        if (calLo != None) & (calHi != None):
            self._vna.calibration = VnaCalWizard.concatCals(calLo, calHi)
        elif calLo != None:
            self._vna.calibration = calLo
        elif calHi != None:
            self._vna.calibration = calHi
        else:
            pass

