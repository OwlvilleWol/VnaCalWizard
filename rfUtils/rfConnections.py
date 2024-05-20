from skrf import Network, Frequency, overlap
from . import FrequencyEx
from typing import overload, List, Tuple
from pathlib import Path
from enum import Enum
from abc import ABC, abstractmethod
import re
import numpy as np



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


class ConnectorGender(Enum):
    MALE = 0
    FEMALE = 1
    GENDERLESS = 2

    def __str__(self) -> str:
        if self == ConnectorGender.MALE: return "male"
        if self == ConnectorGender.FEMALE: return "female"
        if self == ConnectorGender.GENDERLESS: return ""



class RfPort:

    def __init__(self, connectorType: str, gender: ConnectorGender, device: 'RfNPort' = None, name: str = "") -> None:
        self._name = name
        self._connectorType = connectorType
        self._gender = gender
        self._device = device

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def connectorType(self) -> str:
        return self._connectorType
    
    @property
    def device(self) -> 'RfNPort':
        return self._device
    
    @property
    def gender(self) -> ConnectorGender:
        return self._gender

    def __and__(self, other : 'RfPort') -> bool:
        if not isinstance(other, RfPort): return NotImplemented
        if isinstance(other, RfPortnt): return False

        if other.connectorType != self.connectorType: return False
        if (self.gender == ConnectorGender.GENDERLESS) & (other.gender == ConnectorGender.GENDERLESS): return True
        if (self.gender == ConnectorGender.FEMALE) & (other.gender == ConnectorGender.MALE): return True
        if (self.gender == ConnectorGender.MALE) & (other.gender == ConnectorGender.FEMALE): return True
        return False
    
    def __str__(self) -> str:
        elements : List[str] = []
        if self.name != None & self.name != "": elements.append(self.name)
        elements.append(self.connectorType)
        if self.gender != ConnectorGender.GENDERLESS: elements.append(str(self.gender))
        return " ".join(elements)
        
    def instanceOn(self, device) -> 'RfPort':
        return RfPort(self.connectorType, self.gender, device, self.name)


class RfPortnt(RfPort):
    '''Get it? RfPortn't, heh, heh.'''
    def __init__(self) -> None:
        pass

    @property
    def name(self) -> str:
        return ""
    
    @property
    def connectorType(self) -> str:
        return ""
    
    @property
    def device(self) -> 'RfNPort':
        return None
    
    @property
    def gender(self) -> ConnectorGender:
        return ConnectorGender.GENDERLESS

    def __and__(self, other : 'RfPort') -> bool:
        return False
    
    def __str__(self) -> str:
        return ""
        
    def instanceOn(self, device) -> 'RfPort':
        return NotImplemented


class RfPath(ABC):

    @property
    @abstractmethod
    def left(self) -> RfPort:
        ...

    @property
    @abstractmethod
    def right(self) -> RfPort:
        ...
        
    @abstractmethod
    def __copy__(self) -> 'RfPath':
        ...
    
    @property
    @abstractmethod
    def network(self) -> Network:
        ...
    
    @property
    @abstractmethod
    def frequency(self) -> FrequencyEx:
        ...
    
    @property
    @abstractmethod
    def isReverse(self) -> bool:
        ...
    
    @property
    @abstractmethod
    def autoOriented(self) -> 'RfPath':
        ...
    
    @property
    @abstractmethod
    def flipped(self) -> "RfPath":
        ...
    
    @property
    @abstractmethod
    def reverse(self) -> "RfPath":
        ...
    
    @property
    @abstractmethod
    def forward(self) -> "RfPath":
        ...

    @property
    def copy(self) -> "RfPath":
        return self.__copy__()
    
    @property
    @abstractmethod
    def isAutoOrient(self) -> bool:
        ...


    def cascadePaths(leftPath: 'RfPath', rightPath: 'RfPath', ignoreMate : bool = False) -> 'RfPathCascade':

        if not ignoreMate:
            if not (leftPath.right & rightPath.left):
                raise UnmateableRfConnectionException(leftPath.right, rightPath.left)

        return RfPathCascade([leftPath.copy, rightPath.copy], False, False)


    def cascadePort(path: 'RfPath', port: RfPort, ignoreMate : bool = False) -> 'RfPort':
        
        if not ignoreMate:
            if not (path.right & port):
                raise UnmateableRfConnectionException(path.right, port)        
        
        return path.left 


    def __pow__(self, other: 'RfPath' | RfPort) -> 'RfPath' | RfPort:

        if isinstance(other, RfPath):
            try:
                return RfPath.cascadePaths(self, other)
            except UnmateableRfConnectionException as e:
                if self.isAutoOrient:
                    return RfPath.cascadePaths(self.flipped, other)
                else: raise e
        elif isinstance(other, RfPort):       
            try:  
                return RfPath.cascadePort(self, other)
            except UnmateableRfConnectionException as e:
                if self.isAutoOrient:
                    return RfPath.cascadePort(self.flipped, other)
                else: raise e
        else:
            return NotImplemented


    def __rpow__(self, other: 'RfAdapter' | RfPort) -> 'RfAdapter' | RfPort:

        if isinstance(other, RfPath):
            try:
                return RfPath.cascadePaths(other, self)
            except UnmateableRfConnectionException as e:
                if self.isAutoOrient:
                    return RfPath.cascadePaths(other, self.flipped)
                else: raise e
        elif isinstance(other, RfPort):       
            try:  
                return RfPath.cascadePort(self.flipped, other)
            except UnmateableRfConnectionException as e:
                if self.isAutoOrient:
                    return RfPath.cascadePort(self, other)
                else: raise e
        else:
            return NotImplemented


    def __and__(self, other: 'RfPath' | RfPort) -> bool:

        if isinstance(other, RfPath):
            if self.right & other.left: return True
            elif self.isAutoOrient & (self.left & other.left): return True
            else: return False
        elif isinstance(other, RfPort):
            if self.right & other: return True
            elif self.isAutoOrient & (self.right & other): return True
            else: return False
        else:
            return NotImplemented
        

    def __rand__(self, other: 'RfPath' | RfPort) -> bool:

        if isinstance(other, RfPath):
            if other.right & self.left: return True
            elif self.isAutoOrient & (other.right & self.right): return True
            else: return False
        elif isinstance(other, RfPort):
            if other & self.left: return True
            elif self.isAutoOrient & (other & self.right): return True
            else: return False
        else:
            return NotImplemented


class RfPathTerminated(RfPath):

    def __init__(self, P1: RfPort, device: 'RfNPort', isReverse : bool = False, isAutoOrient : bool = False) -> None:
        self._P1 : RfPort = P1
        self._device : 'RfNPort' = device
        self._isReverse : bool = isReverse
        self._isAutoOrient : bool = isAutoOrient

    @property
    def left(self) -> RfPort:
        if self._isReverse == False:
            return self._P1
        else:
            return RfPortnt()

    @property
    @abstractmethod
    def right(self) -> RfPort:
        if self._isReverse == False:
            return RfPortnt()
        else:
            return self._P1
        
    @abstractmethod
    def __copy__(self) -> 'RfPath':
        return RfPathTerminated(self._P1, self._device, self._isReverse, self._isAutoOrient)
    
    @property
    def network(self) -> Network:
        return self._device.network(self).copy()
    
    @property
    def frequency(self) -> FrequencyEx:
        return self._device.frequency(self)
    
    @property
    def isReverse(self) -> bool:
        return self._isReverse
    
    @property
    def autoOriented(self) -> 'RfPath':
        copy : RfPathTerminated = self.__copy__()
        copy._isAutoOrient = True
        return copy
    
    @property
    def flipped(self) -> "RfPath":
        copy : RfPathTerminated = self.__copy__()
        copy._isAutoOrient = False
        copy._isReverse = not self._isReverse
        return copy
    
    @property
    def reverse(self) -> "RfPath":
        copy : RfPathTerminated = self.__copy__()
        copy._isAutoOrient = False
        copy._isReverse = True
        return copy
    
    @property
    def forward(self) -> "RfPath":
        copy : RfPathTerminated = self.__copy__()
        copy._isAutoOrient = False
        copy._isReverse = False
        return copy

    @property
    def isAutoOrient(self) -> bool:
        return self._isAutoOrient



class RfPathSingle(RfPath):

    def __init__(self, P1: RfPort, P2: RfPort, device: 'RfNPort', isReverse : bool = False, isAutoOrient : bool = False) -> None:
        self._P1 : RfPort = P1
        self._P2 : RfPort = P2
        self._device : 'RfNPort' = device
        self._isReverse : bool = isReverse
        self._isAutoOrient : bool = isAutoOrient

    @property
    def left(self) -> RfPort:
        if self._isReverse:
            return self._P2
        else:
            return self._P1

    @property
    def right(self) -> RfPort:
        if self._isReverse:
            return self._P1
        else:
            return self._P2
        
    def __copy__(self) -> 'RfPath':
        return RfPathSingle(self._P1, self._P2, self._device, self._isReverse, self._isAutoOrient)
    
    @property
    def network(self) -> Network:
        if self._isReverse == False:
            return self._device.network(self).copy()
        else:
            return self._device.network(self).flipped()
    
    @property
    def frequency(self) -> FrequencyEx:
        return self._device.frequency(self)
    
    @property
    def isReverse(self) -> bool:
        return self._isReverse
    
    @property
    def autoOriented(self) -> 'RfPath':
        copy : RfPathSingle = self.__copy__()
        copy._isAutoOrient = True
        return copy
    
    @property
    def flipped(self) -> "RfPath":
        copy : RfPathSingle = self.__copy__()
        copy._isAutoOrient = False
        copy._isReverse = not self._isReverse
        return copy
    
    @property
    def reverse(self) -> "RfPath":
        copy : RfPathSingle = self.__copy__()
        copy._isAutoOrient = False
        copy._isReverse = True
        return copy
    
    @property
    def forward(self) -> "RfPath":
        copy : RfPathSingle = self.__copy__()
        copy._isAutoOrient = False
        copy._isReverse = False
        return copy

    @property
    def isAutoOrient(self) -> bool:
        return self._isAutoOrient


class RfPathCascade(RfPath):
    
    def __init__(self, elements: List[RfPath], isReverse : bool = False, isAutoOrient : bool = False) -> None:
        self._elements = elements
        self._isReverse = isReverse
        self._isAutoOrient = isAutoOrient
        if len(self._elements) == 0:
            raise Exception("Can't instantiate Rf path cascade without elements.")

    @property
    def left(self) -> RfPort:
        if self._isReverse:
            return self._elements[-1].right
        else:
            return self._elements[0].left

    @property
    def right(self) -> RfPort:
        if self._isReverse:
            return self._elements[0].left
        else:
            return self._elements[-1].right
        
    def __copy__(self) -> 'RfPath':
        newElements : List[RfPath] = []
        for e in self._elements:
            newElements.append(e.__copy__())
        return RfPathCascade(newElements, self._isReverse, self._isAutoOrient)
    
    @property
    def network(self) -> Network:
        if self._isReverse == False:
            cascade : Network = self._elements[0].network
            for element in self._elements[1:]:
                networks : Tuple[Network] = overlap(cascade, element.network)
                cascade = networks[0] ** networks[1]
            return cascade
        else:
            cascade : Network = self._elements[-1].flipped.network
            for element in reversed(self._elements[:-1]):
                networks : Tuple[Network] = overlap(cascade, element.flipped.network)
                cascade = networks[0] ** networks[1]
            return cascade
    
    @property
    def frequency(self) -> FrequencyEx:
        return FrequencyEx.toEx(self.network.frequency)
    
    @property
    def isReverse(self) -> bool:
        return self._isReverse
    
    @property
    def isAutoOrient(self) -> bool:
        return self._isAutoOrient
    
    @property
    def autoOriented(self) -> 'RfPath':
        copy : RfPathCascade = self.__copy__()
        copy._isAutoOrient = True
        return copy
    
    @property
    def flipped(self) -> "RfPath":
        copy : RfPathCascade = self.__copy__()
        copy._isAutoOrient = False
        copy._isReverse = not self._isReverse
        return copy
    
    @property
    def reverse(self) -> "RfPath":
        copy : RfPathCascade = self.__copy__()
        copy._isAutoOrient = False
        copy._isReverse = True
        return copy
    
    @property
    def forward(self) -> "RfAdapter":
        copy : RfPathCascade = self.__copy__()
        copy._isAutoOrient = False
        copy._isReverse = False
        return copy

    @property
    def elements(self) -> List[RfPath]:
        if self._isReverse == False:
            return self._elements
        else:
            return reversed(self._elements)
    
    @property
    def flattened(self) -> 'RfPathCascade':
        copy : RfPathCascade = self.__copy__()
        newElements : List[RfPath] = []
        for element in copy._elements:
            if isinstance(element, RfPathCascade):
                cascadeElement : RfPathCascade = element
                newElements += cascadeElement.flattened._elements
        return RfPathCascade(newElements, self._isReverse, self._isAutoOrient)
    
    def __getitem__(self, items) -> RfPath | List[RfPath]:
        if self._isReverse == False:
            return self._elements[items]
        else:
            return reversed(self._elements)[items]
        
  



class RfNPort(ABC):

    def __init__(self) -> None:
        self._ports : dict[str, RfPort] = {}
        self._paths : List[RfPath] = []
        pass

    @property
    def port(self) -> dict[str, RfPort]:
        return self._ports

    @property
    def ports(self) -> List[RfPort]:
        return list(self._ports.values)
    
    @abstractmethod
    def network(self, path : 'RfPath') -> Network:
        ...

    @abstractmethod
    def frequency(self, path : 'RfPath') -> FrequencyEx:
        ...

    @property
    @abstractmethod
    def paths(self) -> List[RfPath]:
        ...
    


class RfAdapter(RfNPort):

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
        
        super.__init__(self)

        if data != None:
            self._data = data
            self._ports["1"] = port1.instanceOn(self)
            self._ports["2"] = port2.instanceOn(self)
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
                self._ports["1"] = p1
                self._ports["2"] = p2
                self._sn = sn
                self._model = model

                self._network : Network = Network(str(p.resolve()))

            except Exception as e:
                self._filePath = None
                self._ports = {}
                self._sn = None
                self._model = None
                self._network = None

                raise e
 
            self._auto : bool = False
            
        else:
            self._filePath = None
            self._ports = {}
            self._sn = None
            self._model = None
            self._network = None

            return 
        
    def __copy__(self) -> 'RfAdapter':
        return RfAdapter(self._ports["1"], self._ports["2"], self._network.copy(), self._model, self._sn)

    def network(self, path : 'RfPath' = None) -> Network:
        if self._network != None: 
            if path == None | path.isReverse == False:
                return self._network.copy()
            else:
                return self._network.flipped()
        else:
            raise Exception("No network data loaded for RF Adapter.")

    def frequency(self, path: 'RfPath' = None) -> FrequencyEx:
        if self._network != None: 
            return FrequencyEx.toEx(self._network.frequency)
        else:
            raise Exception("No network data loaded for RF Adapter.")

    @property
    def paths(self) -> List[RfPath]:
        return [self.path]

    @property
    def path(self) -> RfPath:
        return RfPathSingle(self._ports["1"], self._ports["2"], self, False, False)


    def saveToFile(self, folder: str) -> None:

        if self._data == None:
            raise Exception("There is no network data to save.")

        if self._ports["A"] == None | self._ports["B"] == None:
            raise Exception("Insufficient port information.")
        
        gender : dict[ConnectorGender, str] = {ConnectorGender.MALE: "M", ConnectorGender.FEMALE: "F", ConnectorGender.GENDERLESS: ""}
        serNo = f" {self._sn}" if self._sn != None else ""
        model = f" {self._model}" if self._model != None else ""

        fileName: str = f"Adapter {self.port["1"].connectorType}{gender[self.port["1"].gender]} to {self.port["2"].connectorType}{gender[self.port["2"].gender]}{model}{serNo}.s2p"
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
    



