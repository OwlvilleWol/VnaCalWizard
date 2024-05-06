import gpib_ctypes as gpibctypes
import gpib_ctypes.gpib.gpib as gggpib
import numpy as np
import pyvisa
import skrf.vi.vna as skvna




#l = gggpib._load_lib("C:\Windows\SysWOW64\gpib-32.dll")
#l = gggpib._load_lib()
#gpibctypes.make_default_gpib()


#g = gpibctypes.gpib_ctypes.Gpib.Gpib("GPIB0")


#print(g)

#g.close()

from hp8720c import HP8720C


vna = HP8720C("GPIB0::16::INSTR", reset=False, backend="@ivi")

print(vna.frequency)

r : pyvisa.resources.Resource = vna._resource
print(r.visalib)

#d = np.random.random(size=3) + 1.j * np.random.random(size=3)

vna.npoints = 201

#vna.query_format = skvna.ValuesFormat.BINARY_64
#vna.show_data(d)

n = vna.get_network([1])


pass