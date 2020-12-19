#!/usr/bin/python
#
#

from h5py import File
from time import time, sleep

import obd
from obd import OBD, OBDCommand
from obd.protocols import ECU


# --- utility functions -------------------------------------------------------

_hex = lambda val: 0 if val=="" else int( "0x%s" % val, 16 )
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
    cmd = 0         # query command object


    # --- constructor

    def __init__(self, value = []):

        self.name = value[0]
        self.nm = value[1].replace(' ', '_')

        self.pid = _hex(value[2])
        self.eqn = value[3]

        self.minv = _float(value[4])
        self.maxv = _float(value[5])

        self.unit = value[6]
        self.hdr = _hex(value[7])
        self.tms = []

        nbyte=0
        if "A" in self.eqn: nbyte=1
        if "B" in self.eqn: nbyte=2
        if "C" in self.eqn: nbyte=3
        if "D" in self.eqn: nbyte=4

        self.cmd = OBDCommand( self.nm,    # name
                               self.name,  # description
                           hex(self.pid),  # command
                               nbyte,      # number of return bytes to expect
                               decode_pid, # decoding function
                               ECU.ALL,    # (opt) ECU filter
                               True,       # (opt) "01" may be added for speed
                           hex(self.hdr) ) # (opt) custom PID header

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
    pid = (data[0]*256+data[1])*256+data[2] # assume 3-digit mode+PID

    # lookup expression
    sensor = my_obd_sensors[pid]

    A = data[3] if "A" in sensor.eqn else 0
    B = data[4] if "B" in sensor.eqn else 0
    C = data[5] if "C" in sensor.eqn else 0
    D = data[6] if "D" in sensor.eqn else 0

    # FIXME: create Unit object

    return eval( sensor.eqn )



# --- import the CSV file -----------------------------------------------------

my_obd_sensors = {}

with open('Bolt.csv', 'r') as f:

    for num,line in enumerate(f):

        if (num>0):
            sensor = obd_sensors( (line.strip()).split(",") )

            if not ( "[" in sensor.eqn     # skip compound sensors
                     or sensor.pid>>8==1   # skip standard PIDs
                     or sensor.name=="" ): # skip empty entries

                my_obd_sensors[sensor.pid] = sensor


# --- main event loop ---------------------------------------------------------

connection = obd.Async()

for pid,sensor in my_obd_sensors.items():
    connection.supported_commands.add(sensor.cmd)
    connection.watch(sensor.cmd, callback=sensor.accumulate, force=True)

start_time = time()

connection.start()
sleep(15)
connection.stop()

connection.unwatch_all()

# --- write data output -------------------------------------------------------

f_id = File( "sensors.h5", "w" )

for pid,sensor in my_obd_sensors.items():
    f_id.create_dataset( sensor.nm, data=sensor.tms )

f_id.close()

# -----------------------------------------------------------------------------
