# Datos maestros para el libro: incidencias + fotos + jornadas
import json, os, glob, re, sys
from collections import Counter, defaultdict
S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S)
from capitulos import CAP, EXCLUIR, ID2CAP, TITULOS

F = dict(id='fldEy33doqp0YIVCo', resumen='fldqIWpci8iQFrFiZ', tipo='fldZeRwtJkzZjlNPz', unidad='fldIcHLl6v3O6oZEn',
         accion='fldvUgIp53d8aFU65', reportado='fldmEs9KTRPRLcIB5', urgencia='fldQztKSsjUyCRNc5', estatus='fldeJztxd5wowS3JO',
         f_rep='fldMJ2Mi36qEIaAl0', f_cierre='fldDX4ZSONRGSd7Si', f_asig='fldQwxcoUbnvH2k3x', categoria='fldbnhlf3qXDcuQEb',
         desc='fldXpZTwzmnfvZk0m', proveedor='fldyoxeJ1fEWtlehl', horas='fld2Fng2JvrAn7i6H', evidencia='fldKO9zqIUHkG8kIt',
         t_res='fldbeZA6CuG3bBAqS', mes_cierre='fldoz6ZcBmkH8gqaF')
def nm(v):
    if isinstance(v, dict): return v.get('name')
    if isinstance(v, list): return [i.get('name') for i in v if isinstance(i, dict)]
    return v
def load_records(path):
    d = json.load(open(path)); recs = d.get('records', d) if isinstance(d, dict) else d
    return [r.get('cellValuesByFieldId', r.get('fields', {})) for r in recs]

def build():
    recs = load_records(os.path.join(S, 'amb_all_inc.json')) + load_records(os.path.join(S, 'todos_live.json'))
    INC = {}
    for x in recs:
        i = x.get(F['id'])
        if i in EXCLUIR or i is None: continue
        u = nm(x.get(F['unidad'])) or []
        INC[i] = dict(id=i, resumen=(x.get(F['resumen']) or '').strip(), desc=(x.get(F['desc']) or '').strip(),
                      unidades=u, tipo=nm(x.get(F['tipo'])), accion=nm(x.get(F['accion'])), categoria=nm(x.get(F['categoria'])),
                      reportado=nm(x.get(F['reportado'])), urgencia=nm(x.get(F['urgencia'])), estatus=nm(x.get(F['estatus'])) or 'Sin estatus',
                      f_rep=x.get(F['f_rep']), f_cierre=x.get(F['f_cierre']), f_asig=x.get(F['f_asig']),
                      proveedor=nm(x.get(F['proveedor'])) or [], horas=x.get(F['horas']), evidencia=x.get(F['evidencia']),
                      t_res=x.get(F['t_res']), cap=ID2CAP.get(i), fotos=[])
    # Estatus confirmados por Melany el 4-nov-2026 (Airtable aún no actualizado):
    OVERRIDE = {210: 'Terminado', 368: 'Terminado', 266: 'Terminado'}
    for i, st in OVERRIDE.items():
        if i in INC: INC[i]['estatus'] = st
    # fotos directas
    for p in sorted(glob.glob(os.path.join(S, 'fotos_all', '*.jpg'))):
        b = os.path.basename(p)[:-4]; i = int(b.split('_')[0])
        if i in INC: INC[i]['fotos'].append(b)
    # jornadas de Beto (bloques)
    det = load_records(os.path.join(S, 'detalle_all.json'))
    blocks = []
    for x in det:
        inc = x.get('fldgwFUDzHkfQrJZL'); incn = nm(inc) if inc else []
        ids = []
        for n in (incn or []):
            m = re.match(r'\s*#?(\d+)', str(n))
            if m: ids.append(int(m.group(1)))
        j = x.get('fldnvJUORklYht4B3'); jn = (nm(j) or [None])[0] if isinstance(j, list) else j
        u = nm(x.get('fldPPlUWz6IjZFXpM')) or []
        amb = any(i in INC for i in ids) or any('AMB' in str(s).upper() for s in u) or any(str(s)=='Todos' for s in u)
        blocks.append(dict(fecha=jn, horas=x.get('fldVfw2lntbHy5eQY') or 0, que=(x.get('fldRl3BvDYDBk9VQq') or '').strip(), ids=ids, unidades=u, amb=amb))
    return INC, blocks

if __name__ == '__main__':
    INC, blocks = build()
    print('incidencias:', len(INC), ' fotos directas:', sum(len(v['fotos']) for v in INC.values()))
    per = [v for v in INC.values() if v['f_rep'] and '2026-06-01' <= v['f_rep'] <= '2026-09-30']
    print('jun-sep:', len(per), Counter(v['f_rep'][:7] for v in per))
    print('estatus jun-sep:', Counter(v['estatus'] for v in per))
    print('reportado por (jun-sep):', Counter(v['reportado'] for v in per))
    print('categoria:', Counter(v['categoria'] for v in per).most_common())
    print('proveedor:', Counter(tuple(v['proveedor']) for v in per).most_common(6))
    cerr = [v for v in per if v['estatus'] in ('Terminado','Cerrada/Noprocede') and v['f_cierre'] and v['f_rep']]
    from datetime import date
    dias = [(date.fromisoformat(v['f_cierre'])-date.fromisoformat(v['f_rep'])).days for v in cerr]
    print('cerrados con fechas:', len(cerr), 'mismo dia:', sum(1 for d in dias if d==0), 'promedio dias:', round(sum(dias)/len(dias),1), 'mediana:', sorted(dias)[len(dias)//2])
    print('con antes y despues (jun-sep):', sum(1 for v in per if v['evidencia']=='✅ Completa'), 'con alguna foto:', sum(1 for v in per if v['fotos']))
    amb = [b for b in blocks if b['amb'] and b['fecha']]
    bym = defaultdict(float); 
    for b in amb: bym[str(b['fecha'])[:7]] += b['horas']
    print('horas Beto por mes (AMB):', {k: round(v,1) for k,v in sorted(bym.items())}, 'bloques', len(amb))
    dias_beto = sorted(set(str(b['fecha'])[:10] for b in amb))
    print('dias con jornada AMB:', len(dias_beto), ' jun-sep:', len([d for d in dias_beto if d<='2026-09-30']), ' oct:', len([d for d in dias_beto if d>'2026-09-30']))
    print('unidades:', Counter(u for v in per for u in v['unidades']).most_common())
    oct_ = [v for v in INC.values() if v['f_rep'] and v['f_rep']>='2026-10-01']
    print('octubre:', len(oct_), Counter(v['estatus'] for v in oct_))
    sinf = [v['id'] for v in INC.values() if not v['f_rep']]
    print('sin fecha:', sinf)
