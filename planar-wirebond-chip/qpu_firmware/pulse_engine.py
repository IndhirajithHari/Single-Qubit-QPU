#!/usr/bin/env python3
"""
pulse_engine.py
---------------
Author: Indhirajith
License: Open Source
Firmware Waveform Synthesis & Microcode Generator
Generates time-domain microwave pulses (DRAG, Gaussian, Flat-top Readout, Flux Z)
for the FPGA/AWG digital-to-analog converters driving the planar transmon chip.
"""

import numpy as np

class PulseEngine:
    def __init__(self, hal_config):
        self.config = hal_config
        self.xy_cfg = hal_config["hardware_channels"]["channel_0_xy"]
        self.flux_cfg = hal_config["hardware_channels"]["channel_1_flux"]
        self.ro_cfg = hal_config["hardware_channels"]["channel_2_readout"]

        self.dac_dt_xy = 1.0 / (self.xy_cfg["dac_sampling_rate_GSps"] * 1e9) # seconds
        self.dac_dt_ro = 1.0 / (self.ro_cfg["dac_sampling_rate_GSps"] * 1e9)

    def generate_drag_pulse(self, amplitude, duration_ns=20.0, sigma_ns=5.0, phase_rad=0.0, drag_beta=0.718):
        """
        Synthesizes a Derivative Removal by Adiabatic Gate (DRAG) microwave pulse.
        In-phase I(t) = Gaussian envelope.
        Quadrature Q(t) = - (beta / alpha) * dI/dt (eliminates leakage to |2>).
        """
        num_samples = int(np.round((duration_ns * 1e-9) / self.dac_dt_xy))
        t_ns = np.linspace(0, duration_ns, num_samples)
        t_center = duration_ns / 2.0

        # Gaussian envelope
        env_raw = np.exp(-0.5 * ((t_ns - t_center) / sigma_ns)**2)
        # Shift to zero at endpoints
        env_zero = np.exp(-0.5 * (t_center / sigma_ns)**2)
        envelope = amplitude * (env_raw - env_zero) / (1.0 - env_zero)

        # DRAG derivative: d(envelope)/dt
        # d/dt [exp(-(t-t0)^2 / 2s^2)] = - (t - t0) / s^2 * exp(...)
        d_env_dt = - amplitude * ((t_ns - t_center) / (sigma_ns**2)) * env_raw / (1.0 - env_zero) # 1/ns units
        drag_quadrature = - drag_beta * d_env_dt

        # Rotate by carrier phase (e.g. 0 for X gate, pi/2 for Y gate)
        I_env = envelope * np.cos(phase_rad) - drag_quadrature * np.sin(phase_rad)
        Q_env = envelope * np.sin(phase_rad) + drag_quadrature * np.cos(phase_rad)

        # Modulate onto Intermediate Frequency (IF = 50 MHz)
        f_if = self.xy_cfg["if_frequency_MHz"] * 1e6 # Hz
        t_sec = t_ns * 1e-9
        carrier_cos = np.cos(2.0 * np.pi * f_if * t_sec)
        carrier_sin = np.sin(2.0 * np.pi * f_if * t_sec)

        # Single Sideband (SSB) upconverted DAC waveform
        dac_waveform = I_env * carrier_cos - Q_env * carrier_sin

        return {
            "time_ns": t_ns,
            "I_envelope": I_env,
            "Q_envelope": Q_env,
            "dac_rf_waveform": dac_waveform,
            "duration_ns": duration_ns
        }

    def generate_flux_pulse(self, amplitude_v, duration_ns=40.0, risetime_ns=5.0):
        """Generates a fast Z flux pulse with smooth cosine-tapered edges."""
        num_samples = int(np.round((duration_ns * 1e-9) / self.dac_dt_xy))
        t_ns = np.linspace(0, duration_ns, num_samples)

        waveform = np.zeros(num_samples)
        for i, t in enumerate(t_ns):
            if t < risetime_ns:
                waveform[i] = amplitude_v * 0.5 * (1.0 - np.cos(np.pi * t / risetime_ns))
            elif t > (duration_ns - risetime_ns):
                t_fall = t - (duration_ns - risetime_ns)
                waveform[i] = amplitude_v * 0.5 * (1.0 + np.cos(np.pi * t_fall / risetime_ns))
            else:
                waveform[i] = amplitude_v

        return {
            "time_ns": t_ns,
            "voltage_waveform": waveform,
            "duration_ns": duration_ns
        }

    def generate_readout_pulse(self, amplitude_v=0.10, duration_ns=1000.0, edge_ns=20.0):
        """Generates flat-top 7.05 GHz probe burst for dispersive readout."""
        num_samples = int(np.round((duration_ns * 1e-9) / self.dac_dt_ro))
        t_ns = np.linspace(0, duration_ns, num_samples)

        envelope = np.ones(num_samples) * amplitude_v
        for i, t in enumerate(t_ns):
            if t < edge_ns:
                envelope[i] = amplitude_v * 0.5 * (1.0 - np.cos(np.pi * t / edge_ns))
            elif t > (duration_ns - edge_ns):
                t_fall = t - (duration_ns - edge_ns)
                envelope[i] = amplitude_v * 0.5 * (1.0 + np.cos(np.pi * t_fall / edge_ns))

        f_if = self.ro_cfg["if_frequency_MHz"] * 1e6
        t_sec = t_ns * 1e-9
        dac_rf = envelope * np.cos(2.0 * np.pi * f_if * t_sec)

        return {
            "time_ns": t_ns,
            "envelope": envelope,
            "dac_rf_waveform": dac_rf,
            "duration_ns": duration_ns
        }

    def demodulate_readout_iq(self, adc_signal, time_ns):
        """Demodulates ADC voltage trace into integrated I and Q quadrature components."""
        f_if = self.ro_cfg["if_frequency_MHz"] * 1e6
        t_sec = time_ns * 1e-9
        cos_ref = np.cos(2.0 * np.pi * f_if * t_sec)
        sin_ref = np.sin(2.0 * np.pi * f_if * t_sec)

        # Digital downconversion and integration
        i_component = np.mean(adc_signal * cos_ref) * 2.0
        q_component = np.mean(adc_signal * sin_ref) * 2.0
        return i_component, q_component
