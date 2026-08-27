#!/usr/bin/env python3
"""Contract tests for the Trash Panda Dice So Nice module.

These tests encode a dual-version manifest (Foundry 13.351–14.365,
Dice So Nice 5.2.3–6.2.9) and registration calls confirmed from both
DSN 5.2.3 (installed bundle) and DSN 6.2.9 source.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MODULE_JSON = ROOT / "module.json"
SCRIPT = ROOT / "scripts" / "trash-panda-dsn.js"
SFX_SCRIPT = ROOT / "scripts" / "sfx.js"
README = ROOT / "README.md"
PACKAGE_SCRIPT = ROOT / "package.sh"

CLAP_GIF = "/modules/trash-panda-dsn/assets/sfx/raccoon-clap.gif"
DUMPSTER_GIF = "/modules/trash-panda-dsn/assets/sfx/jump-falling.gif"
SFX_FILES = [
    "assets/sfx/raccoon-clap.gif",
    "assets/sfx/jump-falling.gif",
]

TEXTURE_FILES = [
    "assets/textures/trash-panda-dumpster.webp",
    "assets/textures/trash-panda-dumpster-bump.webp",
]

# Icon-only faces. Min = trash-can, max = raccoon-head.
# DSN 6.2.9 order still applies: d10 is 1-9 then 0; d100 is 10-90 then 00.


def test_module_json_dual_version():
    manifest = json.loads(MODULE_JSON.read_text(encoding="utf-8"))
    assert manifest["id"] == "trash-panda-dsn"
    assert manifest["title"] == "Trash Panda Dice So Nice Faces"
    assert manifest["compatibility"]["minimum"] == "13"
    assert manifest["compatibility"]["verified"] == "14.365"
    assert "maximum" not in manifest["compatibility"]
    assert "scripts/trash-panda-dsn.js" in manifest["esmodules"]
    requires = manifest["relationships"]["requires"]
    dsn = next(item for item in requires if item["id"] == "dice-so-nice")
    assert dsn["type"] == "module"
    assert dsn["compatibility"]["minimum"] == "5.2.3"
    assert dsn["compatibility"]["verified"] == "6.2.9"
    recommends = manifest["relationships"]["recommends"]
    pf2e = next(item for item in recommends if item["id"] == "pf2e")
    assert pf2e["compatibility"]["minimum"] == "7.12.2"
    assert pf2e["compatibility"]["verified"] == "8.4.0"


def test_registration_helpers_exist():
    source = SCRIPT.read_text(encoding="utf-8")
    for name in (
        "getDiceSoNiceApi",
        "registerTextures",
        "registerColorsets",
        "registerFaces",
        "initModule",
    ):
        assert f"function {name}(" in source, f"missing helper {name}"
    sfx_source = SFX_SCRIPT.read_text(encoding="utf-8") if SFX_SCRIPT.is_file() else ""
    assert "function registerSfx(" in (source + "\n" + sfx_source), "missing helper registerSfx"
    assert 'const MODULE_ID = "trash-panda-dsn"' in source
    assert "const ASSETS =" in source
    assert "const COLORSETS =" in source
    assert "const FACESETS =" in source


def test_dsn_629_api_calls():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "diceSoNiceReady" in source
    assert "new DiceSystem(" in source
    assert "addSystem(" in source
    assert "addTexture(" in source
    assert "addColorset(" in source
    assert "addDicePreset(" in source
    assert "/modules/dice-so-nice/api.js" in source
    assert "faceLabels(" in source
    assert "assets/faces/${dieType}/" in source
    assert "/modules/${MODULE_ID}/assets/faces/${dieType}/${face}.png" in source or ".png`" in source
    assert 'type: "d10"' in source
    assert 'type: "d100"' in source
    assert "d10 is 1-9 then 0" in source
    assert "d100 is 10-90 then 00" in source
    assert source.index("addTexture(") < source.index("addColorset(")


def test_readme_documents_api_and_assets():
    readme = README.read_text(encoding="utf-8")
    assert "14.365" in readme
    assert "13.351" in readme
    assert "6.2.9" in readme
    assert "5.2.3" in readme
    assert "Special Effects" in readme
    assert "d20 == 20" in readme
    assert "d20 == 1" in readme
    assert "PlayTrashPandaClap" in readme
    assert "PlayTrashPandaDumpster" in readme


def test_sfx_gif_modes():
    assert SFX_SCRIPT.is_file(), "missing scripts/sfx.js"
    sfx = SFX_SCRIPT.read_text(encoding="utf-8")
    main = SCRIPT.read_text(encoding="utf-8")
    combined = sfx + "\n" + main
    assert "addSFXMode" in combined
    assert "DiceSFX" in sfx
    assert "/modules/dice-so-nice/api.js" in sfx
    assert 'id: "PlayTrashPandaClap"' in sfx or 'static id = "PlayTrashPandaClap"' in sfx
    assert 'id: "PlayTrashPandaDumpster"' in sfx or 'static id = "PlayTrashPandaDumpster"' in sfx
    assert CLAP_GIF in sfx
    assert DUMPSTER_GIF in sfx
    assert 'caption: "Nice"' in sfx
    assert 'caption: "Fail"' in sfx
    assert "#3D5C4A" in sfx
    assert "createElement(\"div\")" in sfx or "createElement('div')" in sfx
    assert "media.tenor.com" not in sfx
    assert "createElement(\"img\")" in sfx or "createElement('img')" in sfx
    for relative in SFX_FILES:
        path = ROOT / relative
        assert path.is_file(), f"missing SFX gif {relative}"
        with Image.open(path) as image:
            assert image.format == "GIF", f"{relative} is {image.format}, not GIF"
    assert "registerSfx(" in main
    assert "typeof api.addSFXMode" in main or 'typeof api.addSFXMode' in main
    required = ["addSystem", "addTexture", "addColorset", "addDicePreset"]
    for method in required:
        assert f'"{method}"' in main
    assert '"addSFXMode"' not in main, "addSFXMode must stay optional so missing SFX API does not abort dice registration"


def _opaque_bbox(path: Path) -> tuple[int, int, int, int]:
    with Image.open(path) as image:
        bbox = image.convert("RGBA").getchannel("A").getbbox()
    assert bbox is not None, f"{path} is empty"
    return bbox


def _mean_opaque_rgb(path: Path) -> tuple[float, float, float]:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        pixels = rgba.load()
        width, height = rgba.size
        total = [0, 0, 0]
        count = 0
        for y in range(height):
            for x in range(width):
                red, green, blue, alpha = pixels[x, y]
                if alpha <= 128:
                    continue
                total[0] += red
                total[1] += green
                total[2] += blue
                count += 1
    assert count, f"{path} has no opaque pixels"
    return total[0] / count, total[1] / count, total[2] / count


def test_face_icons_leave_margin():
    samples = [
        "assets/faces/d20/01.png",
        "assets/faces/d20/10.png",
        "assets/faces/d20/20.png",
        "assets/faces/d6/03.png",
        "assets/faces/d4/02.png",
    ]
    max_span = 150
    for relative in samples:
        left, top, right, bottom = _opaque_bbox(ROOT / relative)
        width = right - left
        height = bottom - top
        assert width <= max_span, f"{relative} width {width} > {max_span}"
        assert height <= max_span, f"{relative} height {height} > {max_span}"


def test_trash_can_contrasts_dumpster_green():
    red, green, blue = _mean_opaque_rgb(ROOT / "assets/faces/d20/01.png")
    assert red > 180, f"trash can red {red:.1f} should be hot magenta, not sage"
    assert red > green + 40, f"trash can should not sit in the dumpster-green hue (R={red:.1f} G={green:.1f})"
    assert blue > green, f"trash can should lean magenta, not yellow-green (G={green:.1f} B={blue:.1f})"


def test_dumpster_texture_has_no_orange_stripe():
    path = ROOT / "assets/textures/trash-panda-dumpster.webp"
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        pixels = rgb.load()
        width, height = rgb.size
        reds = []
        greens = []
        for y in range(196, 216):
            for x in range(0, width, 8):
                red, green, _blue = pixels[x, y]
                reds.append(red)
                greens.append(green)
    assert greens, f"{path} stripe band was empty"
    mean_red = sum(reds) / len(reds)
    mean_green = sum(greens) / len(greens)
    assert mean_green > mean_red, (
        f"dumpster texture still has an orange band "
        f"(R={mean_red:.1f} G={mean_green:.1f})"
    )


def test_runtime_textures_are_256_webp():
    for relative in TEXTURE_FILES:
        path = ROOT / relative
        assert path.is_file(), f"missing asset {relative}"
        with Image.open(path) as image:
            assert image.format == "WEBP", f"{relative} is {image.format}, not WEBP"
            assert image.size == (256, 256), f"{relative} is {image.size}, not 256x256"


def test_packaging_script_builds_zip():
    assert PACKAGE_SCRIPT.is_file()
    subprocess.run(["bash", str(PACKAGE_SCRIPT)], check=True, cwd=ROOT)
    zips = list((ROOT / "dist").glob("trash-panda-dsn-*.zip"))
    assert zips, "packaging script did not create a zip"
    with zipfile.ZipFile(zips[0]) as archive:
        names = archive.namelist()
        assert "trash-panda-dsn/module.json" in names
        assert "trash-panda-dsn/scripts/trash-panda-dsn.js" in names
        assert "trash-panda-dsn/scripts/sfx.js" in names
        assert "trash-panda-dsn/assets/sfx/raccoon-clap.gif" in names
        assert "trash-panda-dsn/assets/sfx/jump-falling.gif" in names
        assert "trash-panda-dsn/assets/faces/d20/01.png" in names
        assert any(name.startswith("trash-panda-dsn/CURSOR") for name in names) is False
        assert any("/assets/sources/" in name for name in names) is False


if __name__ == "__main__":
    tests = [
        test_module_json_dual_version,
        test_registration_helpers_exist,
        test_dsn_629_api_calls,
        test_readme_documents_api_and_assets,
        test_sfx_gif_modes,
        test_runtime_textures_are_256_webp,
        test_face_icons_leave_margin,
        test_trash_can_contrasts_dumpster_green,
        test_dumpster_texture_has_no_orange_stripe,
        test_packaging_script_builds_zip,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {test.__name__}: {exc}")
    sys.exit(1 if failed else 0)
