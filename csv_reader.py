#!/usr/bin/python
#
#

import csv
import numpy as np

# --- utility functions

_hex = lambda val: 0 if val=="" else int( "0x%s" % val, 16 )
_float = lambda val: 0. if val=="" else float(val)
Signed = lambda val: np.int16(val)

# --- OBD-II sensor class (matching TorquePro-style CSV file)

class obd_sensors:

    name = ""       # long name
    nm = ""         # short name
    pid = 0         # mode + PID
    eqn = ""        # algebraic expression for unpacking values
    minv = 0        # smallest possible value
    maxv = 0        # biggest possible value
    unit = ""       # physical unit descriptor
    hdr = 0         # OBD-II header

    # --- constructor

    def __init__(self, value = []):

        self.name = (value[0])[1:] # omit leading character
        self.nm = value[1]

        self.pid = _hex(value[2])
        self.eqn = value[3]

        self.minv = _float(value[4])
        self.maxv = _float(value[5])

        self.unit = value[6]
        self.hdr = _hex(value[7])

    # --- print object values

    def __repr__(self):
        return \
            "OBD sensor object:" \
            " name='%s', nm='%s', pid='%s', eqn='%s'," \
            " minv='%g', maxv='%g', unit='%s', hdr='%s'\n" \
            % ( self.name, self.nm, hex(self.pid), self.eqn,
                self.minv, self.maxv, self.unit, hex(self.hdr) )

# --- import the CSV file

my_obd_sensors = []

with open('Bolt.csv', 'r') as f:

    reader = csv.reader(f)
    next(reader, None)  # skip the header

    for row in reader:
        sensor = obd_sensors(row[:])

        if(sensor.name!=""):  # skip empty lines
            my_obd_sensors.append(sensor)

print(my_obd_sensors)
