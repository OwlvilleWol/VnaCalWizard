from ecalControl import ECalHalFtdi
from ecalControl import ECalHalCamino
from ecalControl import ECalControlSk
from ecalControl import ECalStandardSk
from ecalControl import CorrectionSetScope as scope



try:
    #Create ECal HAL object
    #hal = ECalHalFtdi(ECalHalFtdi.getValidFT2232PortPairs()[0])
    hal = ECalHalCamino("COM5")

    ecal = ECalControlSk(hal)


    #fetch and save characterization data 
    #can take a long time using FTDI based HAL
    std : ECalStandardSk
    csk : scope
    for csk in ecal.correctionSets:
        cs = ecal.correctionSets[csk]
        print(cs.scope.name)
        for std in cs:
            print("   " + str(std._touchstoneFilePath))
            std.fetchDataFromEEPROM()
            std.saveDataToTouchstoneFile()
    

    print("All done")


except Exception as e:
    print(e)
    





