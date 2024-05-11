# Python library for calibrating VNAs with legacy HP/Agilent ECal modules 

References, or the Giants from [HP-Agilent-Keysight-equipment on groups.io](https://groups.io/g/HP-Agilent-Keysight-equipment) on whose shoulders we stand:  
Staffan’s [writeup in PDF](<https://groups.io/g/HP-Agilent-Keysight-equipment/files/All HP, Agilent and Keysight instruments in folders by part numbers/A 80000 to 89999/85062/ECal 85062-60006 rev B.pdf>) -  [testjarfalla63\@gmail.com](mailto:testjarfalla63\@gmail.com)  
[Docs, libraries and ECal data dump](<https://groups.io/g/HP-Agilent-Keysight-equipment/files/All HP, Agilent and Keysight instruments in folders by part numbers/A 80000 to 89999/85062/HP8506x ECal Interface.zip>) by Wayne Knowles, ZL2BKC - [w.knowles\@xtra.co.nz](mailto:w.knowles\@xtra.co.nz)  

## Project Goals

- Control HP/Agilent 8506x, 8509x, potentially N443x, and N446x series ECal modules, read module information and standard characterization data
- Using above perform 1 or 2 port calibration on supported VNA(s) via Scikit-rf
- Support for cascaded frequency ranges of 2 ECal modules
- Support adapter characterization and removal for insertable (M-F) module configurations
- Make code extensible with ECal iterfaces, VNAs, calibration methods, etc.

## What do you need

- #### HP/Agilent 8720C VNA
  Adding support for any similar models like the 8510 or 8753 should be straightforward. System can be made to work with **any analyzer** that supports sending uncorrected sweep data out and can take (3 or 12 term) error coefficients in digitally.
- #### HP-IB (GPIB) Interface to the VNA
  Development is done using NI GPIB-USB-HS

ECal module(s)8506x,8509x (B/C rev, A?)N4431A, N446x - ? - per the 85097B manual yes, but I’m yet to try one for compatibility 
ECal control adapter and power suppliesSee examples later in this document. Control code can be also modified to support other interfaces.
Python library: https://github.com/OwlvilleWol/VnaCalWizard
Some basic Python knowledge
Library dependencies (some based on the hardware used)Python ~3.11, scikit-rf, pyVisa, ftd2xx, Camino









