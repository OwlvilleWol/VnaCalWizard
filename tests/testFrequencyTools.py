from skrf import Frequency
from vnaCalWizard import FrequencyEx, ECalFreqCrossover
from typing import List

f1 : FrequencyEx = FrequencyEx.toEx(Frequency(30e3, 9e9, 256))
f2 : FrequencyEx = FrequencyEx.toEx(Frequency(1e9, 26.5e9, 256))
f3 : FrequencyEx = FrequencyEx.toEx(Frequency(50e6, 20e9, 1601))

f4 : FrequencyEx = FrequencyEx.toEx(Frequency(1e9, 2e9, 51))
f5 : FrequencyEx = FrequencyEx.toEx(Frequency(8e9,10e9,201))
f6 : FrequencyEx = FrequencyEx.toEx(Frequency(500e6,600e6,51))
f7 : FrequencyEx = FrequencyEx.toEx(Frequency(10e9,11e9,51))

print(f1 | f2)
print(f1 & f2)
print(f2 & f1)
print(f1 - f2)
print(f2 - f1)
print(f4 & f5)

print("")

print(f3 | f4)
print(f3 & f4)
print(f4 | f3)
print(f4 & f3)

print("")

cross = ECalFreqCrossover(crossoverFreq='preferLo')
fl,fh = cross.splitFrequencyRange(f3,f1,f2)
print(fl)
print(fh)
