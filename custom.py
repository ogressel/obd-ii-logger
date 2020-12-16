#!/usr/bin/python

import obd
from obd import OBDCommand
from obd.protocols import ECU
from obd.utils import bytes_to_int

def gear_position(messages):
    """ decoder for 'gear_position' messages """
    d = messages[0].data # only operate on a single message
    d = d[2:] # chop off mode and PID bytes
    v = bytes_to_int(d) / 4.0  # helper function for converting byte arrays to ints
    return v

cmd = OBDCommand("GEAR_POS",        # name
                 "gear position",   # description
                 b"02889",          # command
                 1,                 # number of return bytes to expect
                 gear_position,     # decoding function
                 ECU.ENGINE,        # (optional) ECU filter
                 True)              # (optional) allow a "01" to be added for speed

obd = obd.OBD()

obd.supported_commands.add(cmd)
response = obd.query(cmd)

print(response)
