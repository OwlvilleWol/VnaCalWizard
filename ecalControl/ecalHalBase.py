
class ECalHal:

    _MUX_ADDR_FLASH_ADDR_0_7 = 2
    _MUX_ADDR_FLASH_ADDR_8_15 = 3
    _MUX_ADDR_FLASH_ADDR_16_17 = 4

    _MUX_ADDR_GATES_1_8 = 0
    _MUX_ADDR_GATES_9_16 = 1

    _MUX_ADDR_FLASH_DATA = 7


    def __init__(self) -> None:
        pass 


    def _writeByte(self,addr: int, value: int) -> None:
        pass


    def _readByteFromFlash(self, addr: int) -> int:
        return 0

