"""Personal bus rig with native Part-owned Harmony degrees and the Kit library."""
from dataclasses import replace
from pathlib import Path
import runpy
from remix.schema import Proof

_base = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'mattias-bus/remix.py'))['REMIX']
REMIX = replace(
    _base, name='mattias-bus-degrees-kits', proof=Proof.CHECK,
    proof_note='Native Part degree gates passed; combined firmware acceptance in progress',
    doc='Personal bus rig with degree/register Harmony, Part settings and KITS.',
    modules=(*_base.modules, 'HARMONY DEGREES', 'KITS'),
)
