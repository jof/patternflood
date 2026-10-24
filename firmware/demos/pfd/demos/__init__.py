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

from .. import upstream

OURS = [Classic, Etch, Squash, Cycles, Sand, Harmono, Rewind, Reaction, Rotor, Echo, Rocket, Vault, Mandala,
        Droplet, Terrain, Glitch, Kaleido, Pool, Resort]
AUDIO = [Milk, MilkTunnel, MilkFlame, MilkMirror, MilkEcho, Superscope, Pulse, Spectrum, Scope, Waterfall, Prism, Rain, Spores, Lissajous, NightDrive, Tempo]
OURS = OURS + AUDIO
# Our own patterns on the Patternflow shelf, each placed after the preset of Lee's it riffs on
ORIGINALS = [(BitTunnel, "pf 0521"), (Obra, "pf 0522"), (Riso, "pf 0528"), (Strange, "pf Lissajous Weave"), (PixelSort, "pf 0519-2"),
             (Moon, "pf Poincaré Sphere"), (Smoke, "pf Vector Field Flow"),
             (Sea, "pf Midsummer Sea"),
             (Caustics, "pf 0530"), (Galaxy, "pf Chromatic Vortex"),
             (Valley, "pf 0624"), (OpArt, "pf Warped Wave"),
             (Bonfire, "pf Firefly Hollow"),
             (Mandel, "pf Retro Digital Tapestry"), (Lava, "pf 0520"),
             (Tesla, "pf MagVortex"), (Window, "pf 0609"),
             (Life, "pf TileWaves"), (Jelly, "pf 0529"),
             (Aurora, "pf 0602"), (Warp, "pf 0510"),
             (Snow, "pf 0515-3"), (Helix, "pf 0512"),
             (Fireworks, "pf a big hit"), (Gears, "pf Origin"),
             (Pendulums, "pf Wave Saw")]


def _shelf(presets):
    out = list(presets)
    for cls, after in ORIGINALS:
        names = [d.name for d in out]
        out.insert(names.index(after) + 1 if after in names else len(out), cls)
    return out


ALL = OURS + _shelf(upstream.demos())       # upstream Patternflow's presets, after ours, with our originals among them
