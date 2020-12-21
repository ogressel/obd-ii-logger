#!/usr/bin/python
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
Signed = lambda val: (val & 0xffff) - (1<<16) if val >= (1<<15) else val

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

        self.pid = bytes(value[2],"ascii")
        self.eqn = value[3]

        self.minv = _float(value[4])
        self.maxv = _float(value[5])

        self.unit = value[6]
        self.hdr = bytes(value[7],"ascii")
        self.tms = []

        self.nbt=0
        if "A" in self.eqn: self.nbt=1
        if "B" in self.eqn: self.nbt=2
        if "C" in self.eqn: self.nbt=3
        if "D" in self.eqn: self.nbt=4

        self.cmd = OBDCommand( self.nm,    # name
                               self.name,  # description
                               self.pid,   # command
                               self.nbt,   # number of return bytes to expect
                               decode_pid, # decoding function
                               ECU.ALL,    # (opt) ECU filter
                               True,       # (opt) "01" may be added for speed
                               self.hdr )  # (opt) custom PID header

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

    data = messages[0].data # only operate on a single message

    pid = ib = 0
    nbytes_msg = len(data)

    print("DEBUG:: decoding message '%s' of length %d" % (data, nbytes_msg))

    if(nbytes_msg>0):
        pid = data[0]; ib+=1

    if(nbytes_msg>1):
        pid = pid*256 + data[ib]; ib+=1

    if(nbytes_msg>2):
        pid = pid*256 + data[2]; ib+=1

    print("DEBUG:: assuming pid='%s'" % hex(pid))

    # lookup expression
    try:
        sensor = my_obd_sensors[pid]

    except KeyError:
        print("WARN:: failed to lookup pid='%s'" % hex(pid))
        return -1

    A = data[ib+0] if "A" in sensor.eqn and ib+0 < nbytes_msg else 0
    B = data[ib+1] if "B" in sensor.eqn and ib+1 < nbytes_msg else 0
    C = data[ib+2] if "C" in sensor.eqn and ib+2 < nbytes_msg else 0
    D = data[ib+3] if "D" in sensor.eqn and ib+3 < nbytes_msg else 0

    # FIXME: create Unit object

    return eval( sensor.eqn )


# --- import the CSV file -----------------------------------------------------

my_obd_sensors = {}

with open('Bolt.csv', 'r') as f:

    for num,line in enumerate(f):

        if (num>0):
            sensor = obd_sensors( (line.strip()).split(",") )

            if not ( "[" in sensor.eqn     # skip compound sensors
                     or len(sensor.pid)==4 # skip standard PIDs (for now)
                     or sensor.name=="" ): # skip empty entries

                my_obd_sensors[sensor.pid] = sensor


# --- main event loop ---------------------------------------------------------

connection = obd.Async()

connection.unwatch_all()

for pid,sensor in my_obd_sensors.items():

    print( "INFO:: adding PID=%s with command '%s', eqn='%s'" %
           (sensor.pid, sensor.cmd, sensor.eqn) )

    connection.supported_commands.add(sensor.cmd)
    connection.watch(sensor.cmd, callback=sensor.accumulate)

epoch = datetime.now()
start_time = time()

connection.start()

for it in range(30):
    print('.'); sleep(0.5); #, end='', flush=True); sleep(0.5)
print()

connection.stop()

connection.unwatch_all()

# --- write data output -------------------------------------------------------

f_nm = epoch.strftime("sensor-readings-%Y.%m.%d-%H:%M:%S.h5")
f_id = File( f_nm, "w" )

for pid,sensor in my_obd_sensors.items():
    f_id.create_dataset( sensor.nm, data=sensor.tms )

f_id.close()

# -----------------------------------------------------------------------------
