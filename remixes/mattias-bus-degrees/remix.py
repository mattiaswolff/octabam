"""Personal bus candidate with the degree-root replacement selected explicitly."""
from dataclasses import replace
from pathlib import Path
import runpy
from remix.schema import Proof

_base = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'mattias-bus/remix.py'))['REMIX']
REMIX = replace(
    _base, name='mattias-bus-degrees', proof=Proof.PORT,
    proof_note='D0 degree lifecycle, panel and playback port suites passed; hardware untested',
    doc='Personal bus selection plus degree/register Harmony roots.',
    modules=(*_base.modules, 'HARMONY DEGREES'),
)
