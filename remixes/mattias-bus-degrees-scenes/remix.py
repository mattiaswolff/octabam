"""Degree compatibility candidate with unmodified KITS and MIDISC2.1."""
from dataclasses import replace
from pathlib import Path
import runpy
from remix.schema import Proof

_base = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'mattias-bus-degrees-kits/remix.py'))['REMIX']
REMIX = replace(
    _base, name='mattias-bus-degrees-scenes', proof=Proof.CHECK,
    proof_note='Degree / KITS / MIDISC2.1 compatibility validation in progress; not hardware tested',
    doc='Personal bus rig with degree/register Harmony, KITS and MIDISC2.1.',
    modules=(*_base.modules, 'MIDI SCENES'),
)
