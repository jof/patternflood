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

from .. import upstream

OURS = [Classic, Etch, Squash, Cycles, Sand, Harmono, Rewind, Reaction, Rotor, Echo, Rocket, Vault, Mandala,
        Droplet, Terrain, Glitch, Kaleido, Pool, Resort,
        Tempo, Spectrum, Scope, Waterfall, Pulse]
ALL = OURS + upstream.demos()       # upstream Patternflow's presets, after ours
