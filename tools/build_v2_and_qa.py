import json,re,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
source_text=(BASE/'inspection/textassets/resources.assets/128_Text2.txt').read_text(encoding='utf-8-sig')
# Split only on LF so the source's two terminal newlines are preserved exactly.
src=source_text.split('\n')
records=json.loads((BASE/'translation/translation.json').read_text(encoding='utf-8'))
final=json.loads((BASE/'translation/v2_final.json').read_text(encoding='utf-8'))
final={str(k):str(v).strip() for k,v in final.items()}
errors=[];warnings=[]
for r in records:
    k=str(r['line']);ko=final.get(k,'')
    if not ko:errors.append((k,'missing','')) ;continue
    if re.search(r'[\u4e00-\u9fff\u3040-\u30ff]',ko):errors.append((k,'CJK leakage',ko))
    if re.search(r'(?i)\b(narration|translation|translate|target ids|draft_ko)\b',ko):errors.append((k,'meta leakage',ko))
    if re.match(r'^\s*\[?\d+\]?[\s:.-]',ko):warnings.append((k,'leading id',ko))
    if len(ko)<2 and len(r['source'])>12:warnings.append((k,'suspiciously short',ko))
    if len(ko)>max(120,len(r['source'])*4):warnings.append((k,'suspiciously long',ko))
    # English sentence leakage, excluding short interjections/proper names.
    if len(re.findall(r'\b[A-Za-z]{3,}\b',ko))>=4:warnings.append((k,'English leakage',ko))
# Preserve all non-translatable control lines byte-for-byte except newline normalization.
out=src[:]
for r in records:out[r['line']-1]=r['prefix']+final[str(r['line'])]
dest=BASE/'translation/Text3_Korean_v2.txt'
dest.write_text('\n'.join(out),encoding='utf-8',newline='\n')
# Command integrity gate.
for i,(a,b) in enumerate(zip(src,out),1):
    if a.startswith('!') and a!=b:errors.append((str(i),'command changed',b))
report={'records':len(records),'final':len(final),'errors':errors,'warnings':warnings,'output':str(dest)}
(BASE/'translation/v2_qa_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'records':len(records),'final':len(final),'errors':len(errors),'warnings':len(warnings),'output':str(dest)},ensure_ascii=False))
if errors:sys.exit(2)
