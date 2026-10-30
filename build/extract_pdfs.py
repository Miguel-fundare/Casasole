import subprocess, os, sys, glob, json, re
from PIL import Image
src, tmp, out = sys.argv[1:4]
res=[]
for pdf in sorted(glob.glob(os.path.join(src,'*.pdf'))):
    base=os.path.basename(pdf)[:-4]
    # list images
    try:
        lst=subprocess.run(['pdfimages','-list',pdf],capture_output=True,text=True,timeout=60).stdout
    except Exception as e:
        print('ERR list',base,e); continue
    big=[]
    for line in lst.splitlines()[2:]:
        p=line.split()
        if len(p)<5: continue
        try: page,num,typ,w,h=int(p[0]),int(p[1]),p[2],int(p[3]),int(p[4])
        except: continue
        if typ=='image' and min(w,h)>=300: big.append((page,num,w,h))
    if not big: 
        res.append(dict(pdf=base,n=0)); continue
    d=os.path.join(tmp,base); os.makedirs(d,exist_ok=True)
    subprocess.run(['pdfimages','-j','-p',pdf,os.path.join(d,'i')],capture_output=True,timeout=120)
    k=0
    for page,num,w,h in big:
        cands=glob.glob(os.path.join(d,f'i-{page:03d}-{num:03d}.*'))
        if not cands: continue
        try:
            im=Image.open(cands[0]).convert('RGB'); im.thumbnail((512,512))
            k+=1; name=f'{base}_p{page:02d}_{k:02d}.jpg'
            im.save(os.path.join(out,name),quality=85)
        except Exception as e:
            print('ERR img',base,cands[0],e)
    res.append(dict(pdf=base,n=k))
    print(base,k,flush=True)
json.dump(res,open(os.path.join(os.path.dirname(out),'pdf_extract.json'),'w'),indent=0)
print('TOTAL',sum(r['n'] for r in res))
