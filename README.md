# Electromigration Control System

## Overview

This repository contains a Python-based graphical interface for automated electromigration experiments using a Keithley Source Measure Unit (SMU).

The software enables full control of pulse-based electromigration protocols, real-time acquisition of electrical measurements, and structured data logging. It is designed for experimental workflows involving controlled current or voltage stressing in microstructured devices.

## Key Features

* Graphical user interface (Tkinter + ttkbootstrap)
* Direct communication with Keithley SMU via PyVISA
* Automated pulse protocol:

  * Incremental pulse amplitude
  * Configurable pulse duration
  * Probe pulses for resistance measurement
* Real-time measurement of:

  * Voltage
  * Current
  * Resistance
* Extraction of:

  * Rmax (during pulse)
  * Rmin (probe measurement)
* Stop criteria:

  * Resistance threshold
  * Maximum pulse amplitude
* Live visualization:

  * Pulse protocol vs time
  * Rmax vs amplitude
  * Rmin vs amplitude
* Resistance vs time measurement mode
* Automatic CSV data logging:

  * Detailed pulse data
  * Summary data
  * Resistance vs time

## Experimental Protocol

The electromigration protocol follows a pulse-based approach:

1. Apply a pulse with increasing amplitude
2. Measure voltage and current continuously
3. Compute Rmax during the pulse
4. Apply probe pulses (+ and -)
5. Compute Rmin from probe measurements
6. Repeat until stop criteria are reached

This enables controlled electromigration and monitoring of irreversible changes in the device.

## Hardware Requirements

* Keithley Source Measure Unit (e.g., 2461)
* GPIB or USB interface
* VISA-compatible backend (NI-VISA recommended)

## Software Requirements

* Python 3.x
* numpy
* pandas
* matplotlib
* pyvisa
* ttkbootstrap

Install dependencies:

pip install -r requirements.txt

## Usage

Run the application:

python em_control_gui.py

### Steps:

1. Connect the SMU
2. Enable remote control
3. Configure:

   * Source mode (Voltage / Current)
   * Measurement mode
   * Compliance
   * Wire configuration (2-wire / 4-wire)
4. Define pulse protocol:

   * Initial amplitude
   * Increment
   * Pulse duration
   * Probe amplitude
   * Probe time
   * Stop criteria
5. Select data folder
6. Start measurement

## Output Data

The system automatically saves:

* Pulse-by-pulse data:

  * Amplitude
  * Voltage
  * Current
  * Rmax
  * Rmin
* Detailed time-resolved pulse data
* Resistance vs time datasets
* Summary CSV file

## Visualization

The interface provides:

* Live pulse protocol tracking
* Rmax vs pulse amplitude
* Rmin vs pulse amplitude
* Resistance vs time plot

## Interface Preview

(Add screenshot here after uploading)

![GUI](figures/gui_overview.png)

## Notes

* Ensure correct VISA address for your instrument
* Default address used in code:

GPIB0::18::INSTR

* Modify if needed for your setup
* Use caution when applying high current or voltage to devices

## Author

Elijah
Experimental physicist specializing in electromigration, thin-film systems, and automated measurement platforms.
