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
- #### ECal module(s)
  **8506x,8509x** (B/C rev, A?)  
  **N4431A, N446x** - maybe - per the 85097B manual yes, but I’m yet to try one for compatibility
- #### ECal control adapter and power supplies
  See examples later in this document. Control code can be modified to support other interfaces.
- #### Some basic Python knowledge
  Until someone makes a UI
- #### Library dependencies
  TBD

## ECal Control Hardware Examples  
In this section easy to build examples are presented to connect the ECal module to your PC.
- #### What these don’t do (that they maybe should)
  - Isolate USB ground
  - Check for ECal presence, or handle hot-swap
  - Filter, condition or switch power supplies
  - Filter data and control lines, or implement ESD protection
  - Provide +12V required for Flash memory write
  - Monitor current draw for warmup and fault detection
- #### What these do
  - Work

### 1. FTDI based solution
The benefit is that every element of the operation can be programmed on the host PC, as part of the Python library. The FTDI module merely operates as a USB-GPIO interface for bit level control of the ECal module. Downside of the presented example is that the FT2232D chip used -for its dual 8bit GPIO ports- is depreciated and its successor the FT2232H operates only at a 3.3V IO voltage, needing level shifters. Moreover, the two ports manifest as two separate USB devices and aren’t synchronized with each other. Worst of all, pin direction changes take about 20ms, thus limiting Flash read speed to about 50Byte/s. To pull the full characterization data from the 85062, for example, takes over 45 minutes. (It only must be done once, though.)  
Apart from this it is a simple, no hassle setup.  
  
Meant to be used with the ecalControl.ecalHalFtdi.ECalHalFtdi hardware abstraction layer class.

#### Parts
- [DLP-2232ML FTDI FT2232D module](https://www.digikey.com/short/w24rvtz0)
- [D-Sub 25-pin IDC cable assembly](https://a.co/d/9McZ1qI)
- [USB Type-C breakout](https://a.co/d/ejkzXOb)

![](/doc/img/schECalFtdi.svg)

### 2. Arduino based solution
For its simplicity and 5V IO the Arduino Nano Every was chosen for this example. The downside is that separate code must be downloaded to the device (and maintained) and communication between the Arduino and the PC relies on yet another 3rd party library.
On the upside the board used is in active production and without the direction switching bottleneck ECal Flash read speed is ~20 times faster compared to above FTDI example.  

Meant to be used with the ecalControl.ecalHalCamino.ECalHalCamino hardware abstraction layer class.  
Software uses the Camino library for serial communication between the Arduino and the PC.  
Find the Arduino code under [/ecalControl/arduino](/ecalControl/arduino)

#### Parts
- [Arduino Nano Every](https://docs.arduino.cc/hardware/nano-every/)
- [D-Sub 25-pin jumper board](https://a.co/d/hQ9iDCi)

![](/doc/img/schECalArduino.svg)

### 3. Power supplies

I used DIN rail mount AC/DC power supplies, but probably these are overkill.
From prior work it is unclear which of the possible four power rails are necessary for which ECal models.

- **+24V** On the 85062 the 24V is used to bias the pin diodes as well as to run the module heater. The 85097A/B interface module takes a single +24V 1A input.
- **+12V** This might only be used as supply voltage for the on-board Flash memory for write operation. No issues without it on the 85062 and 85093.
- **-12V** Unclear what it does or if it is really needed. I kept it connected. Let me know if you know better.
- **+5V** Two separate rails for logic and analog. Unclear if analog 5V is used separately on any modules. On the 85062 they are connected together. I used one supply to drive both 5V rails.

#### Parts
- [Mean Well HDR-60-24 24V 60W DIN rail mount PSU](https://a.co/d/216mub7)
- [Mean Well HDR-15-5 5V 15W DIN rail mount PSU](https://a.co/d/fFkN42M)
- [Mean Well HDR-15-12 12V 15W DIN rail mount PSU](https://a.co/d/1o75U8v)  (In reverse for -12V.)










