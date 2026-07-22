from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "outputs" / "BigDipper_Korean_Patch"
ZIP = ROOT / "outputs" / "BigDipper_Korean_Patch_1.2.2.zip"
SIDE = ZIP.with_suffix(ZIP.suffix + ".sha256.txt")
FIXED_ZIP_TIME = (2026, 7, 21, 18, 49, 22)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_link_or_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_flag)


manifest_path = PACKAGE / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
if manifest.get("patch_version") != "1.2.2":
    raise SystemExit("Refusing to package a manifest that is not version 1.2.2")

expected_hashes = manifest.get("distribution_files", {})
expected_names = {"manifest.json", *expected_hashes}
actual_names = {
    path.relative_to(PACKAGE).as_posix()
    for path in PACKAGE.rglob("*")
    if path.is_file()
}
if actual_names != expected_names:
    missing = sorted(expected_names - actual_names)
    extra = sorted(actual_names - expected_names)
    raise SystemExit(f"Package file-set mismatch; missing={missing!r} extra={extra!r}")

for path in PACKAGE.rglob("*"):
    if is_link_or_reparse(path):
        raise SystemExit(f"Refusing link/reparse-point input: {path}")

for relative, expected in expected_hashes.items():
    actual = sha256(PACKAGE / Path(relative))
    if actual != expected:
        raise SystemExit(f"Package hash mismatch: {relative}: {actual} != {expected}")

if ZIP.exists():
    ZIP.unlink()

files = [PACKAGE / Path(relative) for relative in sorted(expected_names)]
with zipfile.ZipFile(ZIP, "w") as archive:
    for path in files:
        relative = path.relative_to(PACKAGE).as_posix()
        info = zipfile.ZipInfo(relative, date_time=FIXED_ZIP_TIME)
        info.compress_type = zipfile.ZIP_DEFLATED
        info._compresslevel = 9
        info.create_system = 3
        info.external_attr = (stat.S_IFREG | 0o644) << 16
        with path.open("rb") as source, archive.open(info, "w") as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)

digest = sha256(ZIP)
SIDE.write_text(f"{digest}  {ZIP.name}\n", encoding="ascii", newline="\n")
print(f"ZIP={ZIP}")
print(f"FILES={len(files)}")
print(f"SHA256={digest}")
