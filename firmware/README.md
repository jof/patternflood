# Firmware

The delta against upstream Patternflow, as a patch series.

`upstream/` is a pristine clone pinned at `87700bd` (v3.9.5) on `main`, with the
fork's work on a `desktop` branch. The port needs real edits to `config.h` and
`platformio.ini` — [`../docs/desktop/build-prep.md`](../docs/desktop/build-prep.md) §0
explains why `features/overrides.h` can't carry it — so the delta lives here as
exported patches rather than a vendored copy of the tree.

## Working on it

```bash
git -C upstream checkout desktop
# ... edit ...
git -C upstream commit -am "..."
rm -f firmware/patches/*.patch
git -C upstream format-patch main --output-directory ../firmware/patches
```

## Rebasing onto a new upstream

```bash
git -C upstream fetch origin
git -C upstream rebase <new-tag> desktop
```

A conflict here is the point of the arrangement: it means upstream changed
something this build depends on. Re-export the patches afterwards and update the
pinned commit in `.gitignore` and the docs.

## Applying to a fresh clone

```bash
git clone https://github.com/engmung/patternflow upstream
git -C upstream checkout -b desktop 87700bd
git -C upstream am ../firmware/patches/*.patch
```
