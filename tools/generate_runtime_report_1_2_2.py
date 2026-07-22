from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
RUNTIME = ROOT / "outputs" / "BigDipper_Korean_Patch" / "quality" / "runtime"
RUNTIME.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy(source: Path, name: str) -> Path:
    target = RUNTIME / name
    shutil.copy2(source, target)
    return target


for stale in (
    "clean-launch-log.txt", "load.png", "main-menu.png", "probe-log.txt",
    "runtime-report.json", "save.png", "settings.png", "speaker-immediate.png",
    "story.png",
):
    path = RUNTIME / stale
    if path.exists():
        path.unlink()

log_source = BASE / "verification122-runtime.log"
log_text = log_source.read_text(encoding="utf-8")
log_target = copy(log_source, "verification122-log.txt")

screens = {
    "startup_splash": copy(BASE / "BigDipperKorean-verify122-main-menu.png", "startup-splash.png"),
    "load_confirmation": copy(BASE / "BigDipperKorean-verify122-load-confirmation.png", "load-confirmation.png"),
    "julia_before_reveal": copy(BASE / "BigDipperKorean-verify122-julia-before.png", "julia-before-reveal.png"),
    "julia_after_reveal": copy(BASE / "BigDipperKorean-verify122-julia-after.png", "julia-after-reveal.png"),
}

checks = []
for line in log_text.splitlines():
    marker = "VERIFY122|CHECK|"
    if marker not in line:
        continue
    payload = line.split(marker, 1)[1]
    parts = payload.split("|")
    checks.append({
        "label": parts[0],
        "pass": parts[1].lower() == "pass=true",
        "detail": "|".join(parts[2:]),
    })

font = json.loads((BASE / "font" / "font-report.json").read_text(encoding="utf-8"))
glyph_audit = json.loads((BASE / "font" / "glyph-target-audit.json").read_text(encoding="utf-8"))
staging = json.loads((BASE / "staging-1.2.2.json").read_text(encoding="utf-8"))
live = json.loads((BASE / "live-final-state-1.2.2.json").read_text(encoding="utf-8"))

screen_report = {}
for label, path in screens.items():
    with Image.open(path) as image:
        screen_report[label] = {
            "file": path.relative_to(ROOT / "outputs" / "BigDipper_Korean_Patch").as_posix(),
            "sha256": sha256(path),
            "size": list(image.size),
        }

required_target_chars = "戏选员设茱莉亚母亲女孩安德鲁尼古拉斯加载所存档是否新游戏载入画廊制作人员退出主菜单窗口化停止当然뉴텍릭"
rows = {row["char"]: row for row in glyph_audit["targets"]}
target_font_pass = all(
    char in rows and rows[char]["patched_present"] and not rows[char]["source_font_notdef"]
    for char in set(required_target_chars)
)

report = {
    "schema_version": 2,
    "patch_version": "1.2.2",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "runtime": {
        "unity": "2018.3.3f1",
        "bepinex": "5.4.23.5",
        "verification_complete": "VERIFY122|COMPLETE|pass=True|failures=0" in log_text,
        "check_count": len(checks),
        "failed_checks": [check for check in checks if not check["pass"]],
        "error_lines": len(re.findall(r"\[Error", log_text)),
        "warning_lines": len(re.findall(r"\[Warning", log_text)),
        "exception_mentions": len(re.findall(r"Exception", log_text)),
        "hook_failure_mentions": len(re.findall(r"hook failed", log_text, re.IGNORECASE)),
        "startup_hooks": {
            "speaker_setter": "Hook installed: DialogueManager.set_outputChar" in log_text,
            "game_text_writers": "Direct game text writer hooks installed: 7" in log_text,
            "tmp_setter": "Hook installed: TMP_Text.set_text" in log_text,
            "tmp_on_enable": "Hook installed: TextMeshProUGUI.OnEnable" in log_text,
            "initialization_completed": "Korean script slot selected safely (language 2)" in log_text,
        },
        "menu": {
            "korean_labels_active": all(
                any(check["label"] == "MAIN_MENU_LABEL_{}".format(i) and check["pass"] for check in checks)
                for i in range(6)
            ),
            "old_chinese_labels_absent": all(
                any(check["label"] == "MAIN_MENU_OLD_LABEL_{}".format(i) and check["pass"] for check in checks)
                for i in range(6)
            ),
            "korean_description_present": any(check["label"] == "MENU_DESCRIPTION_KOREAN" and check["pass"] for check in checks),
            "russian_description_absent": any(check["label"] == "MENU_DESCRIPTION_RUSSIAN_GONE" and check["pass"] for check in checks),
        },
        "load_confirmation": {
            "question": "선택한 저장 파일을 불러올까요?",
            "question_pass": any(check["label"] == "LOAD_QUESTION" and check["pass"] for check in checks),
            "yes_pass": any(check["label"] == "LOAD_YES" and check["pass"] for check in checks),
            "no_pass": any(check["label"] == "LOAD_NO" and check["pass"] for check in checks),
            "actual_game_writer_hook_observed": "加载所选存档？ -> 선택한 저장 파일을 불러올까요?" in log_text,
        },
        "julia": {
            "before_source_actual_parser_line": any(check["label"] == "SOURCE_BEFORE_REVEAL" and check["pass"] for check in checks),
            "before_visible_name": "소녀",
            "before_pass": any(check["label"] == "SPEAKER_BEFORE_REVEAL" and check["pass"] for check in checks),
            "after_source_actual_parser_line": any(check["label"] == "SOURCE_AFTER_REVEAL" and check["pass"] for check in checks),
            "after_actual_forced_chinese_token": "茱莉亚",
            "after_visible_name": "줄리아",
            "after_pass": any(check["label"] == "SPEAKER_AFTER_REVEAL" and check["pass"] for check in checks),
        },
        "checks": checks,
        "log": {
            "file": log_target.relative_to(ROOT / "outputs" / "BigDipper_Korean_Patch").as_posix(),
            "sha256": sha256(log_target),
        },
        "screenshots": screen_report,
        "visual_inspection": {
            "load_confirmation_no_tofu": True,
            "julia_before_no_tofu_and_visible": True,
            "julia_after_no_tofu_and_visible": True,
            "startup_capture_note": "Splash overlay was still visible; active menu labels and description are proven by the runtime object checks and hook log, not by this frame.",
        },
    },
    "font": {
        "name": font["font_name"],
        "glyph_count": font["glyph_count"],
        "original_glyphs_preserved": font["original_glyphs_preserved"],
        "plugin_missing_codepoints_after_build": font["plugin_missing_codepoints_after_build"],
        "target_korean_cjk_glyphs_present_and_not_notdef": target_font_pass,
        "atlas_size": font["atlas_size"],
        "point_size": font["point_size"],
        "padding": font["padding"],
        "gradient_scale": font["gradient_scale"],
        "source_sha256": font["font_source_sha256"],
        "patched_sharedassets1_sha256": font["patched_sha256"],
    },
    "staging_install_restore": staging,
    "live_final_state": live,
}

report["overall_pass"] = all((
    report["runtime"]["verification_complete"],
    not report["runtime"]["failed_checks"],
    report["runtime"]["error_lines"] == 0,
    report["runtime"]["warning_lines"] == 0,
    report["runtime"]["exception_mentions"] == 0,
    report["runtime"]["hook_failure_mentions"] == 0,
    all(report["runtime"]["startup_hooks"].values()),
    all(report["runtime"]["menu"].values()),
    all(value for key, value in report["runtime"]["load_confirmation"].items() if key.endswith("pass") or key.startswith("actual_")),
    report["runtime"]["julia"]["before_pass"],
    report["runtime"]["julia"]["after_pass"],
    target_font_pass,
    staging["install"]["pass"],
    staging["restore"]["pass"],
    live["game_running"] is False,
    live["cache_exists"] is False,
    live["verification122_present"] is False,
    len(live["plugins"]) == 1,
    live["plugins"][0]["name"] == "BigDipperKoreanSafe.dll",
))

output = RUNTIME / "runtime-report.json"
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "output": str(output),
    "overall_pass": report["overall_pass"],
    "checks": len(checks),
    "failed_checks": len(report["runtime"]["failed_checks"]),
    "screenshots": len(screens),
}, ensure_ascii=True, indent=2))
