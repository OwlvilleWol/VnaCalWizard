import skrf as rf
import skrf.vi.vna as skvna
import skrf.vi.validators as skvalid
import numpy as np
from typing import List,Any,Literal, Callable
from enum import Enum
from vnaCalWizard import CalableVna
from . import HpglUi
from pyvisa.resources import GPIBInstrument
from time import sleep

class HP8720C(skvna.VNA, CalableVna, HpglUi):

    _scpi = False
    _supported_npoints = [3 ,11 , 32, 51, 101, 201, 401, 801, 1601]

    #List of error coefficient keys as used by the skrf 12term calibration dictionary,
    #in the order as returned/requested by the 8720C
    _coefs_list_12term : List[str] = [
        'forward directivity',
        'forward source match',
        'forward reflection tracking',
        'forward isolation',
        'forward load match',
        'forward transmission tracking',
        'reverse directivity',
        'reverse source match',
        'reverse reflection tracking',
        'reverse isolation',
        'reverse load match',
        'reverse transmission tracking'
        ]
    
    _coefs_list_3term: List[str] = [
        'directivity',
        'source match',
        'reflection tracking',
        ]

    class CAL_METHOD(str, Enum):
        NONE = ""
        ONEPORT_1 = "CALIS111"
        ONEPORT_2 = "CALIS221"
        FULL2PORT = "CALIFUL2"

    class RESPONSE(str, Enum):
        NONE = ""
        S11 = "S11"
        S12 = "S12"
        S21 = "S21"
        S22 = "S22"


    class SetFloatValidator(skvalid.Validator):
        def __init__(self, set) -> None:
            self.setvalidator = skvalid.SetValidator(set)
            self.floatvalidator = skvalid.FloatValidator() 
           
        def validate_input(self, arg) -> Any:
            arg = self.floatvalidator.validate_input(arg)
            return self.setvalidator.validate_input(arg)


    def __init__(self, address: str, backend : str | Literal["@ivi", "@py"] ='@ivi', reset: bool = False) -> None:
        super().__init__(address, backend)

        self._resource.timeout = 2_000
        assert '8720C' in self.id

        self._resource.timeout = 60_000
        self.query_delay = 1.

        if reset:
            self.reset()

        self._hpglResource : GPIBInstrument = None
        try:
            res : GPIBInstrument = self._resource
            hpglResourceName : str = res.resource_name.replace(str(res.primary_address) ,str(res.primary_address ^ 1))
            self._hpglResource = res._resource_manager.open_resource(hpglResourceName, open_timeout=res.timeout)
            self._hpglWrite("DF;RS;")
        except Exception as e:
            self._hpglResource = None


    def __del__(self):
        try:
            self._hpglResource.close()
        except:
            pass


    id = skvna.VNA.command(
        get_cmd="OUTPIDEN",
        set_cmd=None,
        doc="""Instrument ID string""",
    )

    last_error = skvna.VNA.command(
        get_cmd="OUTPERRO",
        set_cmd=None,
        doc="""Last error message""",
    )

    freq_start = skvna.VNA.command(
        get_cmd='STAR;OUTPACTI;',
        set_cmd="STAR <arg>;",
        doc="""Start frequency [hz]""",
        validator=skvalid.FreqValidator()
    )

    freq_stop = skvna.VNA.command(
        get_cmd='STOP;OUTPACTI;',
        set_cmd="STOP <arg>;",
        doc="""Stop frequency [hz]""",
        validator=skvalid.FreqValidator()
    )

    npoints = skvna.VNA.command(
        get_cmd='POIN;OUTPACTI;',
        set_cmd="POIN <arg>;",
        doc="""Number of frequency points""",
        validator=SetFloatValidator(_supported_npoints)
    )

    is_continuous = skvna.VNA.command(
        get_cmd="CONT?",
        set_cmd="<arg>", # This is blank on purpose. The command sent is in the BooleanValidator constructor
        doc="""The trigger mode of the instrument""",
        validator=skvalid.BooleanValidator(
            true_response='1',
            false_response='0',
            true_setting='CONT;',
            false_setting='SING;'
        )
    )

    correction_on = skvna.VNA.command(
        get_cmd="CORR?",
        set_cmd="<arg>", # This is blank on purpose. The command sent is in the BooleanValidator constructor
        doc="""The trigger mode of the instrument""",
        validator=skvalid.BooleanValidator(
            true_response='1',
            false_response='0',
            true_setting='CORRON;',
            false_setting='CORROFF;'
        )
    )


    _cal_method_2port = skvna.VNA.command(
        get_cmd="CALIFUL2?",
        set_cmd="<arg>", # This is blank on purpose. The command sent is in the BooleanValidator constructor
        doc="""The trigger mode of the instrument""",
        validator=skvalid.BooleanValidator(
            true_response='1',
            false_response='0',
            true_setting='CALIFUL2;',
            false_setting=';'
        )
    )

    _cal_method_1port1 = skvna.VNA.command(
        get_cmd="CALIS111?",
        set_cmd="<arg>", # This is blank on purpose. The command sent is in the BooleanValidator constructor
        doc="""The trigger mode of the instrument""",
        validator=skvalid.BooleanValidator(
            true_response='1',
            false_response='0',
            true_setting='CALIS111;',
            false_setting=';'
        )
    )

    _cal_method_1port2 = skvna.VNA.command(
        get_cmd="CAL!S221?",
        set_cmd="<arg>", # This is blank on purpose. The command sent is in the BooleanValidator constructor
        doc="""The trigger mode of the instrument""",
        validator=skvalid.BooleanValidator(
            true_response='1',
            false_response='0',
            true_setting='CAL!S221;',
            false_setting=';'
        )
    )  

    @property
    def cal_method(self) -> CAL_METHOD:
        if self._cal_method_1port1: return HP8720C.CAL_METHOD.ONEPORT_1
        if self._cal_method_1port2: return HP8720C.CAL_METHOD.ONEPORT_2
        if self._cal_method_2port: return HP8720C.CAL_METHOD.FULL2PORT
        return HP8720C.CAL_METHOD.NONE

    @cal_method.setter
    def cal_method(self, cal: CAL_METHOD) -> None:
        if cal == HP8720C.CAL_METHOD.FULL2PORT: self._cal_method_2port = True 
        elif cal == HP8720C.CAL_METHOD.ONEPORT_1: self._cal_method_1port1 = True 
        elif cal == HP8720C.CAL_METHOD.ONEPORT_2: self._cal_method_1port2 = True 

    @property
    def response(self) -> RESPONSE:
        if self.query("S11?;") == '1': return HP8720C.RESPONSE.S11
        elif self.query("S12?;") == '1': return HP8720C.RESPONSE.S12
        elif self.query("S21?;") == '1': return HP8720C.RESPONSE.S21
        elif self.query("S22?;") == '1': return HP8720C.RESPONSE.S22
        else: return HP8720C.RESPONSE.NONE

    @response.setter
    def response(self, resp: RESPONSE) -> None:
        if resp == HP8720C.RESPONSE.S11: self.write("S11;")
        elif resp == HP8720C.RESPONSE.S12: self.write("S12;")
        elif resp == HP8720C.RESPONSE.S21: self.write("S21;")
        elif resp == HP8720C.RESPONSE.S22: self.write("S22;")
        else: pass


    status = skvna.VNA.command(
        get_cmd='ESR?',
        set_cmd=None,
        doc="""Retrieve the value of the Event Status Register (ESR)""",
    )

    @property
    def frequency(self) -> rf.Frequency:
        return rf.Frequency(
            start=self.freq_start,
            stop=self.freq_stop,
            npoints=self.npoints,
            unit='Hz'
        )

    @frequency.setter
    def frequency(self, f: rf.Frequency) -> None:
        if f.npoints not in self._supported_npoints:
            raise ValueError("The 8720C only supports one of {self._supported_npoints}.")

        self._resource.clear()
        self.write(f'STEP; STAR {int(f.start)}; STOP {int(f.stop)}; POIN{f.npoints};')
        self.freq_start = f.start
        self.freq_stop = f.stop
        self.npoints = f.npoints

    @property
    def query_format(self) -> skvna.ValuesFormat:
        return self._values_fmt

    @query_format.setter
    def query_format(self, arg: skvna.ValuesFormat) -> None:
        fmt = {
            skvna.ValuesFormat.ASCII: "FORM4;",
            skvna.ValuesFormat.BINARY_32: "FORM2;",
            skvna.ValuesFormat.BINARY_64: "FORM3;"
        }[arg]

        self._values_fmt = arg
        self.write(fmt)

    def reset(self) -> None:
        self.write('OPC?;PRES;')
        self.wait_until_finished()
        self.query_format = skvna.ValuesFormat.ASCII

    def wait_until_finished(self) -> None:
        r: str = self.read()
        assert r.strip('\n') == '1'

    def get_complex_data(self, cmd: str) -> np.ndarray:
        self.query_format = skvna.ValuesFormat.BINARY_32
        # Query values will interpret the response as floats, but the first 4
        # bytes are a header. Since it gets cast to a 4-byte float, we can just
        # ignore the first "value"
        # TODO: Is this correct? or is the header already handled in query_binary_values?
        raw = self.query_values(cmd, container=np.array, delay=self.query_delay, header_fmt="hp", is_big_endian=True)
        vals = raw.reshape((-1, 2))
        vals_complex = (vals[:,0] + 1j * vals[:,1]).flatten()
        return vals_complex

    def _get_single_sweep(self, parameter: tuple[int, int], sweep: bool=True):
        if any(p not in {1,2} for p in parameter):
            raise ValueError("The elements of parameter must be 1, or 2.")

        self.write(f"s{parameter[0]}{parameter[1]}")

        if sweep:
            self.sweep()

        ntwk = rf.Network(name=f"S{parameter[0]}{parameter[1]}")
        ntwk.s = self.get_complex_data("OUTPDATA")
        ntwk.frequency = self.frequency

        return ntwk

    def _get_two_port_sweeps(self, sweep: bool=True) -> rf.Network:
        s11 = self._get_single_sweep((1, 1))
        freq = s11.frequency
        s11 = s11.s[:, 0, 0]
        s12 = self._get_single_sweep((1, 2)).s[:, 0, 0]
        s21 = self._get_single_sweep((2, 1)).s[:, 0, 0]
        s22 = self._get_single_sweep((2, 2)).s[:, 0, 0]

        ntwk = rf.Network()
        ntwk.s = np.array([
            [s11, s21],
            [s12, s22]
        ]).transpose().reshape((-1, 2, 2))
        ntwk.frequency = freq

        return ntwk

    def get_network(self, ports: rf.Sequence = {1,2}) -> rf.Network:
        if not set(ports).issubset({1,2}):
            raise ValueError("This instrument only has two ports. Must pass 1, 2, or (1,2)")

        if len(ports) == 1:
            p = ports[0]
            return self._get_single_sweep((p, p))
        else:
            return self._get_two_port_sweeps()

    def sweep(self) -> None:
        self.write('OPC?;SING;')
        self.wait_until_finished()


    @property
    def calibration(self) -> rf.Calibration:
        """The currently defined calibration as a :class:`skrf.calibration.calibration.Calibration`"""
        
        cm = self.cal_method
        cal_dict = {}

        if cm == HP8720C.CAL_METHOD.FULL2PORT:
            for i in range(12):
                query = 'OUTPCALC{:02d}'.format(i+1)
                vals = self.query_values(query, container=np.array, complex_values=True, header_fmt="hp", is_big_endian=True)
                cal_dict[HP8720C._coefs_list_12term[i]] = vals
            return rf.TwelveTerm.from_coefs(self.frequency, cal_dict)
        elif cm == HP8720C.CAL_METHOD.ONEPORT_1 | cm == HP8720C.CAL_METHOD.ONEPORT_2:
            for i in range(3):
                query = 'OUTPCALC{:02d}'.format(i+1)
                vals = self.query_values(query, container=np.array, complex_values=True, header_fmt="hp", is_big_endian=True)
                cal_dict[HP8720C._coefs_list_3term[i]] = vals
            return rf.OnePort.from_coefs(self.frequency, cal_dict)
        else:
            return None


    @calibration.setter
    def calibration(self, cal: rf.Calibration) -> None:

        if isinstance(cal,rf.TwelveTerm):
            self.cal_method = HP8720C.CAL_METHOD.FULL2PORT          
            for i in range(12):
                query = 'INPUCALC{:02d}'.format(i+1)
                self.write_values(query, cal.coefs_12term[HP8720C._coefs_list_12term[i]], complex_values=True, header_fmt="hp", is_big_endian=True)

        elif isinstance(cal,rf.OnePort):
            
            #check if S22 response is selected, if yes apply oneport cal to port2. In any other case apply oneport cal for port1
            if self.response != HP8720C.RESPONSE.S22:
                self.cal_method = HP8720C.CAL_METHOD.ONEPORT_1    
            for i in range(3):
                query = 'INPUCALC{:02d}'.format(i+1)
                self.write_values(query, cal.coefs_3term[HP8720C._coefs_list_3term[i]], complex_values=True, header_fmt="hp", is_big_endian=True)
        else:
            return

        self.write("SAVC;")
        self.correction_on = True
  

    def plot_data_on_vna(self, data=np.array):
        self.write_values("INPUDATA", data, complex_values=True, header_fmt="hp", is_big_endian=True)        



    def _hpglWrite(self, command : str) -> None:
        try:
            self._hpglResource.write(command)
        except:
            pass


    def _hpglCls(self) -> None:
        self._hpglWrite("AF;")

    
    def _hpglInstrumentScreenOn(self, on : bool = True) -> None:
        self._hpglWrite("RS" if on else "CS") 

    
    def _hpglPrintLabel(self, text : str, x: int, y: int, pen : int = 1, textSize : tuple[int,int] = (16,20), align : Literal["left", "right", "center"] = "left"):  
        if align == "right":
            x = x - len(text)*textSize[0]*5
        elif align == "center":
            x = int(x - len(text)*textSize[0]*2.5)
        text = text + chr(3)
        self._hpglWrite(f"PU;SI.{textSize[0]},.{textSize[1]};SP{pen};PA {x},{y};PD;LB{text};PU;")

    
    def _hpglDrawLine(self, x1,y1,x2,y2 : int, pen : int = 1):
        self._hpglWrite(f"SP{pen};PU;PA {x1},{y1};PD;PA {x2},{y2};PU;")


    def _hpglPrintMenuItem(self, text : str, menuIndex : Literal[1,2,3,4,5,6,7,8]) -> None:

        ymax = 3900
        ymin = 50
        yspac = 520
        x = 5800
        yloc = {1 : ymax, 2 : ymax-yspac, 3 : ymax-yspac*2, 4 : ymax-yspac*3, 5 : ymin+yspac*3 , 6 : ymin+yspac*2 , 7 : ymin+yspac*1, 8 : ymin}

        self._hpglPrintLabel(text, x, yloc[menuIndex], 7, align="right")



    def _waitForKeypress(self)-> int | None:

        softkeys = {60: 1, 61: 2, 56: 3, 59: 4, 4: 5, 57: 6, 58: 7, 10: 8}

        try:
            self.write("CLES;")
            while True:
                esr : int = int(self.query("ESR?;"))
                if (esr & 0b01000000) != 0:
                    key = int(self.query("OUTPKEY;"))
                    if (key in softkeys):
                        return softkeys[key]
                sleep(0.1)
        except:
            return None
        
    
    @property
    def operatorPrompt(self) -> None | Callable[[str, dict[int, tuple[str, str]]] ,str]:
        if self._hpglResource == None:
            return None
        else:
            return lambda prompt,options: self._operatorPrompt(prompt, options) 
    

    def _operatorPrompt(self, prompt : str, options : dict[int, tuple[str, str]]) -> str:
        self.write("MENUOFF")
        self._hpglPrintLabel(prompt, 2500, 3400, 7, align="center")

        for option in options:
            buttonText = options[option][0]
            self._hpglPrintMenuItem(buttonText, option) 
        
        while True:
            keyPress = self._waitForKeypress()
            if keyPress == None: 
                self._hpglCls()
                self._hpglInstrumentScreenOn(True)
                return None
            if keyPress in options: 
                self._hpglCls()
                self._hpglInstrumentScreenOn(True)
                return options[keyPress][1]