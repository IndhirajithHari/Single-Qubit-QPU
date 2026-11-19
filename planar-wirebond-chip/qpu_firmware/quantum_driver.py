#!/usr/bin/env python3
"""
quantum_driver.py
-----------------
Author: Indhirajith
License: Open Source
QPU Hardware Driver & Execution Engine
Simulates the quantum state trajectory of the transmon qubit under physical microwave
pulse excitation, including Rabi rotations, Ramsey precession, and dispersive IQ readout.
"""

import numpy as np

class QPUDriver:
    def __init__(self, pulse_engine):
        self.pe = pulse_engine
        self.calibrated_pi_amp = 0.450 # Volts DAC for 180-deg flip
        self.qubit_freq_GHz = 5.000
        self.readout_freq_GHz = 7.050
        self.chi_shift_MHz = -1.25 # Dispersive shift
        self.T1_us = 95.0          # Qubit relaxation lifetime
        self.T2_star_us = 78.0     # Qubit dephasing lifetime

    def execute_circuit(self, operations):
        """
        Executes a sequence of quantum gate operations.
        operations: list of tuples like [('X',), ('MEASURE',)] or [('PULSE', amp, phase, duration)]
        Returns state vector, final excited state probability P(|1>), and readout IQ coordinates.
        """
        # State vector: [alpha, beta] for alpha|0> + beta|1>
        # Start in ground state |0>
        state = np.array([1.0 + 0.0j, 0.0 + 0.0j])
        total_time_ns = 0.0
        dac_traces = {"xy": [], "flux": [], "readout": []}

        for op in operations:
            op_name = op[0].upper()

            if op_name == "RESET":
                state = np.array([1.0 + 0.0j, 0.0 + 0.0j])

            elif op_name in ["X", "X180"]:
                # Full pi rotation around X
                pulse = self.pe.generate_drag_pulse(self.calibrated_pi_amp, duration_ns=20.0, phase_rad=0.0)
                state = self._apply_rotation(state, theta_rad=np.pi, phi_rad=0.0)
                total_time_ns += 20.0

            elif op_name in ["SX", "X90", "HALF_PI_X"]:
                # 90-degree rotation around X
                pulse = self.pe.generate_drag_pulse(self.calibrated_pi_amp / 2.0, duration_ns=20.0, phase_rad=0.0)
                state = self._apply_rotation(state, theta_rad=np.pi / 2.0, phi_rad=0.0)
                total_time_ns += 20.0

            elif op_name in ["Y", "Y180"]:
                # Full pi rotation around Y
                pulse = self.pe.generate_drag_pulse(self.calibrated_pi_amp, duration_ns=20.0, phase_rad=np.pi / 2.0)
                state = self._apply_rotation(state, theta_rad=np.pi, phi_rad=np.pi / 2.0)
                total_time_ns += 20.0

            elif op_name in ["SY", "Y90", "HALF_PI_Y"]:
                # 90-degree rotation around Y
                pulse = self.pe.generate_drag_pulse(self.calibrated_pi_amp / 2.0, duration_ns=20.0, phase_rad=np.pi / 2.0)
                state = self._apply_rotation(state, theta_rad=np.pi / 2.0, phi_rad=np.pi / 2.0)
                total_time_ns += 20.0

            elif op_name == "DELAY":
                delay_ns = op[1]
                # Free evolution dephasing / precession
                state = self._apply_free_evolution(state, delay_ns)
                total_time_ns += delay_ns

            elif op_name == "PULSE_AMP":
                # Arbitrary amplitude pulse for Rabi calibration
                amp_v = op[1]
                phase = op[2] if len(op) > 2 else 0.0
                theta = (amp_v / self.calibrated_pi_amp) * np.pi
                state = self._apply_rotation(state, theta_rad=theta, phi_rad=phase)
                total_time_ns += 20.0

        p1 = abs(state[1])**2 # Probability of |1>
        return state, p1, total_time_ns

    def _apply_rotation(self, state, theta_rad, phi_rad):
        """Applies single-qubit SU(2) rotation matrix."""
        cos_t = np.cos(theta_rad / 2.0)
        sin_t = np.sin(theta_rad / 2.0)
        # U = [[cos(theta/2), -i * exp(-i*phi) * sin(theta/2)],
        #      [-i * exp(i*phi) * sin(theta/2), cos(theta/2)]]
        u00 = cos_t
        u01 = -1j * np.exp(-1j * phi_rad) * sin_t
        u10 = -1j * np.exp(1j * phi_rad) * sin_t
        u11 = cos_t
        new_s0 = u00 * state[0] + u01 * state[1]
        new_s1 = u10 * state[0] + u11 * state[1]
        return np.array([new_s0, new_s1])

    def _apply_free_evolution(self, state, delay_ns, detuning_MHz=2.5):
        """Simulates free precession (detuning) and T2* dephasing during delay."""
        # Precession angle = 2*pi * detuning * tau
        phase = 2.0 * np.pi * (detuning_MHz * 1e6) * (delay_ns * 1e-9)
        # T2* dephasing decay factor
        decay = np.exp(-delay_ns / (self.T2_star_us * 1e3))

        new_s0 = state[0]
        new_s1 = state[1] * np.exp(-1j * phase) * decay
        # Normalize
        norm = np.sqrt(abs(new_s0)**2 + abs(new_s1)**2)
        return np.array([new_s0 / norm, new_s1 / norm])

    def generate_single_shot_readout(self, p1, num_shots=1000):
        """
        Simulates dispersive readout IQ plane discrimination blobs.
        State |0> centers at I = +0.25, Q = 0.0.
        State |1> centers at I = -0.25, Q = 0.0 (phase shifted by 2*chi/kappa).
        """
        # Ground and excited center centroids in IQ plane
        centroid_0 = np.array([0.25, 0.05])
        centroid_1 = np.array([-0.25, -0.05])

        # Noise spread from cryogenic HEMT amplifier
        sigma_noise = 0.095

        # Draw binary collapse states according to Born rule P(|1>)
        states = np.random.binomial(1, p1, num_shots)

        i_pts = np.zeros(num_shots)
        q_pts = np.zeros(num_shots)

        for idx, s in enumerate(states):
            center = centroid_1 if s == 1 else centroid_0
            i_pts[idx] = np.random.normal(center[0], sigma_noise)
            q_pts[idx] = np.random.normal(center[1], sigma_noise)

        # Threshold discrimination at I = 0.0
        discriminated_p1 = np.mean(i_pts < 0.0)

        return i_pts, q_pts, discriminated_p1
