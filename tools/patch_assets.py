import hashlib, json, shutil, sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/"python_pkgs"))
import UnityPy

src=Path(r"P:\SteamLibrary\steamapps\common\Big Dipper\WIN\_KoreanPatchBackup\resources.assets")
outdir=BASE.parent/"outputs/BigDipper_Korean_Patch"
data_dir=outdir/"patch/Big Dipper_Data"
data_dir.mkdir(parents=True,exist_ok=True)
dest=data_dir/"resources.assets"
raw=(BASE/"translation/Text3_Korean_v2.txt").read_bytes()

env=UnityPy.load(str(src))
found=False
for obj in env.objects:
    if obj.type.name=="TextAsset" and obj.path_id==125:
        data=obj.read()
        if getattr(data,"m_Name","")!="Text3":raise RuntimeError("Path ID 125 is not Text3")
        data.m_Script=raw.decode("utf-8") if isinstance(data.m_Script,str) else raw
        data.save()
        found=True
if not found:raise RuntimeError("Text3 asset not found")
dest.write_bytes(env.file.save())

manifest={
 "game":"Big Dipper","target":"Windows / Unity 2018.3.3f1","language_slot":"Simplified Chinese (Text3)",
 "original_resources_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),
 "patched_resources_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
 "text_asset_path_id":125,"text_asset_name":"Text3","translated_lines":1408
}
(outdir/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(manifest,ensure_ascii=False,indent=2))
