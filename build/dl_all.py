import json, os, sys, urllib.request, re
from concurrent.futures import ThreadPoolExecutor, as_completed
src, outimg, outpdf = sys.argv[1], sys.argv[2], sys.argv[3]
live = json.load(open(src))['records']
A,D,F = 'fld1Tj1mxvWRTr6a5','fldWp6D8eQWQLwY6q','fldrqPQnACrcZqN3U'
slots = {A:'antes', D:'despues', F:'fotos'}
jobs=[]; manifest=[]
for r in live:
    x = r['cellValuesByFieldId']; iid = x.get('fldEy33doqp0YIVCo')
    for k,slot in slots.items():
        for n,a in enumerate(x.get(k) or [], start=1):
            t = a.get('type','')
            ext = 'jpg' if t.startswith('image') else ('pdf' if t=='application/pdf' else 'bin')
            if t.startswith('video'):
                manifest.append(dict(id=iid, slot=slot, n=n, kind='video', filename=a.get('filename'), path=None)); continue
            if ext=='jpg':
                url = (a.get('thumbnails') or {}).get('large',{}).get('url') or a['url']
                path = os.path.join(outimg, f"{iid}_{slot}_{n:02d}.jpg")
                full = a['url']
            elif ext=='pdf':
                url = a['url']; path = os.path.join(outpdf, f"{iid}_{slot}_{n:02d}.pdf"); full=None
            else:
                manifest.append(dict(id=iid, slot=slot, n=n, kind='other', filename=a.get('filename'), path=None)); continue
            m = dict(id=iid, slot=slot, n=n, kind=ext, filename=a.get('filename'), path=path, full_url=full, w=a.get('width'), h=a.get('height'))
            manifest.append(m); jobs.append((url, path))
def get(url, path):
    if os.path.exists(path) and os.path.getsize(path)>0: return path, 'cached'
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as resp, open(path,'wb') as f:
        f.write(resp.read())
    return path, 'ok'
ok=err=0
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(get,u,p):(u,p) for u,p in jobs}
    for fu in as_completed(futs):
        try:
            fu.result(); ok+=1
        except Exception as e:
            err+=1; print('ERR', futs[fu][1], e, flush=True)
        if (ok+err)%50==0: print(f'{ok+err}/{len(jobs)}', flush=True)
json.dump(manifest, open(os.path.join(os.path.dirname(outimg),'manifest_all.json'),'w'), ensure_ascii=False, indent=0)
print('DONE ok',ok,'err',err,'manifest',len(manifest))
