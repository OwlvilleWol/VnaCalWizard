from hp8720c import HP8720C


vna = HP8720C("GPIB0::16::INSTR", reset=False, backend="@ivi")
print(vna.frequency)

vna.npoints = 201
network = vna.get_network([1])

print(network)