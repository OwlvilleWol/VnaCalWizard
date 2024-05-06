from vnaCalWizard import VnaCalWizard
from vnaCalWizard.calableHP8720C import CalableHP8720C
from ecalControl import ECalControlSk, ECalHalFtdi, CorrectionSetScope


vna = CalableHP8720C("GPIB0::16::INSTR")
ecal = ECalControlSk(ECalHalFtdi(ECalHalFtdi.getValidFT2232PortPairs()[0]))
calWiz = VnaCalWizard(vna, ecal)

cal = calWiz.collectDataOnePort(1, CorrectionSetScope.PORT_A)

cal.run()

vna.calibration = cal

pass





