#!/usr/bin/python3
#
#

import sys

from h5py import File

from time import time, sleep
from datetime import datetime

import numpy as np

import obd
from obd import OBD, OBDCommand
from obd.protocols import ECU

from timeloop import Timeloop
from datetime import timedelta

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
    dset = 0        # h5py dataset

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
        self.dset = 0

        self.nbt=0
        if "A" in self.eqn: self.nbt=1
        if "B" in self.eqn: self.nbt=2
        if "C" in self.eqn: self.nbt=3
        if "D" in self.eqn: self.nbt=4

        self.cmd = OBDCommand( self.nm,     # name
                               self.name,   # description
                               self.pid,    # command
                               0,           # number of return bytes to expect
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

    # --- callback method for data accumulation

    def accumulate(self,result):

        self.tms.append( [ time()-start_time, result.value ] )


# --- routine for appending HDF5 datasets -------------------------------------

tloop = Timeloop()

@tloop.job(interval=timedelta(seconds=60))
def append_hdf5_file_every_60s():

    for pid,sensor in my_obd_sensors.items():

        if(len(sensor.tms)==0):
            print("DEBUG:: skipping empty time series '%s'" % sensor.nm)
            continue

        else:
            print("DEBUG:: saving time series '%s' with %d elements"
                  % (sensor.nm, len(sensor.tms)))
            print("DEBUG:: values are %s" % sensor.tms)

        # --- write data to HDF5 file

        if not any( val==None for (_,val) in sensor.tms ):

            tms_data = np.asarray(sensor.tms)

            if not sensor.nm in f_id.keys():  # create dataset

                sensor.dset = f_id.create_dataset( sensor.nm,
                                                   data=tms_data,
                                                   dtype='f8',
                                                   maxshape=(None,2) )

            else:                             # append to dataset

                new = len(sensor.tms)
                sensor.dset.resize(sensor.dset.shape[0]+new, axis=0)
                sensor.dset[-new:] = tms_data

            # --- flush file and purge data

            print("DEBUG:: dataset shape is ", sensor.dset.shape)
            f_id.flush()
            sensor.tms = []


# --- callback function for decoding messages ---------------------------------

def decode_pid(messages):

    """ generic decoder function for OBD-II messages """

    data = messages[0].frames[0].raw # operate on a single message/frame

    pid = bytearray(data[5:11],encoding='ascii');
    pid[0] -= 4       # remove acknowledgement flag
    pid = bytes(pid)  # make hashable

    print("DEBUG:: decoding message '%s' of type %s, assuming pid=%s"
          % (data,type(data), pid))

    # lookup expression
    try:
        sensor = my_obd_sensors[pid]
        print("DEBUG:: found PID %s ('%s') with eqn='%s'"
              % (sensor.pid,sensor.nm,sensor.eqn))

    except KeyError:
        print("WARN:: failed to lookup pid=%s" % pid)
        return -1

    A = int(data[11:13],16) if "A" in sensor.eqn else 0
    B = int(data[13:15],16) if "B" in sensor.eqn else 0

    print("DEBUG:: fetching values A=%s, B=%s" % (A,B))

    result = float( eval( sensor.eqn ) )
    print("DEBUG:: evaluated %s = %g" % (sensor.eqn, result))

    return result


# --- import the CSV file -----------------------------------------------------

if( len(sys.argv)!=2 ):
    print("INFO:: usage is '%s <pid-file.csv>'" % sys.argv[0] )
    sys.exit(-1)

my_obd_sensors = {}

with open(sys.argv[1], 'r') as f:

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


# --- open HDF5 file ----------------------------------------------------------

f_nm = (datetime.now()).strftime("sensor-readings-%Y.%m.%d-%H:%M:%S.h5")
f_id = File( f_nm, "a" )


# --- main event loop ---------------------------------------------------------

start_time = time()
connection = obd.Async()

connection.unwatch_all()

for pid,sensor in my_obd_sensors.items():

    print( "INFO:: adding PID=%s with command '%s', eqn='%s'" %
           (sensor.pid, sensor.cmd, sensor.eqn) )

    connection.supported_commands.add(sensor.cmd)
    connection.watch(sensor.cmd, callback=sensor.accumulate)

tloop.start(block=False) # append HDF5 data

connection.start()

while True:
    print('.', end='', flush=True); sleep(0.5)

print()

connection.stop()

connection.unwatch_all()


# --- close the HDF5 data file ------------------------------------------------

f_id.close()

# -----------------------------------------------------------------------------
