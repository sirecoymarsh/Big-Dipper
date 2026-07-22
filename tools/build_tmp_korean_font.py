from pathlib import Path
import json, sys, unicodedata, hashlib
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'python_pkgs'))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt
import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

GAME=Path(r'P:\SteamLibrary\steamapps\common\Big Dipper\WIN\Big Dipper_Data')
SRC=GAME.parent/'_KoreanPatchBackup/sharedassets1.assets'
OUT=BASE.parent/'outputs/BigDipper_Korean_Patch/patch/Big Dipper_Data/sharedassets1.assets'
PREVIEW=BASE/'font/korean-sdf-atlas.png'
FONT_PATH=BASE/'font/NotoSansCJKkr-Medium.otf'
FONT_LICENSE=BASE/'font/OFL-NotoSansCJK.txt'
TEXT_PATH=BASE/'translation/Text3_Korean_v2.txt'
PLUGIN_SOURCE=BASE/'BigDipperKoreanSafe.cs'
ATLAS_SIZE=4096
POINT_SIZE=64
PADDING=4
FONT_ASSET_ID=644
ATLAS_TEX_ID=51
MATERIAL_ID=13

gen=TypeTreeGenerator('2018.3.3f1')
gen.load_local_dll_folder(str(GAME/'Managed'))
nodes=gen.get_nodes_up('TextMeshPro-2017.3-Runtime.dll','TMPro.TMP_FontAsset')
env=UnityPy.load(str(SRC))
objs={o.path_id:o for o in env.objects}
font_obj=objs[FONT_ASSET_ID]
original_font=font_obj.read_typetree(nodes)
original_glyph_ids={int(g['id']) for g in original_font['m_glyphInfoList']}
original_glyph_chars=''.join(chr(code) for code in sorted(original_glyph_ids)
                             if 0 <= code <= 0x10FFFF and not 0xD800 <= code <= 0xDFFF)

# Preserve every glyph shipped in the original Simplified-Chinese TMP asset as
# well as every character emitted by the Korean script and runtime hook.  The
# plugin source is intentionally used instead of a hand-maintained extra list:
# every new menu/modal/speaker literal automatically enters the font contract.
script_text=TEXT_PATH.read_text(encoding='utf-8')
plugin_text=PLUGIN_SOURCE.read_text(encoding='utf-8')
text=script_text+plugin_text+original_glyph_chars
chars=sorted({c for c in text if not unicodedata.category(c).startswith('C')})
font=ImageFont.truetype(str(FONT_PATH),POINT_SIZE)
ascender,descender=font.getmetrics()

def metrics(ch):
    b=font.getbbox(ch,anchor='ls')
    if b is None: b=(0,0,0,0)
    x0,y0,x1,y1=b
    return x0,y0,max(0,x1-x0),max(0,y1-y0),float(font.getlength(ch))

items=[]
for ch in chars:
    x0,y0,w,h,adv=metrics(ch)
    items.append((ch,x0,y0,w,h,adv))
# Pack tallest first into shelves; coordinates are PIL/TMP top-left atlas coordinates.
items.sort(key=lambda z:(-(z[4]+2*PADDING),ord(z[0])))
atlas=Image.new('L',(ATLAS_SIZE,ATLAS_SIZE),0)
x=y=row_h=0
packed={}
for ch,x0,y0,w,h,adv in items:
    if w==0 or h==0:
        packed[ch]=(0,0,x0,y0,w,h,adv)
        continue
    pw,ph=w+2*PADDING,h+2*PADDING
    if x+pw>ATLAS_SIZE:
        x=0; y+=row_h; row_h=0
    if y+ph>ATLAS_SIZE:
        raise RuntimeError(f'Atlas overflow at U+{ord(ch):04X}; y={y}, h={ph}')
    mask=Image.new('L',(pw,ph),0)
    d=ImageDraw.Draw(mask)
    d.text((PADDING-x0,PADDING-y0),ch,font=font,fill=255,anchor='ls')
    a=np.asarray(mask,dtype=np.uint8)
    inside=a>=128
    if inside.any():
        signed=distance_transform_edt(inside)-distance_transform_edt(~inside)
        sdf=np.clip(128.0+signed*(127.0/PADDING),0,255).astype(np.uint8)
    else:
        sdf=np.zeros_like(a)
    atlas.paste(Image.fromarray(sdf,'L'),(x,y))
    packed[ch]=(x+PADDING,y+PADDING,x0,y0,w,h,adv)
    x+=pw; row_h=max(row_h,ph)
used_h=y+row_h

PREVIEW.parent.mkdir(parents=True,exist_ok=True)
atlas.save(PREVIEW)

d=original_font
glyphs=[]
for ch in sorted(chars,key=ord):
    gx,gy,x0,y0,w,h,adv=packed[ch]
    glyphs.append({
        'id':ord(ch),'x':float(gx),'y':float(gy),'width':float(w),'height':float(h),
        'xOffset':float(x0),'yOffset':float(-y0),'xAdvance':float(adv),'scale':1.0
    })
d['m_Name']='NotoSansCJKkr-Medium SDF'
d['m_glyphInfoList']=glyphs
d['m_fontInfo'].update({
    'Name':'Noto Sans CJK KR Medium','PointSize':float(POINT_SIZE),'Scale':1.0,
    'CharacterCount':len(glyphs),'LineHeight':float(ascender+descender),
    'Baseline':0.0,'Ascender':float(ascender),'CapHeight':float(ascender),
    'Descender':float(-descender),'CenterLine':0.0,
    'SuperscriptOffset':float(ascender),'SubscriptOffset':float(-descender/2),
    'SubSize':0.5,'Underline':float(-max(1,descender/2)),'UnderlineThickness':2.0,
    'strikethrough':float(ascender*0.3),'strikethroughThickness':2.0,
    'TabWidth':float(font.getlength(' ')*4),'Padding':float(PADDING),
    'AtlasWidth':float(ATLAS_SIZE),'AtlasHeight':float(ATLAS_SIZE)
})
font_obj.save_typetree(d,nodes)
material_obj=objs[MATERIAL_ID]
material=material_obj.read_typetree()
floats=[]
for key,value in material['m_SavedProperties']['m_Floats']:
    if key in ('_TextureWidth','_TextureHeight'):
        value=float(ATLAS_SIZE)
    elif key=='_GradientScale':
        value=float(PADDING+1)
    floats.append((key,value))
material['m_SavedProperties']['m_Floats']=floats
material['m_Name']='NotoSansCJKkr-Medium SDF Material'
material_obj.save_typetree(material)
tex=objs[ATLAS_TEX_ID].read()
rgba=Image.new('RGBA',atlas.size,(255,255,255,255))
rgba.putalpha(atlas)
tex.set_image(rgba,target_format=1,mipmap_count=1)
tex.m_IsReadable=False
tex.save()
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_bytes(env.file.save())
report={
 'font_source':str(FONT_PATH),'font_asset_path_id':FONT_ASSET_ID,'atlas_texture_path_id':ATLAS_TEX_ID,
 'material_path_id':MATERIAL_ID,'gradient_scale':PADDING+1,
 'font_name':'Noto Sans CJK KR Medium','font_weight':500,
 'point_size':POINT_SIZE,'padding':PADDING,'material_texture_size':[ATLAS_SIZE,ATLAS_SIZE],
 'glyph_count':len(glyphs),'required_character_count':len(chars),'missing_required_glyphs':0,
 'required_sources':['translation/Text3_Korean_v2.txt','BigDipperKoreanSafe.cs','original TMP glyph IDs'],
 'plugin_unique_characters':len({c for c in plugin_text if not unicodedata.category(c).startswith('C')}),
 'plugin_missing_codepoints_after_build':[f'U+{ord(c):04X}' for c in sorted(set(plugin_text))
                                          if not unicodedata.category(c).startswith('C') and c not in packed],
 'original_glyph_count':len(original_glyph_ids),'original_glyphs_preserved':len(original_glyph_ids & {ord(c) for c in chars}),
 'hangul_syllables':sum(0xAC00<=ord(c)<=0xD7A3 for c in chars),
 'atlas_size':[ATLAS_SIZE,ATLAS_SIZE],'atlas_used_height':used_h,
 'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),
 'patched_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),
 'font_source_sha256':hashlib.sha256(FONT_PATH.read_bytes()).hexdigest(),
 'license':'SIL Open Font License 1.1','license_file':str(FONT_LICENSE),
 'license_sha256':hashlib.sha256(FONT_LICENSE.read_bytes()).hexdigest(),
 'preview':str(PREVIEW)
}
(BASE/'font/font-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))

