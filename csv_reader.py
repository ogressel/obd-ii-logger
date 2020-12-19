#!/usr/bin/python
#
#

# --- utility functions

_hex = lambda val: 0 if val=="" else int( "0x%s" % val, 16 )
_float = lambda val: 0. if val=="" else float(val)
Signed = lambda val: (val & 0xffff) - (1<<16) if val >= (1<<15) else val

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

# --- callback function for decoding messages

def decode_pid(messages):

    """ generic decoder function for OBD-II messages """

    data = messages[0].data # only operate on a single message
    pid = (data[0]*256+data[1])*256+data[2] # assume 3-digit mode+PID

    # lookup expression
    sensor = my_obd_sensors[pid]

    A = data[3] if "A" in sensor.eqn else 0
    B = data[4] if "B" in sensor.eqn else 0

    # FIXME: create Unit object

    return eval( sensor.eqn )


# --- import the CSV file

my_obd_sensors = {}

with open('Bolt.csv', 'r') as f:

    for num,line in enumerate(f):

        if (num>0):
            sensor = obd_sensors( (line.strip()).split(",") )

            if not ( "[" in sensor.eqn     # skip compound sensors
                     or sensor.name=="" ): # skip empty sensors
                my_obd_sensors[sensor.pid] = sensor

#print(my_obd_sensors)

class myFakeMessage:
    data = [0x22,0x28,0xfb,0xab,0xcd]

msg=[]; msg.append(myFakeMessage)
print( decode_pid( msg ) )
