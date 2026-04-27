import tkinter as tk
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import pyvisa
import csv
import os
import time
from threading import Thread
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from pyvisa.errors import VisaIOError

# Initialize connection to SMU
rm = pyvisa.ResourceManager()
try:
    smu = rm.open_resource('GPIB0::18::INSTR')
    connection_status = "Connected"
except pyvisa.VisaIOError:
    smu = None
    connection_status = "Not Connected"

class PulseMeasurementApp:
    def __init__(self, root):
        # Set up ttkbootstrap style with a theme
        style = ttkb.Style(theme="cosmo")
        
        root.title("Keithley 2461 Measurement Interface")
        container = ttkb.Frame(root)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        scrollbar = ttkb.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttkb.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


        # Settings Frame
        settings_frame = ttkb.LabelFrame(scrollable_frame, text="Settings", bootstyle=INFO)
        settings_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nw")

        self.connection_label = ttkb.Label(settings_frame, text=f"Connection Status: {connection_status}")
        self.connection_label.grid(row=0, column=0, columnspan=2, pady=5, sticky="w")

        self.remote_enabled = False
        self.remote_button = ttkb.Button(settings_frame, text="Enable Remote", command=self.toggle_remote, bootstyle=PRIMARY)
        self.remote_button.grid(row=1, column=0, columnspan=2, pady=5)

        ttkb.Label(settings_frame, text="Source Mode:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.source_mode = tk.StringVar(value="Voltage")
        source_mode_menu = ttkb.Combobox(settings_frame, textvariable=self.source_mode, state="readonly", bootstyle=SECONDARY)
        source_mode_menu['values'] = ("Voltage", "Current")
        source_mode_menu.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        source_mode_menu.bind("<<ComboboxSelected>>", self.update_units)

        ttkb.Label(settings_frame, text="Measure Mode:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.measure_mode = tk.StringVar(value="Voltage")
        measure_mode_menu = ttkb.Combobox(settings_frame, textvariable=self.measure_mode, state="readonly", bootstyle=SECONDARY)
        measure_mode_menu['values'] = ("Voltage", "Current")
        measure_mode_menu.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        ttkb.Label(settings_frame, text="Wire Mode:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.wire_mode = tk.StringVar(value="2-Wire")
        wire_mode_menu = ttkb.Combobox(settings_frame, textvariable=self.wire_mode, state="readonly", bootstyle=SECONDARY)
        wire_mode_menu['values'] = ("2-Wire", "4-Wire")
        wire_mode_menu.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        ttkb.Label(settings_frame, text="Compliance:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.compliance_entry = ttkb.Entry(settings_frame)
        self.compliance_entry.grid(row=5, column=1, padx=5, pady=5, sticky="w")
        self.compliance_unit_label = ttkb.Label(settings_frame, text="A")  
        self.compliance_unit_label.grid(row=5, column=2, padx=5, pady=5)

        ttkb.Label(settings_frame, text="Range Mode:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.range_mode = tk.StringVar(value="Auto")
        range_menu = ttkb.Combobox(settings_frame, textvariable=self.range_mode, state="readonly", bootstyle=SECONDARY)
        range_menu['values'] = ("Auto", "Manual")
        range_menu.grid(row=6, column=1, padx=5, pady=5, sticky="w")

        apply_button = ttkb.Button(settings_frame, text="Apply Settings", command=self.apply_settings, bootstyle=SUCCESS)
        apply_button.grid(row=7, column=0, columnspan=2, pady=10)

        # Pulse Measurement Frame
        pulse_frame = ttkb.LabelFrame(scrollable_frame, text="Pulse Measurement Protocol", bootstyle=INFO)
        pulse_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nw")

        ttkb.Label(pulse_frame, text="Initial Pulse Amplitude (A/V):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.initial_pulse_amplitude = ttkb.Entry(pulse_frame)
        self.initial_pulse_amplitude.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttkb.Label(pulse_frame, text="Amplitude Increment (A/V):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.amplitude_increment = ttkb.Entry(pulse_frame)
        self.amplitude_increment.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttkb.Label(pulse_frame, text="Pulse Duration (s):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.pulse_duration = ttkb.Entry(pulse_frame)
        self.pulse_duration.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttkb.Label(pulse_frame, text="Probe Pulse Amplitude (A/V):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.probe_pulse_amplitude = ttkb.Entry(pulse_frame)
        self.probe_pulse_amplitude.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        ttkb.Label(pulse_frame, text="Probe Time (s):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.probe_time = ttkb.Entry(pulse_frame)
        self.probe_time.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        ttkb.Label(pulse_frame, text="Rmin Stop Criterion (Ohms):").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.rmin_stop_criterion = ttkb.Entry(pulse_frame)
        self.rmin_stop_criterion.grid(row=5, column=1, padx=5, pady=5, sticky="w")

        ttkb.Label(pulse_frame, text="Pulse Stop Criterion (A/V):").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.pulse_stop_criterion = ttkb.Entry(pulse_frame)
        self.pulse_stop_criterion.grid(row=6, column=1, padx=5, pady=5, sticky="w")

        select_folder_button = ttkb.Button(scrollable_frame, text="Select Folder", command=self.select_directory, bootstyle=SECONDARY)
        select_folder_button.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.folder_path_label = ttkb.Label(scrollable_frame, text="No folder selected", foreground="blue")
        self.folder_path_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=10)

        self.start_button = ttkb.Button(pulse_frame, text="Start Pulse Measurement", command=self.start_pulse_measurement, bootstyle=SUCCESS)
        self.start_button.grid(row=7, column=0, padx=5, pady=10)
        self.stop_button = ttkb.Button(pulse_frame, text="Stop Pulse Measurement", command=self.stop_pulse_measurement, state="disabled", bootstyle=DANGER)
        self.stop_button.grid(row=7, column=1, padx=5, pady=10)

        # New Resistance vs Time Measurement Frame
        resistance_frame = ttkb.LabelFrame(scrollable_frame, text="Resistance vs Time Measurement", bootstyle=INFO)
        resistance_frame.grid(row=4, column=0, padx=10, pady=10, sticky="nw")

        ttkb.Label(resistance_frame, text="Source (A/V):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.resistance_source = ttkb.Entry(resistance_frame)
        self.resistance_source.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttkb.Label(resistance_frame, text="Total Time (s):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.resistance_time = ttkb.Entry(resistance_frame)
        self.resistance_time.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttkb.Label(resistance_frame, text="Data Step (s):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.resistance_step = ttkb.Entry(resistance_frame)
        self.resistance_step.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        self.start_resistance_button = ttkb.Button(
            resistance_frame, text="Start Resistance Measurement", command=self.start_resistance_measurement, bootstyle=SUCCESS
        )
        self.start_resistance_button.grid(row=3, column=0, padx=5, pady=10)
        self.stop_resistance_button = ttkb.Button(
            resistance_frame, text="Stop Resistance Measurement", command=self.stop_resistance_measurement, state="disabled", bootstyle=DANGER
        )
        self.stop_resistance_button.grid(row=3, column=1, padx=5, pady=10)

        # Initialize Data Structures for Plotting
        self.rmax_values = []
        self.rmin_values = []
        self.pulse_amplitudes = []
        self.protocol_times = []
        self.annotations = []
        self.protocol_values = []
        self.protocol_colors = []  # Color coding for pulse and probe
        
        # Unified plot setup for Rmax/Rmin and Protocol in a single figure
        self.fig, (self.protocol_ax, self.ax1, self.ax2) = plt.subplots(3, 1, figsize=(10, 15))
        
        # Initialize Resistance vs Time Plot for Live Update
        self.fig_r, self.ax_r = plt.subplots(figsize=(8, 4))
        self.ax_r.set_title("Resistance vs Time")
        self.ax_r.set_xlabel("Time (s)")
        self.ax_r.set_ylabel("Resistance (Ohms)")
        self.resistance_times = []
        self.resistance_values = []
        self.resistance_canvas = FigureCanvasTkAgg(self.fig_r, master=scrollable_frame)
        self.resistance_canvas.get_tk_widget().grid(row=0, column=1, rowspan=5, padx=10, pady=10, sticky="n")  # Place on right side

        self.is_measuring = False
        self.csv_writer = None
        self.data_folder = None
        self.is_measuring_resistance = False
        self.resistance_csv_writer = None
        self.resistance_csv_file = None  # Track the file object

    # Functions for Pulse Measurement (Unchanged from original)

    def toggle_remote(self):
        if not smu:
            messagebox.showerror("Error", "Instrument not connected")
            return
        if self.remote_enabled:
            smu.control_ren(6)  
            self.remote_button.config(text="Enable Remote")
            self.remote_enabled = False
        else:
            smu.query("*IDN?")  
            self.remote_button.config(text="Disable Remote")
            self.remote_enabled = True

    def update_units(self, event):
        if self.source_mode.get() == "Voltage":
            self.compliance_unit_label.config(text="A")
        elif self.source_mode.get() == "Current":
            self.compliance_unit_label.config(text="V")

    def apply_settings(self):
        if not smu:
            messagebox.showerror("Error", "Instrument not connected")
            return

        try:
            source_mode = self.source_mode.get()
            measure_mode = self.measure_mode.get()
            wire_mode = self.wire_mode.get()
            compliance_text = self.compliance_entry.get()
            
            if not compliance_text:
                messagebox.showwarning("Compliance Missing", "Please enter a compliance value.")
                return
            
            compliance = float(compliance_text)
            range_mode = self.range_mode.get()

            if source_mode == "Voltage":
                smu.write(":SOUR:FUNC VOLT")
                smu.write(f":SOUR:VOLT:ILIM {compliance}")
            elif source_mode == "Current":
                smu.write(":SOUR:FUNC CURR")
                smu.write(f":SOUR:CURR:VLIM {compliance}")

            smu.write(":SYST:RSEN ON" if wire_mode == "4-Wire" else ":SYST:RSEN OFF")

            if range_mode == "Auto":
                smu.write(":SENS:VOLT:RANG:AUTO ON" if measure_mode == "Voltage" else ":SENS:CURR:RANG:AUTO ON")
            else:
                smu.write(":SENS:VOLT:RANG:AUTO OFF" if measure_mode == "Voltage" else ":SENS:CURR:RANG:AUTO OFF")

            messagebox.showinfo("Settings Applied", "Settings applied successfully to the SMU.")
        
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input for compliance: {e}")

    def select_directory(self):
        selected_folder = filedialog.askdirectory()
        if selected_folder:
            self.data_folder = selected_folder
            self.folder_path_label.config(text=selected_folder)

    def start_pulse_measurement(self):
        if not self.data_folder:
            messagebox.showwarning("Folder Selection", "Please select a folder to save data files.")
            return

        try:
            self.prepare_summary_csv()
            self.is_measuring = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.prepare_csv_file()
            self.protocol_times.clear()
            self.protocol_values.clear()
            self.protocol_colors.clear()
            pulse_thread = Thread(target=self.pulse_measurement_protocol)
            pulse_thread.start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start pulse measurement: {e}")

    def pulse_measurement_protocol(self):
        try:
            # Record the experiment start time for relative time calculations
            experiment_start_time = time.time()
            initial_amplitude = float(self.initial_pulse_amplitude.get())
            increment = float(self.amplitude_increment.get())
            duration = float(self.pulse_duration.get())
            probe_amplitude = float(self.probe_pulse_amplitude.get())
            probe_time = float(self.probe_time.get())
            stop_criterion = float(self.rmin_stop_criterion.get())
            pulse_stop_criterion = float(self.pulse_stop_criterion.get())

            amplitude = initial_amplitude
            time_elapsed = 0  # Track relative time

            pulse_number = 0  # Keep track of the pulse number

            while self.is_measuring:
                pulse_number += 1  # Increment pulse number

                # Apply Pulse
                smu.write(f":SOUR:{self.source_mode.get()} {amplitude}")
                smu.write(":OUTP ON")
                
                # Continuous sampling during the pulse
                voltage_samples = []
                current_samples = []
                timestamps = []
                relative_times = []
                file_path = os.path.join(self.data_folder, f"detailed_pulse_data_{pulse_number}.csv")

                with open(file_path, "w", newline="") as detailed_csv:
                    detailed_writer = csv.writer(detailed_csv)
                    detailed_writer.writerow(["Relative Time (s)", "Actual Time (HH:MM:SS)", "Voltage (V)", "Current (A)"])

                    time_start = time.time()
                    time_end = time_start + duration

                    while time.time() < time_end:
                        current_time = time.time()
                        relative_time = current_time - experiment_start_time
                        actual_time = datetime.fromtimestamp(current_time).strftime("%H:%M:%S")
                        voltage = float(smu.query(":MEAS:VOLT?"))
                        current = float(smu.query(":MEAS:CURR?"))

                        # Append to lists
                        relative_times.append(relative_time)
                        timestamps.append(actual_time)
                        voltage_samples.append(voltage)
                        current_samples.append(current)

                        # Write to CSV
                        detailed_writer.writerow([relative_time, actual_time, voltage, current])

                        time.sleep(0.01)  # Sampling interval (10 ms)
           

                # Compute average values for plotting
                avg_voltage = sum(voltage_samples) / len(voltage_samples)
                avg_current = sum(current_samples) / len(current_samples)

                # Record averaged values for live protocol plot
                actual_value = avg_current if self.source_mode.get() == "Current" else avg_voltage
                self.protocol_times.append(time_elapsed)
                self.protocol_values.append(actual_value * 1e3)  # Convert to mA/mV for plot
                self.protocol_colors.append("red")  # Pulse in red
                time_elapsed += duration

                # Add an optional annotation for the start of the pulse
                #self.annotations.append((time_elapsed, avg_voltage * 1e3, f"Start: {timestamps[0]}"))

            
                # Calculate Rmax
                rmax = avg_voltage / avg_current if avg_current != 0 else float('inf')
                self.rmax_values.append(rmax)
                self.pulse_amplitudes.append(amplitude)

                # Apply Probe Pulse (+ and -) and measure Rmin
                rmin_values_pos = []
                rmin_values_neg = []

                half_probe_time = probe_time / 2
                smu.write(f":SOUR:{self.source_mode.get()} {probe_amplitude}")
                smu.write(":OUTP ON")
                time_end = time.time() + half_probe_time
                while time.time() < time_end:
                    voltage = float(smu.query(":MEAS:VOLT?"))
                    current = float(smu.query(":MEAS:CURR?"))
                    rmin_values_pos.append(voltage / current if current != 0 else float('inf'))
                    self.protocol_times.append(time_elapsed)
                    actual_value = current if self.source_mode.get() == "Current" else voltage
                    self.protocol_values.append(actual_value * 1e3)  # Positive probe in mA/mV
                    self.protocol_colors.append("blue")  # Probe in blue
                    time_elapsed += 1

                smu.write(f":SOUR:{self.source_mode.get()} {-probe_amplitude}")
                time_end = time.time() + half_probe_time
                while time.time() < time_end:
                    voltage = float(smu.query(":MEAS:VOLT?"))
                    current = float(smu.query(":MEAS:CURR?"))
                    rmin_values_neg.append(voltage / current if current != 0 else float('inf'))
                    self.protocol_times.append(time_elapsed)
                    actual_value = current if self.source_mode.get() == "Current" else voltage
                    self.protocol_values.append(actual_value * 1e3)  # Negative probe in mA/mV
                    self.protocol_colors.append("blue")  # Probe in blue
                    time_elapsed += 1

                rmin = (sum(rmin_values_pos) + sum(rmin_values_neg)) / (len(rmin_values_pos) + len(rmin_values_neg))
                self.rmin_values.append(rmin)

                self.save_pulse_data(amplitude, rmax, rmin, avg_current, avg_voltage)

                # Save summary data
                with open(self.summary_file_path, "a", newline="") as summary_csv:
                    summary_writer = csv.writer(summary_csv)
                    summary_writer.writerow([pulse_number, amplitude, avg_voltage, avg_current, rmax, rmin])
                
                root.after(0, self.update_combined_plot)

                if rmin >= stop_criterion or amplitude >= pulse_stop_criterion:
                    break

                amplitude += increment
                smu.write(":OUTP OFF")
                time.sleep(0.1)

            self.stop_pulse_measurement()

        except VisaIOError as e:
            messagebox.showerror("Error", f"Measurement error: {e}")

    def update_combined_plot(self):
        # Update Protocol plot
        self.protocol_ax.clear()
        self.protocol_ax.plot(self.protocol_times, self.protocol_values, color="black")

        # Add annotations for key events (e.g., pulse start times)
        for annotation in self.annotations:
            time_point, value, label = annotation
            self.protocol_ax.annotate(label, xy=(time_point, value),
                                      xytext=(time_point + 5, value + 10),
                                      arrowprops=dict(facecolor='black', arrowstyle="->"))

        
        # Add labels and titles
        y_label_unit = "mA" if self.source_mode.get() == "Current" else "mV"
        self.protocol_ax.set_xlabel("Elapsed Time (s)")
        self.protocol_ax.set_ylabel(f"Measured Value ({y_label_unit})")
        self.protocol_ax.set_title("Live Pulse Protocol")
        
        # Update Rmax and Rmin plots
        unit = self.determine_amplitude_unit()
        self.ax1.clear()
        self.ax1.plot(self.pulse_amplitudes, self.rmax_values, 'o', color='red', label="Rmax")
        self.ax1.set_title("Rmax vs Pulse Amplitude")
        self.ax1.set_xlabel(f"Amplitude ({unit})")
        self.ax1.set_ylabel("Rmax (Ohms)")
        self.ax1.legend()

        self.ax2.clear()
        self.ax2.plot(self.pulse_amplitudes, self.rmin_values, 'o', color='blue', label="Rmin")
        self.ax2.set_title("Rmin vs Pulse Amplitude")
        self.ax2.set_xlabel(f"Amplitude ({unit})")
        self.ax2.set_ylabel("Rmin (Ohms)")
        self.ax2.legend()

        self.fig.canvas.draw()
        plt.pause(0.01)

    def save_protocol_plot(self):
        file_path = os.path.join(self.data_folder, "protocol_plot.png")
        self.fig.savefig(file_path)
        messagebox.showinfo("Protocol Plot Saved", f"Protocol plot saved as {file_path}")

    def stop_pulse_measurement(self):
        self.is_measuring = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        smu.write(":OUTP OFF")
        if self.csv_writer:
            self.csv_file.close()
        self.save_protocol_plot()

    def prepare_csv_file(self):
        counter = 1
        file_path = f"{self.data_folder}/pulse_data_{counter}.csv"
        while os.path.exists(file_path):
            counter += 1
            file_path = f"{self.data_folder}/pulse_data_{counter}.csv"
        self.csv_file = open(file_path, "w", newline="")
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["Pls_number", "Amplitude", "Current", "Voltage", "Rmax", "Rmin"])

    def prepare_summary_csv(self):
        # File path for summary CSV
        self.summary_file_path = os.path.join(self.data_folder, "summary_data.csv")
    
        # Check if file exists
        file_exists = os.path.isfile(self.summary_file_path)
    
        # Open the file and write the header if it doesn't exist
        with open(self.summary_file_path, "a", newline="") as csvfile:
             csv_writer = csv.writer(csvfile)
             if not file_exists:
               csv_writer.writerow(["Pulse Number", "Pulse Amplitude", "Average Voltage (V)", "Average Current (A)", "Rmax (Ohms)", "Rmin (Ohms)"])
    

    def determine_amplitude_unit(self):
        unit = "A" if self.source_mode.get() == "Current" else "V"
        if max(self.pulse_amplitudes) < 1e-3:
            return f"µ{unit}"
        elif max(self.pulse_amplitudes) < 1:
            return f"m{unit}"
        elif max(self.pulse_amplitudes) > 1e3:
            return f"k{unit}"
        return unit

    def save_pulse_data(self, amplitude, rmax, rmin, current, voltage):
        pls_number = len(self.pulse_amplitudes)
        self.csv_writer.writerow([pls_number, amplitude, current, voltage, rmax, rmin])

    # Resistance Measurement Functions
    def start_resistance_measurement(self):
        if not self.data_folder:
            messagebox.showwarning("Folder Selection", "Please select a folder to save data files.")
            return

        try:
            # Clear previous measurement data
            self.resistance_times.clear()
            self.resistance_values.clear()

            # Update the plot to show an empty plot before starting the new measurement
            self.ax_r.clear()
            self.ax_r.set_title("Resistance vs Time")
            self.ax_r.set_title("Resistance vs Time")
            self.ax_r.set_xlabel("Time (s)")
            self.ax_r.set_ylabel("Resistance (Ohms)")
            self.resistance_canvas.draw()
                        
            source_amplitude = float(self.resistance_source.get())
            duration = float(self.resistance_time.get())
            data_step = float(self.resistance_step.get())

            self.prepare_resistance_csv_file()
            self.is_measuring_resistance = True
            self.start_resistance_button.config(state="disabled")
            self.stop_resistance_button.config(state="normal")

            resistance_thread = Thread(
                target=self.resistance_measurement_protocol, args=(source_amplitude, duration, data_step)
            )
            resistance_thread.start()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numerical values for source, time, and data step.")

    def stop_resistance_measurement(self):
        self.is_measuring_resistance = False
        self.start_resistance_button.config(state="normal")
        self.stop_resistance_button.config(state="disabled")
        if self.resistance_csv_file:
            self.resistance_csv_file.close()
            self.resistance_csv_file = None  # Reset the file reference

    def resistance_measurement_protocol(self, source_amplitude, duration, data_step):
        smu.write(f":SOUR:{self.source_mode.get()} {source_amplitude}")
        smu.write(":OUTP ON")
        start_time = time.time()
        elapsed = 0

        while self.is_measuring_resistance and elapsed <= duration:
            try:
                voltage = float(smu.query(":MEAS:VOLT?"))
                current = float(smu.query(":MEAS:CURR?"))
                resistance = voltage / current if current != 0 else float('inf')
                elapsed = time.time() - start_time

                # Save data and update live plot
                if self.resistance_csv_writer:
                    self.save_resistance_data(elapsed, resistance)
                self.update_resistance_plot(elapsed, resistance)

                time.sleep(data_step)
            except VisaIOError as e:
                messagebox.showerror("Error", f"Measurement error: {e}")
                break

        smu.write(":OUTP OFF")
        self.stop_resistance_measurement()

    def update_resistance_plot(self, time_stamp, resistance):
        self.resistance_times.append(time_stamp)
        self.resistance_values.append(resistance)
        
        # Update the plot with new data
        self.ax_r.clear()
        self.ax_r.plot(self.resistance_times, self.resistance_values, color="green")
        self.ax_r.set_title("Resistance vs Time")
        self.ax_r.set_xlabel("Time (s)")
        self.ax_r.set_ylabel("Resistance (Ohms)")
        self.resistance_canvas.draw()

    def prepare_resistance_csv_file(self):
        counter = 1
        file_path = os.path.join(self.data_folder, f"R(t)_{counter}.csv")
        while os.path.exists(file_path):
            counter += 1
            file_path = os.path.join(self.data_folder, f"R(t)_{counter}.csv")
        self.resistance_csv_file = open(file_path, "w", newline="")
        self.resistance_csv_writer = csv.writer(self.resistance_csv_file)
        self.resistance_csv_writer.writerow(["Time (s)", "Resistance (Ohms)"])

    def save_resistance_data(self, time_stamp, resistance):
        if self.resistance_csv_writer:
            self.resistance_csv_writer.writerow([time_stamp, resistance])

if __name__ == "__main__":
    root = ttkb.Window()  # Use ttkbootstrap Window to apply theme automatically
    app = PulseMeasurementApp(root)
    root.mainloop()

    if smu:
        smu.close()
