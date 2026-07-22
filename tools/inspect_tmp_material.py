from pathlib import Path
import json, sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / "python_pkgs"))
import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

GAME = Path(r"P:\SteamLibrary\steamapps\common\Big Dipper\WIN\Big Dipper_Data")
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else GAME.parent / "_KoreanPatchBackup/sharedassets1.assets"
gen = TypeTreeGenerator("2018.3.3f1")
gen.load_local_dll_folder(str(GAME / "Managed"))
nodes = gen.get_nodes_up("TextMeshPro-2017.3-Runtime.dll", "TMPro.TMP_FontAsset")
env = UnityPy.load(str(SRC))
objects = {obj.path_id: obj for obj in env.objects}
font = objects[644].read_typetree(nodes)

def simplify(value):
    if isinstance(value, dict):
        return {k: simplify(v) for k, v in value.items()}
    if isinstance(value, list):
        return [simplify(v) for v in value] if len(value) <= 60 else f"<list {len(value)}>"
    if isinstance(value, (bytes, bytearray)):
        return f"<bytes {len(value)}>"
    return value

print("FONT KEYS")
print(json.dumps(simplify(font), ensure_ascii=False, indent=2))
for key, value in font.items():
    if isinstance(value, dict) and "m_PathID" in value and value["m_PathID"]:
        path_id = value["m_PathID"]
        obj = objects.get(path_id)
        if obj:
            print(f"\nREFERENCE {key} -> {path_id} {obj.type.name}")
            try:
                print(json.dumps(simplify(obj.read_typetree()), ensure_ascii=False, indent=2))
            except Exception as exc:
                print(type(exc).__name__, exc)
