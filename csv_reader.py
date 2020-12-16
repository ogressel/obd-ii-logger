#!/usr/bin/python
#
#

import csv

# --- integer from hexadecimal string

_hex = lambda val: 0 if val=="" else int( "0x%s" % val, 16 )
_float = lambda val: 0. if val=="" else float(val)

# --- OBD-II sensor class (matching TorquePro-style CSV file)

class obd_sensors:

    name = ""       # long name
    nm = ""         # short name
    pid = 0         # mode + PID
    eqn = ""        # algebraic expression for unpacking values
    minv = 0        # smalles possible value
    maxv = 0        # biggest possible value
    unit = ""       # physical unit descriptor
    hdr = 0         # OBD-II header

    # --- constructor

    def __init__(self, row = []):

        self.name = (row[0])[1:]
        self.nm = row[1]

        self.pid = _hex(row[2])
        self.eqn = row[3]

        self.minv = _float(row[4])
        self.maxv = _float(row[5])

        self.unit = row[6]
        self.hdr = _hex(row[7])

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
    next(reader, None)  # skip the headers

    for row in reader:
        sensor = obd_sensors(row[:])
        if(sensor.name!=""):
            my_obd_sensors.append(sensor)

print(my_obd_sensors)
