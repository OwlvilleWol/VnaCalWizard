from skrf import Network
from typing import overload
from . import Port, ConnectorGender
import re
from pathlib import Path


class RfAdapter:


    ####
    #### File name format: Adapter {type}(M|F| ) to {type}(M|F| ) [Model:{model}] [SerNo:{serialNum}]
    #### E.g. Adapter 35M to 35F Model:SM3310 SerNo:0001.s2p

    @overload
    def __init__(self, port1 : Port, port2 : Port, data: Network, model: str = None, serNo: str = None):
        pass

    @overload
    def __init__(self, filePath: str):
        pass

    def __init__(self, filePath: str = None, port1 : Port = None, port2 : Port = None, data: Network = None, model : str = None,  serNo: str = None) -> None:
        
        if data != None:
            self._data = data
            self._port1 = p1
            self._port2 = p2
            self._sn = sn
            self._model = model

        elif filePath != None:
            try:
                p : Path = Path(filePath)
                m = re.match("Adapter ((?:[^MF\s]|(?:[MF](?!\s)))+)([MF]?) to ((?:[^MF\s]|(?:[MF](?!\s)))+)([MF]?)(?: Model:(\S+))?(?: SN:(\S+))?",p.stem)
                p1 = Port("port1", m[1], ConnectorGender.MALE if m[2] == "M" else ConnectorGender.FEMALE if m[2] == "F" else ConnectorGender.GENDERLESS)
                p2 = Port("port1", m[3], ConnectorGender.MALE if m[4] == "M" else ConnectorGender.FEMALE if m[4] == "F" else ConnectorGender.GENDERLESS)
                model = m[5]
                sn = m[6]

                self._filePath = filePath
                self._port1 = p1
                self._port2 = p2
                self._sn = sn
                self._model = model

                self._network : Network = Network(str(p.resolve()))

            except:
                self._filePath = None
                self._port1 = None
                self._port2 = None
                self._sn = None
                self._model = None
                self._network = None

                return 
            
        else:
            self._filePath = None
            self._port1 = None
            self._port2 = None
            self._sn = None
            self._model = None
            self._network = None

            return 
        
    def saveToFile(self, folder: str) -> None:

        if self._data == None:
            raise Exception("There is no network data to save.")

        if self._port1 == None | self._port2 == None:
            raise Exception("Insufficient port information.")
        
        gender : dict[ConnectorGender, str] = {ConnectorGender.MALE: "M", ConnectorGender.FEMALE: "F", ConnectorGender.GENDERLESS: ""}
        serNo = f" {self._sn}" if self._sn != None else ""
        model = f" {self._model}" if self._model != None else ""

        fileName: str = f"Adapter {self._port1.connectorType}{gender[self._port1.gender]} to {self._port2.connectorType}{gender[self._port2.gender]}{model}{serNo}.s2p"
        path : Path = Path(folder, fileName)

        i : int = 0
        if path.exists():
            backup = path.with_suffix(".bak")
            while backup.exists():
                i += 1
                backup = path.with_suffix(".bak" + str(i))
            path.rename(backup)

        self._network.write_touchstone(filename=str(path.stem), dir=str(path.parent))