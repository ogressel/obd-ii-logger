# OBD-II logger

A python script that reads Torque-Pro style sensor definitions from a CSV file and creates custom commands for the Python OBD-II interface library.

## Description

The script is intended to run on a Raspberry Pi and dump the sampled sensor values into an HDF5 data file, using individually labelled datasets for each PID time series.

## Getting Started

### Dependencies

* Python 3
* Non-standard modules: h5py, obd, timeloop

### Installing

* Download and configure the 'obd' Python module following these [instructions](https://python-obd.readthedocs.io/en/latest/#installation)
* Link your OBD-II dongle, e.g., following these [steps](https://fsjohnny.medium.com/connecting-your-bluetooth-obdii-adapter-or-other-serial-port-adapters-to-a-raspberry-pi-3-f2c9663dae73)
* Simply download the 'obd-ii-logger.py' script

### Executing program
* simply run from the command line, providing the filename for the CSV sensor-definitions as an argument

## Help

* Please let me know if you should encounter any issues.

## Version History

* 0.1
    * Initial Release

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

