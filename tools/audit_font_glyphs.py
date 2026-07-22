from __future__ import print_function

from collections import defaultdict
from hashlib import sha256
from pathlib import Path
import json
import sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / "python_pkgs"))

import UnityPy
from PIL import ImageFont
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

GAME_DATA = Path(r"P:\SteamLibrary\steamapps\common\Big Dipper\WIN\Big Dipper_Data")
ORIGINAL = GAME_DATA.parent / "_KoreanPatchBackup" / "sharedassets1.assets"
PATCHED = BASE.parent / "outputs" / "BigDipper_Korean_Patch" / "patch" / "Big Dipper_Data" / "sharedassets1.assets"
FONT = BASE / "font" / "NotoSansCJKkr-Medium.otf"
TARGETS = "戏选员设茱莉亚母亲女孩安德鲁尼古拉斯加载所存档是否新游戏载入画廊制作人员退出主菜单窗口化停止当然뉴텍릭가힣"


def load_font_asset(path):
    generator = TypeTreeGenerator("2018.3.3f1")
    generator.load_local_dll_folder(str(GAME_DATA / "Managed"))
    nodes = generator.get_nodes_up("TextMeshPro-2017.3-Runtime.dll", "TMPro.TMP_FontAsset")
    env = UnityPy.load(str(path))
    objects = {obj.path_id: obj for obj in env.objects}
    data = objects[644].read_typetree(nodes)
    glyphs = {int(glyph["id"]): glyph for glyph in data["m_glyphInfoList"]}
    return data, glyphs


def mask_fingerprint(font, char):
    mask = font.getmask(char)
    return (mask.size, sha256(bytes(mask)).hexdigest())


def main():
    source_font = ImageFont.truetype(str(FONT), 64)
    notdef = mask_fingerprint(source_font, chr(0x10FFFF))
    replacement = mask_fingerprint(source_font, "�")
    report = {
        "targets": [],
        "notdef_fingerprint": notdef,
        "replacement_fingerprint": replacement,
    }

    loaded = {}
    for label, path in (("original", ORIGINAL), ("patched", PATCHED)):
        _, glyphs = load_font_asset(path)
        loaded[label] = glyphs
        report[label + "_glyph_count"] = len(glyphs)

    rectangles = defaultdict(list)
    for char in TARGETS:
        code = ord(char)
        source_fp = mask_fingerprint(source_font, char)
        row = {
            "char": char,
            "codepoint": "U+{:04X}".format(code),
            "source_font_notdef": source_fp == notdef,
            "source_font_replacement": source_fp == replacement,
            "original_present": code in loaded["original"],
            "patched_present": code in loaded["patched"],
        }
        if code in loaded["patched"]:
            glyph = loaded["patched"][code]
            rect = tuple(float(glyph[key]) for key in ("x", "y", "width", "height", "xAdvance"))
            row["patched_metrics"] = rect
            rectangles[rect].append(char)
        report["targets"].append(row)

    report["duplicate_metric_groups"] = [
        {"chars": "".join(chars), "metrics": metrics}
        for metrics, chars in rectangles.items()
        if len(chars) > 1
    ]
    output = BASE / "font" / "glyph-target-audit.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    # The report file is authoritative; console output stays ASCII so Windows
    # cp949 terminals never turn a successful audit into a GUI crash/error.
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
