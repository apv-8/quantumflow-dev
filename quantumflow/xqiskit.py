# Copyright 2019-, Gavin E. Crooks and the QuantumFlow contributors
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.


"""
.. contents:: :local:
.. currentmodule:: quantumflow

Interface between IBM's Qiskit and QuantumFlow


.. autofunction:: qiskit_to_circuit
.. autofunction:: circuit_qiskit
"""


from .circuits import Circuit
from .stdops import If
from .gates import NAMED_GATES
from .utils import invert_map
from .translate import select_translators, translate
import qiskit as qk

# This module imports qiskit, so we do not include it at top level.
# Must be imorted explicitly. e.g.
# > from quantumflow.xqiskit import qiskit_to_circuit, circuit_to_qiskit
#
# Note that QASM specific gates are defined in quantumflow/gates/gates_qasm.py
# Concevable you might want to use those gates in QuantumFlow without loading
# qiskit

# TODO: __all__

QASM_TO_QF = {
    'ccx': 'CCNOT',
    'ch': 'CH',
    'crz': 'CRZ',
    'cswap': 'CSWAP',
    'cu1': 'CPHASE',
    'cu3': 'CU3',
    'cx': 'CNOT',
    'cy': 'CY',
    'cz': 'CZ',
    'h': 'H',
    'id': 'I',
    'rx': 'RZ',
    'ry': 'RY',
    'rz': 'RZ',
    'rzz': 'RZZ',
    's': 'S',
    'sdg': 'S_H',
    'swap': 'SWAP',
    't': 'T',
    'tdg': 'T_H',
    'u1': 'PHASE',
    'u2': 'U2',
    'u3': 'U3',
    'x': 'X',
    'y': 'Y',
    'z': 'Z',
    # 'barrier': 'Barrier',   # TODO TESTME
    # 'measure': 'Measure'   # TODO
    }
"""Map from qiskit operation names to QuantumFlow names"""


def qiskit_to_circuit(qkcircuit: qk.QuantumCircuit) -> Circuit:
    """Convert a qsikit QuantumCircuit to QuantumFlow's Circuit"""
    # We assume that there is only one quantum register of qubits.

    named_ops = dict(NAMED_GATES)

    circ = Circuit()

    for instruction, qargs, cargs in qkcircuit:
        name = instruction.name
        if name not in QASM_TO_QF:
            raise NotImplementedError('Unknown qiskit operation')

        qf_name = QASM_TO_QF[name]
        qubits = [q.index for q in qargs]
        args = [float(param) for param in instruction.params] + qubits
        gate = named_ops[qf_name](*args)

        if instruction.control is None:
            circ += gate
        else:
            classical, value = instruction.control
            circ += If(gate, classical, value)

    return circ


def circuit_to_qiskit(circ: Circuit,
                      translate: bool = False) -> qk.QuantumCircuit:
    """Convert a QuantumFlow's Circuit to a qsikit QuantumCircuit."""

    # In qiskit each gate is defined as a class, and then a method is
    # monkey patched onto QuantumCircuit which will create that gate and
    # append it to the circuit. The method names correspond to the qasm
    # names in QASM_TO_QF

    if translate:
        circ = translate_gates_to_qiskit(circ)

    QF_TO_QASM = invert_map(QASM_TO_QF)
    QF_TO_QASM['I'] = 'iden'

    # We assume only one QuantumRegister. Represent qubits by index in register
    qreg = qk.QuantumRegister(circ.qubit_nb)
    qubit_map = {q: qreg[i] for i, q in enumerate(circ.qubits)}

    qkcircuit = qk.QuantumCircuit(qreg)

    for op in circ:
        name = QF_TO_QASM[op.name]
        params = op.params.values()
        qbs = [qubit_map[qb] for qb in op.qubits]

        getattr(qkcircuit, name)(*params, *qbs)

        # TODO: Handle If seperatly

    return qkcircuit


# DOCME TESTME
def translate_gates_to_qiskit(circ: Circuit) -> Circuit:
    target_gates = list([NAMED_GATES[n] for n in QASM_TO_QF.values()])
    trans = select_translators(target_gates)  # type: ignore

    circ = translate(circ, trans)
    return circ