from . import ECalHalAbc


class ECalHal(ECalHalAbc):

    def __init__(self) -> None:
        pass 


    def _writeByte(self,addr: int, value: int) -> None:
        pass


    def _readByteFromFlash(self, addr: int) -> int:
        return 0

