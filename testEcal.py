from ecalControl import ECalHalFtdi
from ecalControl import ECalHalCamino
from ecalControl import ECalControlSk
from ecalControl import ECalStandardSk
from ecalControl import CorrectionSetScope as scope

import time


try:
    #hal = ECalHalFtdi(ECalHalFtdi.getValidFT2232PortPairs()[0])
    hal = ECalHalCamino("COM5")

    ecal = ECalControlSk(hal)


    #std = ecal.correctionSets[scope.PORT_A][0x8003]
    #std.fetchDataFromEEPROM()

    t0 = time.time()
    std : ECalStandardSk

    
    csk : scope
    for csk in ecal.correctionSets:
        cs = ecal.correctionSets[csk]
        print(cs.scope.name)
        for std in cs:
            print("   " + str(std._touchstoneFilePath))
            print("Elapsed time: " + str(time.time() - t0))
            std.fetchDataFromEEPROM()
            std.saveDataToTouchstoneFile()
    
    
    
    #std = ecal.correctionSets[scope.VERIFY_AB][0x0200]
    #std.fetchDataFromEEPROM()
    #std.saveDataToTouchstoneFile()
    

    #next(iter(ecal.correctionSets[scope.PORT_A])).activate()

    #ecal.isolate()

    print("All done: Elapsed time: " + str(time.time() - t0))



except Exception as e:
    print(e)
    





