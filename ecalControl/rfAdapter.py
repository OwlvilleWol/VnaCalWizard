from skrf import Network, Frequency, overlap
from typing import overload, List, Tuple
from . import RfPort, ConnectorGender
import re
from pathlib import Path
import numpy as np
import dataclasses


class UnmateableRfConnectionException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

        self._port1 : RfPort = None
        self._port2 : RfPort = None

        if len(args) >= 2:
            if isinstance(args[0], RfPort) & isinstance(args[1], RfPort):
                self._port1 = args[0]
                self._port2 = args[1]

    def __str__(self) -> str:
        msg : str = ""
        if self._port1 != None:
            return f"{self._port1} cannot be mated to {self._port2}."
        else:
            return super().__str__()



class RfAdapter:


    ####
    #### File name format: Adapter {type}(M|F| ) to {type}(M|F| ) [Model:{model}] [SerNo:{serialNum}]
    #### E.g. Adapter 35M to 35F Model:SM3310 SerNo:0001.s2p

    @overload
    def __init__(self, port1 : RfPort, port2 : RfPort, data: Network, model: str = None, serNo: str = None):
        pass

    @overload
    def __init__(self, filePath: str):
        pass

    def __init__(self, filePath: str = None, port1 : RfPort = None, port2 : RfPort = None, data: Network = None, model : str = None,  serNo: str = None) -> None:
        
        if data != None:
            self._data = data
            self._leftPort = port1.instanceOn(self)
            self._rightPort = port2.instanceOn(self)
            self._sn = sn
            self._model = model

        elif filePath != None:
            try:
                p : Path = Path(filePath)
                m = re.match("Adapter ((?:[^MF\s]|(?:[MF](?!\s)))+)([MF]?) to ((?:[^MF\s]|(?:[MF](?!\s)))+)([MF]?)(?: Model:(\S+))?(?: SN:(\S+))?",p.stem)
                p1 = RfPort("port1", m[1], ConnectorGender.MALE if m[2] == "M" else ConnectorGender.FEMALE if m[2] == "F" else ConnectorGender.GENDERLESS, device=self)
                p2 = RfPort("port1", m[3], ConnectorGender.MALE if m[4] == "M" else ConnectorGender.FEMALE if m[4] == "F" else ConnectorGender.GENDERLESS, device=self)
                model = m[5]
                sn = m[6]

                self._filePath = filePath
                self._leftPort = p1
                self._rightPort = p2
                self._sn = sn
                self._model = model

                self._network : Network = Network(str(p.resolve()))

            except Exception as e:
                self._filePath = None
                self._leftPort = None
                self._rightPort = None
                self._sn = None
                self._model = None
                self._network = None

                raise e
 
            self._isFlipped : bool = False
            self._auto : bool = False
            
        else:
            self._filePath = None
            self._leftPort = None
            self._rightPort = None
            self._sn = None
            self._model = None
            self._network = None

            return 
        
    def __copy__(self) -> 'RfAdapter':
        return RfAdapter(self._leftPort, self._rightPort, self._network.copy(), self._model, self._sn)


    @property
    def network(self) -> Network:
        if self._network != None: 
            if self._isFlipped:
                return self._network.flipped()
            else:
                return self._network
        else:
            raise Exception("No network data loaded for RF Adapter.")

    @property
    def frequency(self) -> Frequency:
        if self._network != None: return self._network.frequency
        else:
            raise Exception("No network data loaded for RF Adapter.")

    @property
    def leftPort(self) -> RfPort:
        if self._isFlipped:
            return self._rightPort
        else:
            return self._leftPort

    @property
    def rightPort(self) -> RfPort:
        if self._isFlipped:
            return self._leftPort
        else:
            return self._rightPort

    @property
    def auto(self) -> "RfAdapter":
        copy = self.__copy__()
        copy.auto = True
        return copy
    
    @property
    def flipped(self) -> "RfAdapter":
        copy = self.__copy__()
        copy.auto = False
        copy._isFlipped = not self._isFlipped
        return copy
    
    @property
    def reversed(self) -> "RfAdapter":
        copy = self.__copy__()
        copy.auto = False
        copy._isFlipped = True
        return copy
    
    @property
    def forward(self) -> "RfAdapter":
        copy = self.__copy__()
        copy.auto = False
        copy._isFlipped = False
        return copy


    def cascadeAdapters(left: 'RfAdapter', right: 'RfAdapter', ignoreMate : bool = False) -> 'RfAdapter':

        if not ignoreMate:
            if not (left.rightPort & right.leftPort):
                raise UnmateableRfConnectionException(left.rightPort, right.leftPort)

        networks : Tuple[Network] = overlap(left.network, right.network)
        combinedNwk : Network = networks[0] ** networks[1]

        return RfAdapter(left.leftPort, 
                        right.rightPort, 
                        combinedNwk, 
                        model=f"{left._model}{"rev" if left._isFlipped else ""}+{right._model}{"rev" if right._isFlipped else ""}", 
                        serNo="+".join([left._sn, right._sn]))


    def cascadePort(adapter: 'RfAdapter', port: RfPort, ignoreMate : bool = False) -> 'RfAdapter':
        
        if not ignoreMate:
            if not (adapter.rightPort & port):
                raise UnmateableRfConnectionException(adapter.rightPort, port)        
        
        return adapter.leftPort 


    def __pow__(self, other: 'RfAdapter' | RfPort) -> 'RfAdapter' | RfPort:

        if isinstance(other, RfAdapter):
            try:
                return RfAdapter.cascadeAdapters(self, other)
            except UnmateableRfConnectionException as e:
                if self.auto:
                    return RfAdapter.cascadeAdapters(self.flipped, other)
                else: raise e
        elif isinstance(other, RfPort):       
            try:  
                return RfAdapter.cascadePort(self, other)
            except UnmateableRfConnectionException as e:
                if self.auto:
                    return RfAdapter.cascadePort(self.flipped, other)
                else: raise e
        else:
            return NotImplemented


    def __rpow__(self, other: 'RfAdapter' | RfPort) -> 'RfAdapter' | RfPort:

        if isinstance(other, RfAdapter):
            try:
                return RfAdapter.cascadeAdapters(other, self)
            except UnmateableRfConnectionException as e:
                if self.auto:
                    return RfAdapter.cascadeAdapters(other, self.flipped)
                else: raise e
        elif isinstance(other, RfPort):       
            try:  
                return RfAdapter.cascadePort(self.flipped, other)
            except UnmateableRfConnectionException as e:
                if self.auto:
                    return RfAdapter.cascadePort(self, other)
                else: raise e
        else:
            return NotImplemented


    def __and__(self, other: 'RfAdapter' | RfPort) -> bool:

        if isinstance(other, RfAdapter):
            if self.rightPort & other.leftPort: return True
            elif self.auto & (self.leftPort & other.leftPort): return True
            else: return False
        elif isinstance(other, RfPort):
            if self.rightPort & other: return True
            elif self.auto & (self.rightPort & other): return True
            else: return False
        else:
            return NotImplemented
        

    def __rand__(self, other: 'RfAdapter' | RfPort) -> bool:

        if isinstance(other, RfAdapter):
            if other.rightPort & self.leftPort: return True
            elif self.auto & (other.rightPort & self.rightPort): return True
            else: return False
        elif isinstance(other, RfPort):
            if other & self.leftPort: return True
            elif self.auto & (other & self.rightPort): return True
            else: return False
        else:
            return NotImplemented



    def saveToFile(self, folder: str) -> None:

        if self._data == None:
            raise Exception("There is no network data to save.")

        if self._leftPort == None | self._rightPort == None:
            raise Exception("Insufficient port information.")
        
        gender : dict[ConnectorGender, str] = {ConnectorGender.MALE: "M", ConnectorGender.FEMALE: "F", ConnectorGender.GENDERLESS: ""}
        serNo = f" {self._sn}" if self._sn != None else ""
        model = f" {self._model}" if self._model != None else ""

        fileName: str = f"Adapter {self._leftPort.connectorType}{gender[self._leftPort.gender]} to {self._rightPort.connectorType}{gender[self._rightPort.gender]}{model}{serNo}.s2p"
        path : Path = Path(folder, fileName)

        i : int = 0
        if path.exists():
            backup = path.with_suffix(".bak")
            while backup.exists():
                i += 1
                backup = path.with_suffix(".bak" + str(i))
            path.rename(backup)

        self._network.write_touchstone(filename=str(path.stem), dir=str(path.parent))

    
    def loadAllFromFolder(folderPath : Path) -> List['RfAdapter']:

        if not folderPath.is_dir(): return []
        adapterList : List[RfAdapter] = []

        for filePath in folderPath.glob('**/*.s2p'):
            try:
                adapter = RfAdapter(str(filePath.resolve()))
                adapterList.append(adapter)
            except:
                continue

        return adapterList
    

    def dummy(port1: RfPort, port2: RfPort, freq: Frequency = None) -> 'RfAdapter':
        '''Creates an ideal adapter between the given Ports at DC-100GHz'''
    
        if freq == None:
            freq = Frequency(0,100e9,2)

        id = np.identity(2, dtype=complex)
        s = np.tile(id, (len(freq),1))
        nwk = Network(frequency=freq, s=s)

        return RfAdapter(port1, port2, nwk, "Dummy")
    



