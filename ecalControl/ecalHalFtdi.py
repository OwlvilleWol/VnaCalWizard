from ftd2xx.ftd2xx import DeviceInfoDetail
from ftd2xx import * 
import time
from typing import List

from .ecalHalBase import ECalHal

class ECalHalFtdi(ECalHal):

    def __init__(self, portInfoPair : tuple[DeviceInfoDetail, DeviceInfoDetail]):

        try:
            controlPort: FTD2XX = openEx(portInfoPair[1]["serial"])
            controlPort.setBaudRate(3000000)

            try:
                dataPort = openEx(portInfoPair[0]["serial"])
                dataPort.setBaudRate(3000000)
            except Exception as e:
                controlPort.close()
                raise e
            
        except Exception as e:
            self._cPort = None
            self._dPort = None
            raise e
            
        self._cPort: FTD2XX = controlPort
        self._dPort: FTD2XX = dataPort

        self._ADDR = 0
        self._ENn = 1
        self._OEn = 1
        self._WEn = 1
        self._RESETn = 1
        self._Detect = 0

        self._DataByte = 0
        self._DPortIsWrite = False
        self._dPort.setBitMode(0,4) #set data port to read
        self._cPort.setBitMode(0b11111110,4) #set control port to write
        self._writeFtdiControlPort()
        self._writeFtdiControlPort(RESETn=0)
        time.sleep(0.01)
        self._writeFtdiControlPort(RESETn=1)
        time.sleep(0.016)


    def __del__(self):
        if self._cPort != None: self._cPort.close()
        if self._dPort != None: self._dPort.close()


    def _writeFtdiControlPort(self, ADDR = None, ENn = None, OEn = None, WEn = None, RESETn = None, Detect = None):
        dataByte = 0

        if (ADDR != None): self._ADDR = ADDR
        if (ENn != None): self._ENn = ENn
        if (OEn != None): self._OEn = OEn
        if (WEn != None): self._WEn = WEn
        if (RESETn != None): self._RESETn = RESETn
        if (Detect != None): self._Detect = Detect

        bitList = [(self._ADDR & 0b1), (self._ADDR & 0b10) >> 1, (self._ADDR & 0b100) >> 2, self._ENn, self._OEn, self._WEn, self._RESETn, self._Detect]
        for bit in bitList:
            dataByte = (dataByte << 1) | bit

        self._cPort.write(bytes([dataByte]))

    def _writeFtdiDataPort(self, dataByte):
        self._DataByte = dataByte
        if self._DPortIsWrite == False: 
            self._DPortIsWrite = True
            self._dPort.setBitMode(0b11111111,4)
        self._dPort.write(bytes([self._DataByte]))

    def _readFtdiDataPort(self) -> int:
        if self._DPortIsWrite == True: 
            self._DPortIsWrite = False
            self._dPort.setBitMode(0b00000000,4)

        while True:
            rxq,txq,evt = self._dPort.getStatus()
            if txq == 0: break
        self._dPort.write(bytes([0]))
        rxq,txq,evt = self._dPort.getStatus()
        self._DataByte = self._dPort.read(rxq+1)
        return int(self._DataByte[-1])

    def _setDataPortToIn(self):
        if self._DPortIsWrite: 
            self._DPortIsWrite = False
            self._dPort.setBitMode(0b00000000,4)

    def _latch(self): 
        self._writeFtdiControlPort(ENn = 0)
        self._writeFtdiControlPort(ENn = 1)

    def _reset(self):
        self._writeFtdiControlPort(RESETn = 0)
        self._writeFtdiControlPort(RESETn = 1)


    def _writeByte(self,addr: int, value: int) -> None:
        self._writeFtdiDataPort(value & 0x00ff)
        self._writeFtdiControlPort(addr)
        self._latch()


    def _readByteFromFlash(self, addr) -> int:
        
        addr0_7 = (addr & 0x000000FF) >> 0
        addr8_15 = (addr & 0x0000FF00) >> 8
        addr16_17 = (addr & 0x00030000) >> 16

        self._writeFtdiDataPort(addr0_7)
        self._writeFtdiControlPort(ADDR = ECalHalFtdi._MUX_ADDR_FLASH_ADDR_0_7)
        self._latch()

        self._writeFtdiDataPort(addr8_15)
        self._writeFtdiControlPort(ADDR = ECalHalFtdi._MUX_ADDR_FLASH_ADDR_8_15)
        self._latch()

        self._writeFtdiDataPort(addr16_17)
        self._writeFtdiControlPort(ADDR = ECalHalFtdi._MUX_ADDR_FLASH_ADDR_16_17)
        self._latch()

        self._dPort.setBitMode(0,4) #set data pins to read
        self._DPortIsWrite = False
        time.sleep(0.016)

        self._writeFtdiControlPort(ADDR= ECalHalFtdi._MUX_ADDR_FLASH_DATA)
        self._writeFtdiControlPort(ENn = 0)
        self._writeFtdiControlPort(OEn = 0)

        readByte = self._readFtdiDataPort()

        self._writeFtdiControlPort(OEn= 1)
        self._writeFtdiControlPort(ENn= 1)

        return readByte


    def getValidFT2232PortPairs() -> List[tuple[DeviceInfoDetail, DeviceInfoDetail]]:
        try:
            n = createDeviceInfoList()
            infoDetails = []
            for i in range(n):
                infoDetails.append(getDeviceInfoDetail(i))

            valid_port_pairs = []
            port_A : DeviceInfoDetail
            for port_A in infoDetails:
                ser_A = port_A["serial"].decode()
                if not ser_A.endswith("A"):
                    continue
                
                port_B : DeviceInfoDetail
                for port_B in infoDetails:
                    ser_B = port_B["serial"].decode()
                    if not ser_B.endswith("B"):
                        continue
                    if ser_B[:-1] == ser_A[:-1] and port_B["location"] == port_A["location"] + 1:
                        valid_port_pairs.append((port_A, port_B))

            return valid_port_pairs

        except Exception as e: 
            return []