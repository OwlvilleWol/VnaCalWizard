from abc import ABC, abstractmethod
import numpy as np
import skrf as rf
from typing import Callable


class CalableVna(ABC):

    @abstractmethod
    def get_network(self, ports: rf.Sequence = {1,2}) -> rf.Network:
        pass

    @property
    @abstractmethod
    def frequency(self) -> rf.Frequency:
        pass

    @property
    @abstractmethod
    def calibration(self) -> rf.Calibration:
        pass

    @calibration.setter
    @abstractmethod
    def calibration(self, cal: rf.Calibration) -> None:
        pass

    @property
    @abstractmethod
    def correction_on(self) -> bool:
        pass

    @correction_on.setter
    @abstractmethod
    def correction_on(self, arg: bool):
        pass

    @property
    @abstractmethod
    def operatorPrompt(self) -> None | Callable[[str, dict[str, str]],str]:
        pass
