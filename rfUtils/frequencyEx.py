from skrf import Frequency
import numpy as np
from typing import Literal, List, Tuple


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