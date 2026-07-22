from __future__ import annotations

import hashlib
import json
import stat
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "outputs" / "BigDipper_Korean_Patch"
ZIP = ROOT / "outputs" / "BigDipper_Korean_Patch_1.2.2.zip"
SIDE = ZIP.with_suffix(ZIP.suffix + ".sha256.txt")
GAME = Path(r"P:\SteamLibrary\steamapps\common\Big Dipper\WIN")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def zip_sha256(archive: zipfile.ZipFile, name: str) -> str:
    digest = hashlib.sha256()
    with archive.open(name, "r") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


checks: list[tuple[str, bool]] = []


def check(name: str, result: bool) -> None:
    checks.append((name, bool(result)))


manifest_path = PACKAGE / "manifest.json"
manifest_bytes = manifest_path.read_bytes()
manifest = json.loads(manifest_bytes.decode("utf-8-sig"))
runtime = json.loads((PACKAGE / "quality/runtime/runtime-report.json").read_text(encoding="utf-8-sig"))
qa = json.loads((PACKAGE / "quality/translation-qa.json").read_text(encoding="utf-8-sig"))
cross = json.loads((PACKAGE / "quality/crossreview.json").read_text(encoding="utf-8-sig"))
font = json.loads((PACKAGE / "quality/font-report.json").read_text(encoding="utf-8-sig"))
glyph = json.loads((PACKAGE / "quality/glyph-target-audit.json").read_text(encoding="utf-8-sig"))

check("manifest version 1.2.2", manifest["patch_version"] == "1.2.2")
check("runtime report version 1.2.2", runtime["patch_version"] == "1.2.2")
check("translation source is English", manifest["translation"]["source_language"] == "English" and cross["manual_review"]["source_language"] == "English")
check("translation records 1408", qa["records"] == qa["final"] == 1408)
check("translation QA zero errors/warnings", not qa["errors"] and not qa["warnings"])
check("cross-review pass all records", cross["status"] == "pass" and cross["manual_review"]["reviewed_records"] == 1408)
check("source/output lines preserved", cross["counts"]["source_lines"] == cross["counts"]["output_lines"] == 6759)
check("579 script commands preserved", cross["counts"]["commands"] == 579)
check("final text hash bound", cross["hashes"]["output_text_sha256"] == manifest["translation"]["final_text_sha256"])
check(
    "translation manifest metadata fully bound",
    manifest["translation"]["translated_records"] == qa["records"] == cross["counts"]["catalog_records"] == cross["counts"]["final_records"]
    and manifest["translation"]["preserved_commands"] == cross["counts"]["commands"]
    and manifest["translation"]["source_text_sha256"] == cross["hashes"]["source_text_sha256"]
    and manifest["translation"]["translation_map_sha256"] == cross["hashes"]["final_map_sha256"]
    and manifest["translation"]["target_language"] == cross["manual_review"]["target_language"] == "Korean",
)
check("packaged final text hash bound", sha256(PACKAGE / "Text3_Korean.txt") == manifest["translation"]["final_text_sha256"])
check("packaged translation map hash bound", sha256(PACKAGE / "quality/translation-map.json") == manifest["translation"]["translation_map_sha256"])

check("runtime overall pass", runtime["overall_pass"])
check("runtime 22 checks zero failed", runtime["runtime"]["check_count"] == 22 and not runtime["runtime"]["failed_checks"])
check("runtime zero errors/warnings/exceptions", runtime["runtime"]["error_lines"] == runtime["runtime"]["warning_lines"] == runtime["runtime"]["exception_mentions"] == 0)
check("runtime zero hook failures", runtime["runtime"]["hook_failure_mentions"] == 0)
check("all startup hooks installed", all(runtime["runtime"]["startup_hooks"].values()))
check("menu labels and description Korean", all(runtime["runtime"]["menu"].values()))
load = runtime["runtime"]["load_confirmation"]
check("load question/yes/no pass", load["question_pass"] and load["yes_pass"] and load["no_pass"])
check("actual modal writer hook observed", load["actual_game_writer_hook_observed"])
julia = runtime["runtime"]["julia"]
check("Julia actual parser sources pass", julia["before_source_actual_parser_line"] and julia["after_source_actual_parser_line"])
check("Julia before reveal is Korean girl label", julia["before_pass"] and julia["before_visible_name"] == "\uc18c\ub140")
check("Julia after reveal is Korean Julia label", julia["after_pass"] and julia["after_visible_name"] == "\uc904\ub9ac\uc544" and julia["after_actual_forced_chinese_token"] == "\u8331\u8389\u4e9a")

font_contract = manifest["font"]
check("font is Noto Sans CJK KR Medium", font["font_name"] == font_contract["name"] == "Noto Sans CJK KR Medium")
check(
    "font manifest metadata fully bound",
    font_contract["weight"] == font["font_weight"]
    and font_contract["font_asset_path_id"] == font["font_asset_path_id"]
    and font_contract["atlas_texture_path_id"] == font["atlas_texture_path_id"]
    and font_contract["hangul_syllables"] == font["hangul_syllables"]
    and font_contract["required_sources"] == font["required_sources"]
    and font_contract["plugin_unique_characters"] == font["plugin_unique_characters"]
    and font_contract["source_sha256"] == font["font_source_sha256"]
    and font_contract["license"] == font["license"]
    and font_contract["license_sha256"] == font["license_sha256"]
    and font["source_sha256"] == manifest["original_sharedassets1_sha256"]
    and font["patched_sha256"] == manifest["patched_sharedassets1_sha256"],
)
check("font glyph contract complete", font["glyph_count"] == font["required_character_count"] == font_contract["glyph_count"] == 2769 and font["missing_required_glyphs"] == font_contract["missing_required_glyphs"] == 0)
check("plugin output font contract complete", not font["plugin_missing_codepoints_after_build"] and not font_contract["plugin_missing_codepoints_after_build"])
check("original 1656 glyphs preserved", font["original_glyph_count"] == font["original_glyphs_preserved"] == font_contract["original_glyph_count"] == font_contract["original_glyphs_preserved"] == 1656)
check("font atlas/material settings", font["atlas_size"] == font_contract["atlas_size"] == [4096, 4096] and font["material_texture_size"] == font_contract["material_texture_size"] == [4096, 4096] and font["point_size"] == font_contract["point_size"] == 64 and font["padding"] == font_contract["padding"] == 4 and font["gradient_scale"] == font_contract["gradient_scale"] == 5)
check("target Korean/CJK glyphs are real", runtime["font"]["target_korean_cjk_glyphs_present_and_not_notdef"])
check("glyph audit patched count", glyph["patched_glyph_count"] == font_contract["glyph_count"] == 2769)
check("font license present", (PACKAGE / "licenses/OFL-NotoSansCJK.txt").exists() and sha256(PACKAGE / "licenses/OFL-NotoSansCJK.txt") == font_contract["license_sha256"])
check("font asset reopen evidence present", (PACKAGE / "quality/font-asset-verification.txt").exists())

screens = runtime["runtime"]["screenshots"]
check("four fresh screenshots", len(screens) == 4 and all((PACKAGE / item["file"]).exists() for item in screens.values()))
check("all screenshot hashes", all(sha256(PACKAGE / item["file"]) == item["sha256"] for item in screens.values()))
visual = runtime["runtime"]["visual_inspection"]
check("modal and Julia screenshots no tofu", visual["load_confirmation_no_tofu"] and visual["julia_before_no_tofu_and_visible"] and visual["julia_after_no_tofu_and_visible"])

staging = runtime["staging_install_restore"]
check("staging install pass", staging["install"]["pass"] and staging["install"]["marker_version"] == "1.2.2")
check("staging single plugin/cache removed", staging["install"]["plugin_dll_count"] == 1 and staging["install"]["stale_cache_removed"])
check("staging restore pass", staging["restore"]["pass"] and staging["restore"]["marker_removed"] and staging["restore"]["bepinex_removed"])

plugin_root = PACKAGE / "patch/BepInEx/plugins"
plugin_files = sorted(path.relative_to(plugin_root).as_posix() for path in plugin_root.rglob("*.dll"))
check("package recursively has one safe plugin", plugin_files == ["BigDipperKoreanSafe.dll"])
check("payload plugin hash", sha256(plugin_root / "BigDipperKoreanSafe.dll") == manifest["plugin_sha256"])
check("payload resources hash", sha256(PACKAGE / "patch/Big Dipper_Data/resources.assets") == manifest["patched_resources_sha256"])
check("payload shared hash", sha256(PACKAGE / "patch/Big Dipper_Data/sharedassets1.assets") == manifest["patched_sharedassets1_sha256"])
check("installer/restorer UTF-8 BOM", (PACKAGE / "\uc124\uce58.ps1").read_bytes().startswith(b"\xef\xbb\xbf") and (PACKAGE / "\uc81c\uac70.ps1").read_bytes().startswith(b"\xef\xbb\xbf"))
readme = (PACKAGE / "README.md").read_text(encoding="utf-8-sig")
check("README version and fixed hooks", "1.2.2" in readme and "DialogueManager.set_outputChar" in readme)
check("diagnostic executables absent from package", not any(path.name in {"HarmonyPatchSmoke.exe", "ListStrings.exe"} for path in PACKAGE.rglob("*")))
check("verification DLL absent from package", not any("verification" in path.name.lower() for path in PACKAGE.rglob("*.dll")))

payload = manifest["payload_files"]
distribution = manifest["distribution_files"]
package_actual = {
    path.relative_to(PACKAGE).as_posix()
    for path in PACKAGE.rglob("*")
    if path.is_file() and path.name != "manifest.json"
}
check("all 46 distribution files declared", len(distribution) == 46 and package_actual == set(distribution))
check("payload set equals package patch set", {f"patch/{relative}" for relative in payload} == {name for name in distribution if name.startswith("patch/")})
check("payload hashes equal distribution contract", all(distribution.get(f"patch/{relative}") == expected for relative, expected in payload.items()))
check("all package distribution hashes", all(sha256(PACKAGE / Path(relative)) == expected for relative, expected in distribution.items()))

zip_hash = sha256(ZIP)
expected_sidecar = f"{zip_hash}  {ZIP.name}"
check("ZIP sidecar hash and filename", SIDE.read_text(encoding="ascii").splitlines() == [expected_sidecar])
expected_zip_names = {"manifest.json", *distribution}
with zipfile.ZipFile(ZIP) as archive:
    infos = [info for info in archive.infolist() if not info.is_dir()]
    names = [info.filename for info in infos]
    check("ZIP path traversal absent", all(not Path(name).is_absolute() and ".." not in Path(name).parts for name in names))
    check("ZIP duplicate members absent", len(names) == len(set(names)))
    check("ZIP symlinks absent", all(((info.external_attr >> 16) & 0o170000) != stat.S_IFLNK for info in infos))
    check("ZIP exact current package member set", len(names) == 47 and set(names) == expected_zip_names)
    check("ZIP manifest byte-identical to current package", archive.read("manifest.json") == manifest_bytes)
    zmanifest = json.loads(archive.read("manifest.json").decode("utf-8-sig"))
    check("ZIP manifest version", zmanifest["patch_version"] == "1.2.2")
    check("ZIP manifest contract equals current package", zmanifest == manifest)
    check("all ZIP hashes match current package manifest", all(zip_sha256(archive, relative) == expected for relative, expected in distribution.items()))
    zip_plugins = sorted(name[len("patch/BepInEx/plugins/"):] for name in names if name.lower().startswith("patch/bepinex/plugins/") and name.lower().endswith(".dll"))
    check("ZIP recursively has one safe plugin", zip_plugins == ["BigDipperKoreanSafe.dll"])
    check("ZIP runtime proof present", all(name in set(names) for name in ("quality/runtime/julia-before-reveal.png", "quality/runtime/julia-after-reveal.png", "quality/runtime/load-confirmation.png")))

marker = json.loads((GAME / ".bigdipper-korean-installed").read_text(encoding="utf-8-sig"))
live_plugin_root = GAME / "BepInEx/plugins"
live_plugins = sorted(path.relative_to(live_plugin_root).as_posix() for path in live_plugin_root.rglob("*.dll"))
live_bepinex_dlls = sorted(path.relative_to(GAME).as_posix() for path in (GAME / "BepInEx").rglob("*.dll"))
expected_bepinex_dlls = sorted(relative for relative in payload if relative.lower().startswith("bepinex/") and relative.lower().endswith(".dll"))
check("live marker 1.2.2", marker["version"] == "1.2.2")
check("live game build identity", sha256(GAME / "Big Dipper.exe") == manifest["build_identity"]["game_exe_sha256"] and sha256(GAME / "Big Dipper_Data/Managed/Assembly-CSharp.dll") == manifest["build_identity"]["assembly_csharp_sha256"])
check("live complete payload hashes", all((GAME / Path(relative)).is_file() and sha256(GAME / Path(relative)) == expected for relative, expected in payload.items()))
check("live resources/shared hashes", sha256(GAME / "Big Dipper_Data/resources.assets") == manifest["patched_resources_sha256"] and sha256(GAME / "Big Dipper_Data/sharedassets1.assets") == manifest["patched_sharedassets1_sha256"])
check("live plugin hash", sha256(live_plugin_root / "BigDipperKoreanSafe.dll") == manifest["plugin_sha256"])
check("live recursively has only safe plugin", live_plugins == ["BigDipperKoreanSafe.dll"])
check("live has no unexpected BepInEx executable DLLs", live_bepinex_dlls == expected_bepinex_dlls)
check("live BepInEx cache absent", not (GAME / "BepInEx/cache").exists())
check("live verifier absent", not any("verification" in path.name.lower() for path in live_plugin_root.rglob("*.dll")))
check("original backups valid", sha256(GAME / "_KoreanPatchBackup/resources.assets") == manifest["original_resources_sha256"] and sha256(GAME / "_KoreanPatchBackup/sharedassets1.assets") == manifest["original_sharedassets1_sha256"])

failed = [name for name, result in checks if not result]
for index, (name, result) in enumerate(checks, 1):
    print("{:02d} {} {}".format(index, "PASS" if result else "FAIL", name))
print("TOTAL={} PASS={} FAIL={}".format(len(checks), len(checks) - len(failed), len(failed)))
print("ZIP_SHA256={}".format(zip_hash))
if failed:
    raise SystemExit(1)
