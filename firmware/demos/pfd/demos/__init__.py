"""Demo registry, in menu order."""
from .classic import Classic
from .etch import Etch
from .squash import Squash
from .cycles import Cycles
from .sand import Sand
from .harmono import Harmono
from .rewind import Rewind
from .reaction import Reaction
from .rotor import Rotor
from .echo import Echo
from .rocket import Rocket
from .vault import Vault
from .mandala import Mandala
from .droplet import Droplet
from .terrain import Terrain
from .glitch import Glitch
from .kaleido import Kaleido
from .pool import Pool
from .resort import Resort
from .tempo import Tempo
from .spectrum import Spectrum
from .scope import Scope
from .waterfall import Waterfall
from .pulse import Pulse
from .played import Prism, Rain, Spores, Lissajous, NightDrive
from .milk import Milk, MilkTunnel, MilkFlame, MilkMirror, MilkEcho
from .superscope import Superscope
from .obra import Obra
from .bittunnel import BitTunnel
from .riso import Riso
from .strange import Strange
from .pixelsort import PixelSort
from .moon import Moon
from .smoke import Smoke
from .sea import Sea
from .caustics import Caustics
from .galaxy import Galaxy
from .valley import Valley
from .opart import OpArt
from .bonfire import Bonfire
from .mandel import Mandel
from .lava import Lava
from .tesla import Tesla
from .window import Window
from .life import Life
from .jelly import Jelly
from .aurora import Aurora
from .warp import Warp
from .snow import Snow
from .helix import Helix
from .fireworks import Fireworks
from .gears import Gears
from .pendulums import Pendulums
from .spiro import Spiro
from .orrery import Orrery
from .flock import Flock
from .koi import Koi
from .shore import Shore
from .grove import Grove
from .cumulus import Cumulus
from .radar import Radar
from .zen import Zen
from .plankton import Plankton
from .neon import Neon
from .clock import Clock
from .truchet import Truchet
from .isobands import Isobands
from .glass import Glass
from .chroma import Chroma
from .guilloche import Guilloche
from .weave import Weave
from .quasi import Quasi
from .cyclic import Cyclic
from .wallpaper import Wallpaper
from .droste import Droste
from .hexpulse import HexPulse
from .ribbons import Ribbons
from .moire import Moire
from .copper import Copper
from .streams import Streams
from .girih import Girih
from .marbling import Marbling
from .dial import Dial
from .cable import Cable

from .. import community, upstream
from ..runtime import SHELF_NAMES

PLAY = [Classic, Etch, Squash, Cycles, Sand, Harmono, Rewind, Reaction, Rotor, Echo, Rocket, Vault, Mandala,
        Droplet, Terrain, Glitch, Kaleido, Pool, Resort]
# Our own patterns in Patternflow's manner (pfd/demos/original.py): on the Patternflood shelf, after the play demos
ORIGINALS = [BitTunnel, Obra, Riso, Strange, PixelSort, Moon, Smoke, Sea, Caustics, Galaxy, Valley, OpArt, Bonfire,
             Mandel, Lava, Tesla, Window, Life, Jelly, Aurora, Warp, Snow, Helix, Fireworks, Gears, Pendulums, Spiro,
             Orrery, Flock, Koi, Shore, Grove, Cumulus, Radar, Zen, Plankton, Neon, Clock, Truchet, Isobands, Glass,
             Chroma, Guilloche, Weave, Quasi, Cyclic, Wallpaper, Droste, HexPulse, Ribbons, Moire, Copper, Streams,
             Girih, Marbling, Dial]
AUDIO = [Milk, MilkTunnel, MilkFlame, MilkMirror, MilkEcho, Superscope, Pulse, Spectrum, Scope, Waterfall, Prism, Rain, Spores, Lissajous, NightDrive, Tempo]
OURS = PLAY + ORIGINALS + AUDIO + [Cable]

# Upstream Patternflow's presets (SeungHun's), ours and the community's, sorted onto the shelves in menu order
ALL = sorted(upstream.demos() + OURS + community.demos(), key=lambda d: list(SHELF_NAMES).index(d.group))
