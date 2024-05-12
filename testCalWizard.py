from vnaCalWizard import VnaCalWizard
from hp8720c import HP8720C
from ecalControl import ECalControlSk, ECalHalFtdi, CorrectionSetScope
from skrf import OnePort

vna = HP8720C("GPIB0::16::INSTR")
ecal = ECalControlSk(ECalHalFtdi(ECalHalFtdi.getValidFT2232PortPairs()[0]))
calWiz = VnaCalWizard(vna, ecal)

cal: OnePort = calWiz._collectDataOnePort(1, CorrectionSetScope.PORT_A)

cal.run()

vna.calibration = cal

pass





