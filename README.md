# Trash Panda Dice So Nice Faces

A raccoon / trash-panda dice set for [Dice So Nice](https://foundryvtt.com/packages/dice-so-nice). Icon faces on a dumpster-green wrap. Nat 20 is an orange raccoon head; nat 1 is a magenta trash can.

Works on **Foundry VTT 13.351** with Dice So Nice **5.2.3** (Pathfinder 2e **7.12.2**) and **Foundry VTT 14.365** with Dice So Nice **6.2.9** (Pathfinder 2e **8.4.0**).

## Install

1. Copy this folder to `{userData}/Data/modules/trash-panda-dsn` so `module.json` sits at that path.
2. Enable **Trash Panda Dice So Nice Faces** in *Manage Modules* (Dice So Nice must be enabled).
3. Open *Game Settings → Dice So Nice*.
   - **Dice Presets:** Trash Panda Faces
   - **Themes:** Trash Panda Classic or Trash Panda Dumpster
4. Under **Special Effects**, add two rows (per player):
   - Advanced `d20 == 20` → **Trash Panda Clap** (`PlayTrashPandaClap`) — caption **Nice**
   - Advanced `d20 == 1` → **Trash Panda Dumpster Dive** (`PlayTrashPandaDumpster`) — caption **Fail**

If faces show file paths after an update, re-select the Trash Panda theme and save.

## Special Effects

| Trigger | Effect | GIF |
| --- | --- | --- |
| `d20 == 20` | Trash Panda Clap | `assets/sfx/raccoon-clap.gif` |
| `d20 == 1` | Trash Panda Dumpster Dive | `assets/sfx/jump-falling.gif` |

Import/Load appearance profiles do not install these SFX modes.

## Development

```bash
python3 tests/test_module.py
python3 scripts/compose-assets.py   # rebuild faces and dumpster texture
bash package.sh                     # dist/trash-panda-dsn-1.0.0.zip
```

Keep texture paths in `ASSETS`, themes in `COLORSETS`, face lists in `FACESETS`, and SFX URLs in `scripts/sfx.js`.

## License

See [LICENSE.md](LICENSE.md). Face icons are CC BY 3.0 from [game-icons.net](https://game-icons.net/).
