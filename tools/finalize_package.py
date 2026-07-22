import datetime as dt
import hashlib
import json
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
OUT = ROOT / "outputs/BigDipper_Korean_Patch"
PATCH = OUT / "patch"
QUALITY = OUT / "quality"
LICENSES = OUT / "licenses"
GAME = Path(r"P:\SteamLibrary\steamapps\common\Big Dipper\WIN")
BACKUP = GAME / "_KoreanPatchBackup"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


QUALITY.mkdir(parents=True, exist_ok=True)
copy(BASE / "translation/Text3_Korean_v2.txt", OUT / "Text3_Korean.txt")
copy(BASE / "translation/v2_final.json", QUALITY / "translation-map.json")
copy(BASE / "translation/v2_qa_report.json", QUALITY / "translation-qa.json")
copy(BASE / "translation/v2_crossreview_report.json", QUALITY / "crossreview.json")
copy(BASE / "font/font-report.json", QUALITY / "font-report.json")
copy(BASE / "font/korean-sdf-atlas.png", QUALITY / "korean-sdf-atlas.png")
copy(BASE / "font/font-comparison.png", QUALITY / "font-comparison.png")
copy(BASE / "tmp-material-patched-1.2.2.txt", QUALITY / "font-asset-verification.txt")
copy(BASE / "font/glyph-target-audit.json", QUALITY / "glyph-target-audit.json")
copy(BASE / "font/OFL-NotoSansCJK.txt", LICENSES / "OFL-NotoSansCJK.txt")
old_license = LICENSES / "OFL-NotoSansKR.txt"
if old_license.exists():
    old_license.unlink()

old_screenshot = OUT / "runtime-mainmenu.png"
if old_screenshot.exists():
    old_screenshot.unlink()

payload_files = {
    path.relative_to(PATCH).as_posix(): sha256(path)
    for path in sorted(PATCH.rglob("*"))
    if path.is_file()
}

resources = PATCH / "Big Dipper_Data/resources.assets"
shared = PATCH / "Big Dipper_Data/sharedassets1.assets"
plugin = PATCH / "BepInEx/plugins/BigDipperKoreanSafe.dll"
source_text = BASE / "inspection/textassets/resources.assets/128_Text2.txt"
final_text = BASE / "translation/Text3_Korean_v2.txt"
final_map = BASE / "translation/v2_final.json"
font_report = json.loads((BASE / "font/font-report.json").read_text(encoding="utf-8"))

manifest = {
    "game": "Big Dipper",
    "patch_name": "Big Dipper unofficial Korean patch",
    "patch_version": "1.2.2",
    "target": "Steam Windows 32-bit / Unity 2018.3.3f1",
    "language_slot": "Simplified Chinese (Text3)",
    "translation": {
        "source_language": "English",
        "target_language": "Korean",
        "translated_records": 1408,
        "preserved_commands": 579,
        "text_asset_path_id": 125,
        "text_asset_name": "Text3",
        "source_text_sha256": sha256(source_text),
        "translation_map_sha256": sha256(final_map),
        "final_text_sha256": sha256(final_text),
    },
    "font": {
        "name": font_report["font_name"],
        "weight": font_report["font_weight"],
        "font_asset_path_id": 644,
        "atlas_texture_path_id": 51,
        "glyph_count": font_report["glyph_count"],
        "original_glyph_count": font_report["original_glyph_count"],
        "original_glyphs_preserved": font_report["original_glyphs_preserved"],
        "hangul_syllables": font_report["hangul_syllables"],
        "atlas_size": font_report["atlas_size"],
        "point_size": font_report["point_size"],
        "padding": font_report["padding"],
        "gradient_scale": font_report["gradient_scale"],
        "material_texture_size": font_report["material_texture_size"],
        "missing_required_glyphs": 0,
        "required_sources": font_report["required_sources"],
        "plugin_unique_characters": font_report["plugin_unique_characters"],
        "plugin_missing_codepoints_after_build": font_report["plugin_missing_codepoints_after_build"],
        "source_sha256": font_report["font_source_sha256"],
        "license": font_report["license"],
        "license_sha256": font_report["license_sha256"],
    },
    "original_resources_sha256": sha256(BACKUP / "resources.assets"),
    "patched_resources_sha256": sha256(resources),
    "original_sharedassets1_sha256": sha256(BACKUP / "sharedassets1.assets"),
    "patched_sharedassets1_sha256": sha256(shared),
    "plugin_sha256": sha256(plugin),
    "build_identity": {
        "game_exe_sha256": sha256(GAME / "Big Dipper.exe"),
        "assembly_csharp_sha256": sha256(GAME / "Big Dipper_Data/Managed/Assembly-CSharp.dll"),
    },
    "payload_files": payload_files,
    "quality_reports": [
    "quality/translation-qa.json",
    "quality/crossreview.json",
    "quality/font-report.json",
    "quality/glyph-target-audit.json",
    "quality/runtime/runtime-report.json",
],
    "built_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
}

# Hash every distributable root file except the manifest itself, which would be recursive.
distribution_files = {}
for path in sorted(OUT.rglob("*")):
    if not path.is_file() or path.name == "manifest.json":
        continue
    distribution_files[path.relative_to(OUT).as_posix()] = sha256(path)
manifest["distribution_files"] = distribution_files

(OUT / "manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps({
    "manifest": str(OUT / "manifest.json"),
    "payload_files": len(payload_files),
    "distribution_files": len(distribution_files),
    "resources": manifest["patched_resources_sha256"],
    "sharedassets1": manifest["patched_sharedassets1_sha256"],
    "plugin": manifest["plugin_sha256"],
}, ensure_ascii=False, indent=2))
