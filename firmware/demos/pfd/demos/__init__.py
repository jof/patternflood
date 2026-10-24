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

from .. import upstream

OURS = [Classic, Etch, Squash, Cycles, Sand, Harmono, Rewind, Reaction, Rotor, Echo, Rocket, Vault, Mandala]
ALL = OURS + upstream.demos()       # upstream Patternflow's presets, after ours
