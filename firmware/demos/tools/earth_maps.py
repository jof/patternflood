#!/usr/bin/env python3
"""Build Moon's Earth maps (pfd/demos/earth/) from NASA's public-domain imagery.

    tools/earth_maps.py DIR      # DIR holds the two downloads below

day.png:   Blue Marble Next Generation, topography and bathymetry, July 2004 (Reto Stöckli,
           NASA Earth Observatory), 5400 x 2700, downsampled to 512 x 256.
           https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73751/world.topo.bathy.200407.3x5400x2700.jpg
night.png: Black Marble 2016 (NASA Earth Observatory), 3600 x 1800: its lights alone (the yellow,
           not the moonlit blue of the land), each pixel the brighter of its block's peak and twice
           its mean, so small towns survive the shrink.
           https://eoimages.gsfc.nasa.gov/images/imagerecords/144000/144898/BlackMarble_2016_01deg.jpg
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

W, H = 512, 256
OUT = Path(__file__).resolve().parent.parent / "pfd/demos/earth"


def main():
    src = Path(sys.argv[1])
    OUT.mkdir(exist_ok=True)
    day = Image.open(src / "world.topo.bathy.200407.3x5400x2700.jpg").convert("RGB")
    day.resize((W, H), Image.LANCZOS).save(OUT / "day.png", optimize=True)

    k = 7
    night = Image.open(src / "BlackMarble_2016_01deg.jpg").convert("RGB").resize((W * k, H * k), Image.BOX)
    a = np.asarray(night, np.float32) / 255
    lights = np.clip((a[..., 0] + a[..., 1]) / 2 - a[..., 2] * 0.9 - 0.02, 0, 1)
    blocks = lights.reshape(H, k, W, k)
    v = np.maximum(blocks.max((1, 3)), 2 * blocks.mean((1, 3)))
    v = np.clip(v / np.percentile(v, 99.7), 0, 1)
    Image.fromarray((v * 255 + 0.5).astype(np.uint8), "L").save(OUT / "night.png", optimize=True)
    print(f"{OUT}/day.png, night.png")


if __name__ == "__main__":
    main()
