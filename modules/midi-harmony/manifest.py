"""MIDI scale notes and diatonic chords, before the stock arpeggiator."""
from remix.schema import Category, Detour, Gate, Kind, Linked, Module, Proof, Poke, SymbolRef


def follow_inc(modules):
    return ('.set HAVE_FOLLOW,1\n' if 'MIDI FOLLOW' in modules else '') + ('.set HAVE_SCALES,1\n' if 'MIDI SCALES' in modules else '')


MODULE = Module(
    name='midi-harmony', key='MIDI HARMONY', kind=Kind.CF_PATCH,
    category=Category.MIDI_USB, author='Local Octabam prototype',
    author_url='https://github.com/sambanks/octabam', proof=Proof.PORT,
    proof_note='Development candidate; hardware untested',
    doc='MIDI NOTE SETUP HARM using stock ARP KEY/scale; optional MIDI Follow inheritance.',
    linked=(Linked('midiharmony', 'modules/midi-harmony/harmony.s', dram=True, include=follow_inc),),
    symbol_refs=(SymbolRef(0x400d3f34, 0, 'midiharmony', 'mh_type_format', 'NOTE SETUP F TYPE formatter'),),
    pokes=(
        Poke(0x400d3e96, b'----\0\0', b'HARM\0\0', 'NOTE SETUP F label'),
        Poke(0x400d3f04, bytes.fromhex('00000080'), bytes.fromhex('00000004'), 'four TYPE values'),
        Poke(0x400d3f64, bytes(4), bytes.fromhex('400467a4'), 'TYPE text widget'),
        Poke(0x400d3fca, b'\x01', b'\x11', 'enable NOTE SETUP F only'),
    ),
    detours=(
        Detour(0x40036682, bytes.fromhex('2001e9882040'), 'midiharmony', 'mh_draw_type', 'NOTE SETUP F module value'),
        Detour(0x4003a8e8, bytes.fromhex('4feffff048d70c0c'), 'midiharmony', 'mh_note_encoder', 'NOTE SETUP F TYPE encoder', pad_to=8),
        Detour(0x4007a1b0, bytes.fromhex('181020037403'), 'midiharmony', 'mh_draw_key', 'show source KEY when following'),
        Detour(0x4009fad2, bytes.fromhex("102800316606"), "midiharmony", "mh_scale", "avoid second stock scale correction"),
        Detour(0x4009fa2a, bytes.fromhex('240e59822f02'), 'midiharmony', 'mh_sequence', 'generate working chord before stock arp'),
        Detour(0x4009e9a8, bytes.fromhex('4fefffe448d704fc'), 'midiharmony', 'mh_keyboard', 'live MIDI notes with release ownership', pad_to=8),
        Detour(0x4007a2ec, bytes.fromhex('4fefffdc48d71cfc'), 'midiharmony', 'mh_arp_encoder', 'inherited native KEY is read-only', pad_to=8),
        Detour(0x400867aa, bytes.fromhex('ba8067001a76'), 'midiharmony', 'mh_load', 'project comment reader after stock/quantizer comment prefix'),
        Detour(0x40088882, bytes.fromhex('71398000004e'), 'midiharmony', 'mh_save', 'project comment writer'),
        Detour(0x40025ac8, bytes.fromhex('42b9100b14d8'), 'midiharmony', 'mh_defaults', 'new project settings defaults'),
        Detour(0x40010224, bytes.fromhex('7139100b14ae'), 'midiharmony', 'mh_boot', 'validate battery-backed settings'),
    ),
    gates=(Gate('tools/verify/verify_midi_harmony.py', stage='image', venv=True),),
)
