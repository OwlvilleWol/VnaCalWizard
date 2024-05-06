from hp8720c import HP8720C
from .calableVna import CalableVna


class CalableHP8720C(HP8720C, CalableVna):

    def __init__(self, address: str, backend='@ivi', reset: bool = False) -> None:
        super().__init__(address, backend, reset)
    


