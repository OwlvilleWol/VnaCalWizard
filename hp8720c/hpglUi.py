from abc import ABC, abstractmethod


class HpglUi(ABC):

    @abstractmethod
    def _hpglWrite(self, command : str) -> None:
        pass

    @abstractmethod
    def _hpglCls(self) -> None:
        pass

    @abstractmethod
    def _hpglInstrumentScreenOn(self, on : bool = True) -> None:
        pass

    @abstractmethod
    def _hpglPrintLabel(self, text : str, x: int, y: int, pen : int = 1, textSize : int = 16, alignRight : bool = False):
        pass

    @abstractmethod
    def _hpglDrawLine(self, x1,y1,x2,y2 : int, pen : int = 1):
        pass

    @abstractmethod
    def _waitForKeypress(self)-> int | None:
        pass

