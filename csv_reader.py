#!/usr/bin/python3
#
#

from h5py import File
from time import time, sleep
from datetime import datetime

import obd
from obd import OBD, OBDCommand
from obd.protocols import ECU


# --- utility functions -------------------------------------------------------

_float = lambda val: 0. if val=="" else float(val)
Signed = lambda val: (val & 0xff) - (1<<8) if val >= (1<<7) else val

# --- OBD-II sensor class (matching TorquePro-style CSV file) -----------------

class obd_sensors:

    name = ""       # long name
    nm = ""         # short name
    pid = 0         # mode + PID
    eqn = ""        # algebraic expression for unpacking values
    minv = 0        # smallest possible value
    maxv = 0        # biggest possible value
    unit = ""       # physical unit descriptor
    hdr = 0         # OBD-II header
    tms = 0         # time series of data
    nbt = 0         # number of bytes returned
    cmd = 0         # query command object

    # --- constructor

    def __init__(self, value = []):

        self.name = value[0]
        self.nm = value[1].replace(' ', '_')

        self.pid = bytes(value[2],encoding='ascii')
        self.eqn = value[3]

        self.minv = _float(value[4])
        self.maxv = _float(value[5])

        self.unit = value[6]
        self.hdr = bytes(value[7],encoding='ascii')
        self.tms = []

        self.nbt=0
        if "A" in self.eqn: self.nbt=1
        if "B" in self.eqn: self.nbt=2
        if "C" in self.eqn: self.nbt=3
        if "D" in self.eqn: self.nbt=4

        self.cmd = OBDCommand( self.nm,     # name
                               self.name,   # description
                               self.pid,    # command
                               0,    #### number of return bytes to expect
                               decode_pid,  # decoding function
                               ECU.UNKNOWN, # (opt) ECU filter
                               True,        # (opt) "01" may be added for speed
                               self.hdr )   # (opt) custom PID header

    # --- print object values

    def __repr__(self):
        return \
            "OBD sensor object:" \
            " name='%s', nm='%s', pid='%s', eqn='%s'," \
            " minv='%g', maxv='%g', unit='%s', hdr='%s'\n" \
            % ( self.name, self.nm, hex(self.pid), self.eqn,
                self.minv, self.maxv, self.unit, hex(self.hdr) )

    # --- callback method for data accumulationa

    def accumulate(self,result):

        self.tms.append( [ time()-start_time, result.value ] )


# --- callback function for decoding messages ---------------------------------

def decode_pid(messages):

    """ generic decoder function for OBD-II messages """

    #for i,msg in enumerate(messages):
    #    for j,frm in enumerate(msg.frames):
    #        print( "DEBUG:: raw message[%d].frame[%d].raw=%s"
    #              % ( i,j, frm.raw ) )

    #for i,msg in enumerate(messages):
    #    print( "DEBUG:: message[%d]=%s" % (i, msg.data) )

    data = messages[0].frames[0].raw # operate on a single message/frame

    pid = bytearray(data[5:11],encoding='ascii');
    pid[0] -= 4 # remove acknowledgement flag
    pid = bytes(pid) # make hashable

    print("DEBUG:: decoding message %s, assuming pid=%s" % (data, pid))

    # lookup expression
    try:
        sensor = my_obd_sensors[pid]

    except KeyError:
        print("WARN:: failed to lookup pid=%s" % pid)
        return -1

    A = int(data[11:13],16) if "A" in sensor.eqn else 0
    B = int(data[13:15],16) if "B" in sensor.eqn else 0

    print("DEBUG:: fetching values A=%s, B=%s" % (A,B))

    # FIXME: create Unit object

    return eval( sensor.eqn )


# --- import the CSV file -----------------------------------------------------

my_obd_sensors = {}

with open('Bolt.csv', 'r') as f:

    for num,line in enumerate(f):

        if (num>0):
            sensor = obd_sensors( (line.strip()).split(",") )

            if "[" in sensor.eqn:
                print("WARN:: skipping compound expression '%s'" % sensor.eqn)
                continue

            if len(sensor.pid)==4:
                print("WARN:: skipping standard PID %s" % sensor.pid)
                continue

            if sensor.name=="":
                print("WARN:: skipping empty entry")
                continue

            if sensor.pid in my_obd_sensors:
                print("WARN:: skipping duplicate PID %s" % sensor.pid)
                continue

            my_obd_sensors[sensor.pid] = sensor


# ####### FIXME: add ELM_VOLTAGE ############
#
#elm_v = OBDCommand("ELM_VOLTAGE", "Voltage detected by OBD-II adapter",
#                   b"ATRV", 0, decode_pid, ECU.UNKNOWN, False)

# --- main event loop ---------------------------------------------------------

connection = obd.Async()

connection.unwatch_all()

#connection.watch(elm_v, callback=sensor.accumulate)

for pid,sensor in my_obd_sensors.items():

    print( "INFO:: adding PID=%s with command '%s', eqn='%s'" %
           (sensor.pid, sensor.cmd, sensor.eqn) )

    connection.supported_commands.add(sensor.cmd)
    connection.watch(sensor.cmd, callback=sensor.accumulate)

epoch = datetime.now()
start_time = time()

connection.start()

for it in range(120):
    print('.', end='', flush=True); sleep(0.5)
print()

connection.stop()

connection.unwatch_all()


# --- write data output -------------------------------------------------------

f_nm = epoch.strftime("sensor-readings-%Y.%m.%d-%H:%M:%S.h5")
f_id = File( f_nm, "w" )

for pid,sensor in my_obd_sensors.items():
    print("DEBUG:: saving time series '%s' with %d elements of type %s" % (sensor.nm, len(sensor.tms), type(sensor.tms[0])) )
    print("DEBUG:: values are %s" % sensor.tms)

    f_id.create_dataset( sensor.nm, data=sensor.tms, dtype='f8' )

f_id.close()

# -----------------------------------------------------------------------------
