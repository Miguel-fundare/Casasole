#!/usr/bin/env python3
"""Libro: Programa de renovación y operación Amberjack 2026 (junio–septiembre, y octubre en curso).
HTML autocontenido (fotos base64) a partir de las fotos descargadas de Airtable."""
import base64, io, os, sys, html, json, re
from datetime import date
from collections import Counter, defaultdict
from PIL import Image, ImageOps
S = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, S)
from web_css import CSS
from libro_data import build
from capitulos import CAP, TITULOS

SITE = os.path.join(S, 'docs'); os.makedirs(os.path.join(SITE, 'img'), exist_ok=True)
INC, BLOCKS = build()
import time
VER = time.strftime('%Y%m%d%H%M')
E = html.escape

# ------------------------------------------------------------------ fotos
_done = {}
def _src(name):
    for d in ('fotos_full2', 'fotos_all', 'fotos_pdf', 'inc462_dl/imgs'):
        p = os.path.join(S, d, name + '.jpg')
        if os.path.exists(p): return p
    raise FileNotFoundError(name)
def img_file(name, w, q=70):
    """Escribe site/img/{name}-{w}.webp (si no existe) y regresa (url, ancho real)."""
    key = (name, w)
    if key in _done: return _done[key]
    im = ImageOps.exif_transpose(Image.open(_src(name))).convert('RGB')
    if im.width > w:
        im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    out = os.path.join(SITE, 'img', f'{name}-{w}.webp')
    if not os.path.exists(out):
        im.save(out, 'WEBP', quality=q, method=4)
    _done[key] = (f'img/{name}-{w}.webp', im.width)
    return _done[key]
def img_tag(name, maxw, q=70, pos='center', eager=False, sizes=None, alt=''):
    srcw = ImageOps.exif_transpose(Image.open(_src(name))).width
    widths = sorted({min(maxw, srcw), min(maxw * 2, srcw)})
    files = [img_file(name, w, q) for w in widths]
    srcset = ', '.join(f'{u} {w}w' for u, w in files)
    sz = sizes or f'(max-width: 720px) 100vw, {maxw}px'
    load = 'eager' if eager else 'lazy'
    fp = ' fetchpriority="high"' if eager else ''
    return f'<img src="{files[0][0]}" srcset="{srcset}" sizes="{sz}" loading="{load}" decoding="async"{fp} alt="{E(alt)}" style="object-position:{pos}">'

def ph(name, tag=None, pos='center', maxw=560, q=66, eager=False, sizes=None):
    cls = {'Antes': 't-antes', 'Después': 't-despues'}.get(tag, 't-neutral')
    t = f'<span class="tag {cls}">{E(tag)}</span>' if tag else ''
    return f'<div class="ph">{img_tag(name, maxw, q, pos, eager, sizes, tag or "")}{t}</div>'

def pair(antes, despues, cap, pos_a='center', pos_d='center', cls='', maxw=560):
    return (f'<figure class="pair {cls}">{ph(antes,"Antes",pos_a,maxw)}{ph(despues,"Después",pos_d,maxw)}'
            f'<figcaption>{cap}</figcaption></figure>')

def strip(items, cap=None, cols=4, sq=False, maxw=320):
    """items: list of (name, label) or name"""
    cells = []
    for it in items:
        name, lab = (it if isinstance(it, tuple) else (it, None))
        pos = 'center'
        if isinstance(lab, tuple): lab, pos = lab
        cells.append(f'<div class="cell">{ph(name, None, pos, maxw)}' + (f'<div class="lab">{lab}</div>' if lab else '') + '</div>')
    c = {3: 'c3', 4: '', 5: 'c5', 6: 'c6'}[cols]
    return f'<div class="strip {c} {"sq" if sq else ""}">{"".join(cells)}' + (f'<div class="strip-cap">{cap}</div>' if cap else '') + '</div>'

def proj(titulo, meta, parrafos, visual, first=False, wide=None):
    text = ''.join(f'<p>{p}</p>' for p in parrafos)
    return (f'<div class="proj {"first" if first else ""}"><div class="text"><h3>{titulo}</h3><div class="meta">{meta}</div>{text}</div>'
            f'{visual}' + (f'<div class="wide">{wide}</div>' if wide else '') + '</div>')

def timeline(items):
    return '<ul class="timeline">' + ''.join(f'<li><b>{E(d)}</b><span>{t}</span></li>' for d, t in items) + '</ul>'

CHIPS = {1: ['8 puertas renovadas', '8 faroles nuevos', 'Letrero Casa Sole 128', 'Barandales y escaleras'],
 2: ['28 visitas de servicio', 'Filtro de arena nuevo', 'Bomba nueva', 'Calentador nuevo en octubre'],
 3: ['4 unidades atendidas', 'Rejillas rehechas', 'Ventanas selladas'],
 4: ['9 detectores nuevos', '7 timbres Ring con cámara', 'Chapas y llaves'],
 5: ['Clima', 'Cocina y electrodomésticos', 'Baños', 'Muebles y luz'],
 6: ['Cerca hidrolavada', '12 lavados a presión', '2 fumigaciones', 'Pasto y jardín'],
 7: ['Cada reporte con su tiempo de respuesta'],
 8: ['Calentador del jacuzzi', 'Lluvias en 3 unidades', '18 trabajos al 16 de octubre'],
 9: ['Decisión de los socios', 'En manos del equipo']}
def cap_head(num, titulo, intro):
    chips = ''.join(f'<span>{E(c)}</span>' for c in CHIPS.get(num, []))
    return (f'<section class="cap" id="cap{num}"><div class="band-light cap-band"><div class="in"><div class="num">Capítulo {num}</div><h2>{titulo}</h2><p class="intro">{intro}</p>'
            + (f'<div class="chips">{chips}</div>' if chips else '') + '</div></div><div class="in cap-body">')
def cmp(antes, despues, cap, pos_a='center', pos_d='center', maxw=600, q=68, eager=False):
    img_d = img_tag(despues, maxw, q, pos_d, eager, None, 'Después').replace('<img ', '<img class="a" ', 1)
    img_a = img_tag(antes, maxw, q, pos_a, eager, None, 'Antes')
    return (f'<figure class="cmpf"><div class="cmp">{img_d}<div class="b">{img_a}</div>'
            f'<input type="range" min="0" max="100" value="50" aria-label="Comparar antes y después"><div class="hd"></div>'
            f'<span class="lab la">Antes</span><span class="lab ld">Después</span></div><figcaption class="cmp-cap">{cap}</figcaption></figure>')
def card(anchor, num, titulo, texto, foto, pos='center'):
    return f'<a class="card" href="#{anchor}">{ph(foto, None, pos, 400, 64)}<div class="cb"><div class="n">{num}</div><h3>{E(titulo)}</h3><p>{E(texto)}</p></div></a>'

MESES = {1:'ene',2:'feb',3:'mar',4:'abr',5:'may',6:'jun',7:'jul',8:'ago',9:'sep',10:'oct',11:'nov',12:'dic'}
def fd(s):
    if not s: return ''
    d = date.fromisoformat(s); return f'{d.day} {MESES[d.month]}'

def unidad_txt(v):
    us = [u.strip() for u in v['unidades']]
    us = ['Áreas comunes' if u in ('Edificio AMB', 'AMB-AL', 'Todos') else u.upper() for u in us]
    us = [u for u in us if u.upper().startswith('AMB') or u == 'Áreas comunes']
    out = []
    for u in us:
        if u not in out: out.append(u)
    return ', '.join(out) or 'Áreas comunes'
TIT = {175: 'TV de sala: montada con soporte nuevo', 236: 'Filtro de arena de la alberca: reemplazo completo', 216: 'Escalera para operación', 339: 'Compra de materiales en SPI Hardware', 340: 'Revisión de refrigerador', 181: 'Letreros del permiso STR actualizados en todas las unidades', 210: 'Detector de humo intermitente: reemplazo pendiente de instalar', 209: 'Base de cama king rota: reforzada', 231: 'Base de cama twin rota (1 de 2): pedida', 232: 'Base de cama twin rota (2 de 2): pedida', 1: 'Panel eléctrico de la alberca oxidado: energía restablecida, reemplazo cotizado', 182: 'Termostato del A/C: pilas y reemplazo', 252: 'Detectores de humo y monóxido: programa de reemplazo', 235: 'Instalar timbres Ring', 226: 'Lavamanos: reemplazo', 228: 'Plomería pendiente', 217: 'Tostador por reemplazar', 223: 'Revisar lavadora', 245: '', 266: 'Pintar las ocho puertas de entrada', 174: 'Poste de barandal sin tapa, agarraderas flojas', 254: 'Puerta principal: marco astillado y herrajes oxidados', 253: 'Caja de llaves (lockbox) reemplazada', 200: 'Chapa que se batallaba: arreglada', 202: 'Puerta de lavadora caída: arreglada', 203: 'Foco exterior cambiado', 191: 'Control de TV repuesto', 179: 'Internet sin servicio: módem reemplazado por Spectrum', 180: 'Internet sin servicio: restablecido', 183: 'Colchón hundido', 348: 'Fallas eléctricas en cocina (triturador, lavavajillas y drenaje)', 189: 'Fumigación de todas las unidades', 204: ''}
def titulo_limpio(t, i=None):
    if i in TIT: return TIT[i]
    t = t.split(' — ')[0]
    t = re.sub(r'\s*\([^)]*(\$|no tengo|pendiente saber|tentativo|confirmar|cotizar|por transfer)[^)]*\)', '', t, flags=re.I)
    t = re.sub(r'\s*#\d{4}\b', '', t)
    t = re.sub(r'\$[\d,\.]+', '', t)
    return t.strip().rstrip(':').strip()

# ------------------------------------------------------------------ números
PER = [v for v in INC.values() if v['f_rep'] and '2026-06-01' <= v['f_rep'] <= '2026-09-30']
OCT = [v for v in INC.values() if v['f_rep'] and v['f_rep'] >= '2026-10-01']
n_per = len(PER)
n_cerr = sum(1 for v in PER if v['estatus'] in ('Terminado', 'Cerrada/Noprocede'))
cerr = [v for v in PER if v['estatus'] in ('Terminado', 'Cerrada/Noprocede') and v['f_cierre']]
dias = [(date.fromisoformat(v['f_cierre']) - date.fromisoformat(v['f_rep'])).days for v in cerr]
mismo_dia = sum(1 for d in dias if d == 0)
amb_blocks = [b for b in BLOCKS if b['amb'] and b['fecha'] and str(b['fecha'])[:10] <= '2026-09-30']
horas_beto = round(sum(b['horas'] for b in amb_blocks))
dias_beto = len(set(str(b['fecha'])[:10] for b in amb_blocks))
fotos_per = sum(len(v['fotos']) for v in PER)
fotos_tot = sum(len(v['fotos']) for v in INC.values())
rep = Counter(v['reportado'] for v in PER)
n_huesped = rep.get('Huésped', 0)
por_mes = Counter(v['f_rep'][:7] for v in PER)
visitas_bc = 6 + 9 + 9 + 4
print('n_per', n_per, 'cerrados', n_cerr, 'mismo dia', mismo_dia, '/', len(dias), 'horas', horas_beto, 'dias', dias_beto, 'fotos per', fotos_per, 'tot', fotos_tot, rep)

SITE_EXTRA_CSS = r"""
.nav a.out{margin-left:auto;color:var(--muted)}
.ph img{background:var(--phbg)}
"""
SITE_JS = r"""
(function(){
  if(/github\.io$/.test(location.hostname)){ document.querySelectorAll('a.out').forEach(function(a){a.remove()}); }
  document.querySelectorAll('.cmp').forEach(function(c){
    var r=c.querySelector('input[type=range]'), b=c.querySelector('.b'), h=c.querySelector('.hd');
    function set(v){ b.style.clipPath='inset(0 '+(100-v)+'% 0 0)'; h.style.left=v+'%'; }
    r.addEventListener('input',function(){set(+r.value)}); set(50);
  });
  var bar=document.getElementById('filters'); if(!bar) return;
  var units=document.querySelectorAll('#apx .apx-unit');
  var saved=null; try{saved=localStorage.getItem('amb-unit')}catch(e){}
  function apply(u){
    units.forEach(function(el){el.hidden = !(u==='all' || el.getAttribute('data-unit')===u)});
    bar.querySelectorAll('button').forEach(function(b){b.setAttribute('aria-pressed', b.getAttribute('data-unit')===u ? 'true':'false')});
    try{localStorage.setItem('amb-unit',u)}catch(e){}
  }
  bar.addEventListener('click',function(ev){var b=ev.target.closest('button'); if(!b) return; apply(b.getAttribute('data-unit'));});
  var h=(location.hash||'').replace('#',''); if(h && bar.querySelector('[data-unit="'+h+'"]')) apply(h);
  else if(saved && bar.querySelector('[data-unit="'+saved+'"]')) apply(saved);
})();
"""
FAVICON = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#0F2B46"/><circle cx="32" cy="30" r="11" fill="#C9A86A"/><path d="M12 50h40" stroke="#1C7293" stroke-width="5" stroke-linecap="round"/></svg>'
# ------------------------------------------------------------------ contenido
parts = []
def nav(home):
    h = '' if home else 'index.html'
    return (f'<nav class="nav"><div class="in"><a class="brand" href="{h or "#top"}"><small>Casasole LP</small>Amberjack 2026</a><a href="{h}#antecedente">Antecedente</a><a href="{h}#programas">Programas</a><a href="{h}#numeros">Números</a><a href="{h}#cap1">Imagen</a><a href="{h}#cap2">Alberca</a><a href="{h}#cap3">Lluvias</a><a href="{h}#cap4">Seguridad</a><a href="{h}#cap5">Unidades</a><a href="{h}#cap6">Exterior</a><a href="{h}#cap7">Huéspedes</a><a href="{h}#cap8">Octubre</a><a href="{h}#cap9">Lo que sigue</a><a href="unidades.html">Por unidad</a><a class="out" href="logout">Salir</a></div></nav>')
def head(title, desc, home=True):
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex,nofollow">
<meta name="theme-color" content="#0F2B46">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=Inter:wght@400;500;600&display=swap">
<link rel="stylesheet" href="css/site.css?v={VER}">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
</head>
<body>
{nav(home)}
"""
parts.append(head('Amberjack 2026 · Casasole', 'Programa de renovación y operación de Amberjack 1–8, junio a septiembre de 2026 y octubre en curso.'))
parts.append(f"""<header class="band hero" id="top"><div class="in hero-grid">
  <div>
    <p class="kicker">Informe para los socios · Amberjack 1–8, South Padre Island</p>
    <h1>Programa de mantenimiento, renovación y operación 2026</h1>
    <p class="sub">Todo lo que se hizo en la propiedad de junio a septiembre, y lo que va de octubre, contado con las fotos de antes y después que tomó el equipo en sitio.</p>
    <p class="meta"><b>Wanderhaus LLC</b> · administración y mantenimiento · corte al 16 de octubre de 2026</p>
  </div>
  <div>{cmp('266_antes_17','266_despues_04','Puerta de la unidad 2, antes y después del programa de puertas de septiembre. Arrastra el control para comparar.', pos_a='center 40%', pos_d='center 45%', eager=True)}</div>
</div>
<div class="in"><div class="kpis">
  <div class="kpi"><b>{n_per}</b><span>trabajos registrados de junio a septiembre</span></div>
  <div class="kpi"><b>{n_cerr}</b><span>cerrados al corte; {mismo_dia} el mismo día que se reportaron</span></div>
  <div class="kpi"><b>{horas_beto} h</b><span>de handyman en sitio, {dias_beto} jornadas</span></div>
  <div class="kpi"><b>{fotos_tot}</b><span>fotos de antes y después en la bitácora</span></div>
</div></div></header>
<div class="after-hero"></div>

<section class="antecedente" id="antecedente"><div class="in">
  <p class="kicker">Antecedente</p>
  <h2>Por qué cambió la forma de operar</h2>
  <p class="lead">Hasta la primavera de 2026 el mantenimiento de Amberjack dependía de un encargado que se negaba a rendir cuentas: no reportaba lo que hacía, no tomaba fotos y no presentaba recibos. Los incumplimientos y las quejas de huéspedes se fueron acumulando, y en <b>mayo de 2026</b> se tomó la decisión de terminar esa relación y rehacer el programa de mantenimiento desde cero: ejecución inmediata, proveedores profesionales, evidencia de cada trabajo y control por medio de tecnología. <b>Este es el primer informe bajo el nuevo esquema.</b></p>
  <div class="aa">
    <div class="antes"><h3>Antes<small>hasta mayo de 2026</small></h3><ul>
      <li>Un encargado de mantenimiento que se negaba a rendir cuentas: no reportaba, no tomaba fotos y no presentaba recibos.</li>
      <li>Los reportes de huéspedes no tenían fecha de atención ni de cierre; muchos se quedaban sin resolver.</li>
      <li>Compras y gastos sin comprobante, sin cotización y sin comparar proveedores.</li>
      <li>Reparaciones sin evidencia: no había forma de saber qué se hizo ni cómo quedó.</li>
      <li>Sin garantías sobre el trabajo ni sobre los equipos instalados.</li>
      <li>Quejas repetidas de huéspedes por fallas que no se atendían.</li>
    </ul></div>
    <div class="ahora"><h3>Ahora<small>desde mayo de 2026</small></h3><ul>
      <li><b>Todo queda registrado.</b> Cada reporte entra a la bitácora (Airtable) con unidad, fecha, quién lo reportó y urgencia; se asigna a un responsable y se cierra con fecha.</li>
      <li><b>Se atiende de inmediato y se mide.</b> {mismo_dia} de {len(dias)} trabajos cerrados se resolvieron el mismo día; el tiempo de respuesta queda registrado en cada caso.</li>
      <li><b>Evidencia obligatoria.</b> Fotos de antes y después de cada trabajo: {fotos_tot} en este periodo.</li>
      <li><b>Trabajo externo y profesional.</b> Handyman por jornadas registradas, servicio de alberca con reporte en cada visita, y para reparaciones mayores se cotiza con varios proveedores antes de aprobar.</li>
      <li><b>Garantías.</b> Los equipos nuevos se compran con garantía del fabricante (la bomba de la alberca, dos años) y cada proveedor responde por su trabajo.</li>
      <li><b>Transparencia.</b> Este informe se actualiza cada mes en la misma dirección y los socios tienen acceso permanente a todos los trabajos y sus fotos.</li>
    </ul></div>
  </div>
  <p class="cierre">Lo que sigue en este informe es el resultado de ese cambio: lo que se hizo de junio a septiembre, programa por programa, y lo que va de octubre.</p>
</div></section>
<section class="programs" id="programas"><div class="in">
  <p class="kicker">Lo que se hizo, por programa</p>
  <h2>Ocho programas, un verano</h2>
  <p class="lead">Cada programa tiene su capítulo con la historia, las fechas y las fotos. Toca uno para ir directo.</p>
  <div class="cards">
   {card('cap1','01','Renovación de imagen','Puertas, letrero, faroles y barandales.','266_despues_12','center 30%')}
   {card('cap2','02','Alberca y jacuzzi','Filtro, bomba, calentador y 28 visitas de servicio.','445_antes_01_p11_09')}
   {card('cap3','03','Lluvias y humedad','Techos, rejillas y ventanas en cuatro unidades.','451_despues_09','center 40%')}
   {card('cap4','04','Seguridad y accesos','Detectores, timbres Ring y chapas.','455_despues_01','center 40%')}
   {card('cap5','05','Dentro de las unidades','Clima, cocina, baños, muebles y luz.','226_despues_01')}
   {card('cap6','06','Exterior y limpieza','Cerca hidrolavada, pisos, jardín y fumigación.','443_despues_04')}
   {card('cap7','07','Atención al huésped','{n_huesped} reportes de huéspedes y cuánto tardó cada uno.','182_despues_01')}
   {card('cap8','08','Octubre, en curso','Calentador del jacuzzi y reparación por lluvias.','462_despues_02_p04_03')}
  </div>
</div></section>
""")

# EL VERANO EN NÚMEROS
parts.append(f"""
<section class="sec" id="numeros"><div class="in">
<div class="cap-head"><div class="num">Resumen</div><h2>El verano en números</h2>
<p class="intro">Entre junio y septiembre la propiedad tuvo <b>{n_per} trabajos registrados</b>: reparaciones, mejoras, limpiezas y servicio de alberca. Cada uno quedó en la bitácora con quién lo reportó, quién lo atendió, cuándo se cerró y, en la gran mayoría, con fotos de antes y después.</p></div>
<div class="stats">
 <div class="stat"><b>{n_per}</b><span>trabajos registrados de junio a septiembre ({por_mes['2026-06']} en junio, {por_mes['2026-07']} en julio, {por_mes['2026-08']} en agosto, {por_mes['2026-09']} en septiembre)</span></div>
 <div class="stat"><b>{n_cerr}</b><span>cerrados al corte del 16 de octubre; el resto está en proceso o esperando autorización</span></div>
 <div class="stat"><b>{mismo_dia} de {len(dias)}</b><span>trabajos cerrados se resolvieron el mismo día en que se reportaron</span></div>
 <div class="stat"><b>{horas_beto} h</b><span>de handyman en sitio en {dias_beto} jornadas (Beto), julio a septiembre</span></div>
 <div class="stat"><b>{visitas_bc}</b><span>visitas de servicio de alberca de Blue Creek, junio a septiembre</span></div>
 <div class="stat"><b>8 de 8</b><span>unidades con puerta renovada, farol exterior nuevo y fumigación; 7 de 8 ya con timbre Ring con cámara</span></div>
 <div class="stat"><b>{round(100*(n_per-n_huesped)/n_per)} %</b><span>de los trabajos los detectó el equipo (inspección, limpieza, administración) antes de que un huésped los reportara</span></div>
 <div class="stat"><b>{fotos_per}</b><span>fotos documentan los trabajos de junio a septiembre; {fotos_tot} en todo el periodo</span></div>
</div>
<h3 style="margin-top:44px">Cómo trabajamos</h3>
<p class="intro" style="margin-bottom:6px">Un equipo chico, en sitio, con una regla: todo lo que se hace se registra y se fotografía.</p>
<div class="team">
 <div><b>Bitácora en Airtable</b><span>Cada reporte lleva unidad, fecha, quién lo reportó y urgencia. Se asigna, se cierra con fecha y se documenta con fotos.</span></div>
 <div><b>Beto, handyman</b><span>Reparaciones, pintura, instalaciones y limpieza de exteriores, por jornadas registradas. En septiembre fue casi diario.</span></div>
 <div><b>Lily, limpieza</b><span>Limpia entre huéspedes y es la primera en detectar fallas: {rep.get('Limpieza',0)} de los {n_per} reportes vinieron de limpieza.</span></div>
 <div><b>Blue Creek Pool Service</b><span>Servicio semanal de alberca y jacuzzi, química del agua, reparaciones y reporte con fotos de cada visita.</span></div>
 <div><b>Melany y Miguel</b><span>Reciben los reportes, compran materiales, dan seguimiento y cierran cada trabajo.</span></div>
</div>
<h3 style="margin-top:44px">De dónde salen los reportes</h3>
<div class="origen">
 <div><b>{rep.get('Mantenimiento',0)}</b><i>Mantenimiento</i><span>Lo que Beto detecta en sus recorridos: lo que está por fallar, no lo que ya falló.</span></div>
 <div><b>{rep.get('Miguel',0)+rep.get('Melanny',0)}</b><i>Administración</i><span>Programas decididos desde Wanderhaus: puertas, lámparas, timbres, detectores, letrero.</span></div>
 <div><b>{rep.get('Limpieza',0)}</b><i>Limpieza</i><span>Lo que Lily encuentra al limpiar entre huéspedes.</span></div>
 <div><b>{n_huesped}</b><i>Huéspedes</i><span>Lo que un huésped reportó durante su estancia. Están todos en el capítulo 7, con el tiempo que tardó cada uno.</span></div>
</div>
<p class="small muted" style="margin-top:28px">Las fotos las tomó el equipo en sitio con el teléfono, como parte del registro de cada trabajo; no son fotos de producción. Están completas, trabajo por trabajo, en la sección por unidad.</p>
</div></section>""")

# CAPÍTULO 1 · IMAGEN
parts.append(cap_head(1, 'Renovación de imagen',
 'Amberjack está a dos cuadras de la playa y la sal se come todo: pintura, herrajes, lámparas, tapas de barandal. En agosto y septiembre se atacó lo que un huésped ve al llegar: la puerta de su unidad, el letrero de la calle, la iluminación del pasillo y los barandales.'))
parts.append(proj('Las ocho puertas de entrada, renovadas', 'Septiembre · 8 unidades · Beto, 6 jornadas',
 ['Las puertas tenían salitre, manchas de hongo y pintura descarapelada. En lugar de comprar puertas nuevas, Beto las desmontó una por una, las lijó hasta la madera, resanó y aplicó esmalte para exterior; también se repintaron los números.',
  'Empezó el 6 de septiembre con la unidad 4 y terminó el 21 con la 8. Mientras cada puerta estaba fuera, el vano se cubrió para que la unidad siguiera en renta.'],
 pair('266_antes_16', '266_despues_04', 'Puerta de la unidad 2: la sal había manchado el panel completo. Hoy luce como nueva y con el mismo herraje.', pos_a='center 40%', pos_d='center 45%'),
 first=True,
 wide=strip([('266_antes_06', 'Vano cubierto mientras la puerta está en taller'), ('266_antes_09', 'Lijado a madera'), ('266_despues_09', 'Esmalte en caballetes'), ('266_despues_12', 'Unidad 7, terminada')], cols=4) +
      strip([('266_despues_02', 'Unidad 1'), ('266_despues_01', 'Unidad 4'), ('266_despues_05', 'Unidad 3'), ('266_despues_11', 'Unidad 6'), ('266_despues_13', 'Unidad 5'), ('266_despues_14', 'Unidad 8')], cols=6, cap='Las ocho puertas terminadas durante septiembre.')))
parts.append(proj('El letrero de la calle: “Casa Sole 128”', 'Septiembre · entrada por Amberjack St. · Beto',
 ['El monumento de la entrada todavía decía “San Francisco”, el nombre anterior del edificio, y el número no se leía desde la calle. El 1 de septiembre la ciudad dejó un aviso pidiendo la dirección numérica visible.',
  'Beto lijó el letrero hasta dejar la base limpia y se rotuló con el nombre actual y el número 128, legible de día y de noche. Quedó cerrado el 14 de septiembre, dentro del plazo del aviso.'],
 cmp('408_antes_03', '408_despues_02', 'Mismo monumento. El nombre viejo desapareció y el 128 se ve desde la banqueta.', pos_a='center 35%', pos_d='center 45%'),
 wide=strip([('408_antes_07', 'Lijado'), ('408_antes_10', 'Base lista para rotular'), ('408_despues_01', 'Desde la calle'), ('408_despues_03', 'Terminado')], cols=4)))
parts.append(proj('Iluminación exterior: faroles y luces de pasillo', 'Septiembre–octubre · 8 unidades y pasillos · Beto',
 ['Los faroles de las entradas estaban oxidados y con los vidrios opacos. Se cambiaron los ocho por el mismo modelo nuevo, uno por unidad, del 25 de septiembre al 2 de octubre.',
  'En los pasillos, los aros de las luces empotradas estaban corroídos. Se están sustituyendo por bisel blanco nuevo; las primeras siete ya están y faltan algunas piezas por llegar.'],
 pair('449_antes_01', '449_despues_01', 'Farol de la unidad 3: oxidado y apagado; nuevo e instalado.', pos_a='center 40%'),
 wide=strip([('449_despues_02', 'Unidad 2'), ('449_despues_03', 'Unidad 1'), ('450_antes_02', 'Aro corroído retirado'), ('450_antes_06', 'Luz de pasillo, antes'), ('450_despues_06', 'Bisel nuevo'), ('450_despues_03', 'Pasillo')], cols=6)))
parts.append(proj('Barandales, pasamanos y escaleras', 'Julio–octubre · áreas comunes · Beto',
 ['Los postes de los barandales tenían las tapas rotas o faltantes y la madera expuesta se estaba pudriendo con el agua. Se limpiaron, se selló la madera y se colocaron tapas piramidales nuevas en todos los postes que lo necesitaban.',
  'Los soportes metálicos de la baranda de la escalera estaban sin instalar y oxidados: se lijaron, instalaron y pintaron. Los soportes del pasamanos, desgastados, se cambiaron por piezas nuevas. Y en los escalones, que estaban resbalosos, se colocaron tiras antiderrapantes.'],
 pair('174_antes_04', '174_despues_01', 'Poste de barandal del segundo piso: la madera expuesta y agrietada, y la tapa nueva ya sellada.'),
 wide=strip([('431_antes_08', 'Postes sin tapa'), ('431_despues_02', 'Con tapa'), ('384_antes_01', 'Soporte oxidado'), ('384_despues_01', 'Soportes instalados y pintados'), ('418_antes_02', 'Soporte de pasamanos desgastado'), ('418_despues_01', 'Pieza nueva')], cols=6) +
      strip([('383_antes_01', 'Escalones sin antiderrapante'), ('383_despues_02', 'Tiras antiderrapantes'), ('382_antes_12', 'Piso de entrada: juntas dañadas'), ('382_antes_13', 'Juntas selladas')], cols=4)))
parts.append(proj('Detalles que también cambiaron', 'Agosto–octubre',
 ['Los letreros del permiso STR en las ventanas tenían el contacto de una persona que ya no trabaja con nosotros; se reemplazaron en todas las unidades con el número vigente de Melany (4 de agosto).',
  'En AMB-01 y AMB-03 se cambiaron las persianas rotas por nuevas. En AMB-04 se restauró el mueble de la recámara principal, que estaba despintado. En AMB-06 se resanó una grieta en la pared de la cocina.'],
 pair('316_antes_03', '316_despues_01', 'Persianas con las tablillas rotas (reporte de un huésped) y las nuevas instaladas.', pos_a='center 40%'),
 wide=strip([('181_antes_02', 'Letrero STR con contacto viejo'), ('181_despues_02', 'Letrero actualizado'), ('379_antes_04', 'Mueble despintado, AMB-04'), ('379_despues_01', 'Restaurado'), ('387_antes_02', 'Grieta en cocina, AMB-06'), ('387_despues_01', 'Resanada')], cols=6)))
parts.append('</div></section>')

# CAPÍTULO 2 · ALBERCA
parts.append(cap_head(2, 'Alberca y jacuzzi',
 'La alberca es lo que más fotos recibe en las reseñas y lo que más mantenimiento pide en South Padre: sal, viento, arena y lluvia. Este verano se rehízo prácticamente todo el cuarto de máquinas y se sostuvo el servicio semanal sin interrupción.'))
parts.append('<h3>Lo que pasó, en orden</h3>' + timeline([
 ('Junio', 'Seis visitas de servicio de Blue Creek (química del agua, limpieza, cambio de tapa y empaque del colador).'),
 ('Julio', 'Nueve visitas de servicio. El 6 de julio el breaker oxidado del panel de la alberca se botó; se restableció la energía y Blue Creek cotizó el reemplazo del panel (ver “Lo que sigue”).'),
 ('7 jul', 'La bomba del jacuzzi perdía el cebado: la unión de succión estaba agrietada. Blue Creek la reemplazó el mismo día de la visita.'),
 ('24–28 jul', 'Con el filtro de arena viejo fallando, el agua se puso verde y un huésped lo reportó. El 27 el filtro, corroído por el salitre, empezó a fugar agua a presión: se aprobó el reemplazo y en menos de 24 horas quedó instalado el filtro nuevo con válvula multipuerto.'),
 ('30 jul', 'Agua clara otra vez: se trató con cloro, alguicida y clarificador y el filtro nuevo hizo el resto.'),
 ('Agosto', 'Nueve visitas de servicio. Se instaló una bomba nueva de velocidad variable (Pentair IntelliFlo3 VSF, 1.5 HP, dos años de garantía), que consume menos y es más silenciosa.'),
 ('Septiembre', 'Cuatro visitas de servicio. Beto compró una red y limpia la alberca entre visitas; el 26 de septiembre, al hidrolavar la cerca, la limpió de nuevo.'),
 ('30 sep', 'Visita de servicio al jacuzzi: la pantalla del calentador fallaba. Blue Creek advirtió que el calentador estaba empezando a fallar.'),
 ('1 oct', 'Se compró una máquina de limpieza de fondo para que Beto aspire la alberca sin depender del servicio semanal.'),
 ('8 oct', 'Calentador nuevo. Blue Creek aprovechó para reacomodar bombas y filtro del jacuzzi y retirar cajas eléctricas viejas (capítulo 8).'),
]))
parts.append('<div class="gal" style="margin-top:26px">' +
 cmp('236_antes_01', '236_despues_01', 'Filtro de arena: el tanque gris, corroído y fugando (27 de julio), y el tanque nuevo instalado al día siguiente.', pos_a='center 60%') +
 pair('326_antes_01', '326_despues_01', 'Bomba de la alberca: la instalación anterior y la bomba nueva de velocidad variable (19 de agosto).') +
 pair('411_antes_01', '335_despues_08_p10_07', 'El agua verde de finales de julio, con el filtro fallando, y la alberca el 30 de julio con el filtro nuevo trabajando.') +
 pair('430_antes_01', '430_despues_01', 'Limpieza entre visitas con la red nueva: hojas y basura fuera el mismo día (5 de septiembre).') +
 '</div>')
parts.append('<h3 style="margin-top:34px">El servicio semanal, visita por visita</h3><p class="intro">Blue Creek deja un reporte con fotos en cada visita. Estas son doce de las ' + str(visitas_bc) + ' del periodo, una por semana, tal como las entregó el técnico.</p>' +
 strip([('335_despues_01_p10_07', '9 jul'), ('335_despues_03_p11_06', '16 jul'), ('335_despues_05_p11_06', '23 jul'), ('335_despues_08_p10_07', '30 jul'), ('411_despues_02_p09_05', '3 ago'), ('411_despues_04_p11_06', '10 ago'),
        ('411_despues_06_p09_06', '17 ago'), ('411_despues_08_p10_05', '24 ago'), ('445_antes_01_p11_09', '3 sep'), ('445_antes_02_p08_06', '10 sep'), ('445_antes_03_p07_05', '17 sep'), ('445_antes_04_p08_06', '24 sep')], cols=6, sq=True))
parts.append('<h3 style="margin-top:30px">El cuarto de máquinas, de julio a octubre</h3>' +
 strip([('335_despues_07_p12_07', '27 jul: filtro viejo, gris'), ('335_despues_08_p07_05', '30 jul: filtro nuevo'), ('411_despues_09_p06_04', '27 ago: con bomba nueva'), ('462_despues_02_p04_03', '8 oct: calentador nuevo')], cols=4, cap='La misma esquina del cuarto de máquinas en cuatro momentos. En octubre, además del calentador, se reacomodaron bombas y filtro del jacuzzi.'))
parts.append('<h3 style="margin-top:30px">Área de asador y accesorios</h3>' + '<div class="gal">' +
 pair('250_antes_01', '250_despues_03', 'Asador: la charola y el quemador con grasa acumulada; limpio y listo para la temporada (31 de julio).', pos_a='center 40%') +
 pair('269_antes_01', '269_despues_02', 'Segunda limpieza a fondo del asador el 4 de agosto; se rellenó el tanque de gas dos veces en el verano.') +
 '</div>' + strip([('351_antes_01', 'Conector de manguera roto'), ('351_despues_01', 'Conector nuevo'), ('357_despues_01', 'Máquina de limpieza de fondo (octubre)'), ('357_despues_02', 'Red para basura flotante')], cols=4))
parts.append('</div></section>')

# CAPÍTULO 3 · AGUA
parts.append(cap_head(3, 'Lluvias, humedad y filtraciones',
 'Agosto y octubre trajeron lluvia fuerte. En una construcción frente al mar, eso se traduce en manchas de humedad en techos, rejillas de ventilación oxidadas, marcos de ventana que absorben agua y moho en esquinas. Se atendió unidad por unidad: limpieza, sellado, resane y pintura. Las lluvias de octubre, que volvieron a meter agua en tres unidades, están en el capítulo 8.'))
parts.append('<div class="gal">' +
 cmp('373_antes_04', '373_despues_04', 'AMB-01 (20–25 de agosto): el techo junto al ventilador tenía desprendimiento de pintura por la humedad de la rejilla. Se resanó y pintó.', pos_a='center 30%', pos_d='center 30%') +
 pair('373_antes_12', '373_despues_05', 'AMB-01: el marco de la ventana estaba hinchado por el agua; se reparó, selló y se repusieron las persianas.') +
 pair('397_antes_11', '397_despues_01', 'AMB-03 (25–29 de agosto): las rejillas de ventilación estaban oxidadas y soltaban olor. Se desmontaron, limpiaron con vinagre y cloro, y se pintaron.') +
 pair('400_antes_05', '400_despues_01', 'AMB-05 (21–29 de agosto): grietas y manchas en el techo, resanadas y pintadas.') +
 '</div>')
parts.append(strip([('397_antes_04', 'AMB-03: rejillas retiradas, con óxido'), ('397_despues_02', 'Rejillas pintadas'), ('373_antes_03', 'AMB-01: ducto sin rejilla'), ('373_despues_03', 'Rejilla repuesta y techo pintado')], cols=4, cap='Las rejillas del aire acondicionado son el punto donde más se concentra la humedad; en AMB-01 y AMB-03 se rehicieron por completo.'))
parts.append('<h3 style="margin-top:30px">Sellado preventivo</h3><div class="gal">' +
 pair('308_antes_01', '308_despues_02', 'AMB-02 (10 de agosto): el repisón de la ventana de la cocina estaba agrietado y dejaba pasar agua. Se selló y repintó.') +
 pair('262_antes_01', '262_despues_01', 'AMB-04: juntas entre azulejo y muro, selladas con caulking para que el agua de la regadera no entre a la pared. Igual en AMB-05.') +
 pair('425_antes_01', '425_despues_01', 'Techo de la entrada, desprendido: enderezado y fijado el mismo día (5 de septiembre).') +
 pair('426_antes_01', '426_despues_01', 'Pared junto a la caja de servicios, dañada: resanada y caja recolocada (5 de septiembre).') +
 '</div>')
parts.append('</div></section>')

# CAPÍTULO 4 · SEGURIDAD
parts.append(cap_head(4, 'Seguridad y accesos',
 'Tres frentes: que cada unidad tenga detectores de humo y monóxido vigentes, que la entrada tenga cámara, y que las chapas y llaves funcionen a la primera, tanto para huéspedes como para el equipo de limpieza.'))
parts.append(proj('Detectores de humo y monóxido, programa de reemplazo', 'Julio–agosto · 8 unidades',
 ['Los detectores del edificio cumplieron diez años, que es su vida útil. Se compraron nueve detectores combinados (humo y monóxido, cableados con batería de respaldo de 10 años) para reemplazar los de todas las unidades.',
  'Se instalaron en AMB-02, 03, 05, 06 y 07; en AMB-01, donde el detector sonaba intermitente, está comprado y pendiente de instalar.'],
 pair('252_antes_01', '252_despues_01', 'Base cableada del detector viejo y el detector combinado nuevo instalado.'),
 first=True,
 wide=strip([('252_antes_02', 'Nueve detectores, listos para instalar'), ('252_despues_02', 'Instalado y en prueba'), ('252_despues_03', 'Cajas de los reemplazados')], cols=3)))
parts.append(proj('Timbres Ring con cámara en las ocho entradas', 'Agosto–septiembre · 8 unidades · Beto',
 ['Los timbres anteriores (Nest blancos, ya sin servicio) se sustituyeron por Ring con cámara, negros. Permiten ver quién llega, hablar con el huésped si se queda afuera y tener registro de entradas. Se instalaron entre el 2 de agosto y el 7 de septiembre.'],
 cmp('434_antes_01', '434_despues_01', 'AMB-08: el botón anterior y el Ring con cámara instalado en el mismo punto (7 de septiembre).'),
 wide=strip([('455_despues_01', 'Ring en operación'), ('434_despues_01', 'AMB-08'), ('455_antes_01', 'Alta en la app Ring')], cols=3, sq=True, cap='Según la bitácora hay Ring en siete entradas y falta el de AMB-05. Las fotos del Ring instalado en cada unidad se agregan en la siguiente versión; las que estaban cargadas mostraban el timbre anterior.')))
parts.append(proj('Chapas, bisagras y llaves', 'Julio–octubre · varias unidades · Beto',
 ['Se arreglaron o cambiaron chapas en AMB-01, 03, 05, 06 y 08 (una de baño que se zafaba, una principal que se batallaba para abrir, la caja de llaves de AMB-08, bisagras caídas).',
  'En octubre se cambiaron las chapas de AMB-01, 03 y 06 por juegos nuevos de cerradura y manija, y se sacaron copias de llaves para el equipo.'],
 pair('454_antes_03', '454_despues_02', 'AMB-01: la manija vieja, floja, y el juego nuevo de cerrojo y manija (11 de octubre).'),
 wide=strip([('206_antes_01', 'AMB-03: chapa de baño zafada'), ('206_despues_01', 'Reparada'), ('265_antes_01', 'AMB-05: chapa'), ('265_despues_01', 'Ajustada'), ('253_despues_01', 'AMB-08: lockbox nuevo'), ('465_despues_01', 'AMB-06: bisagra repuesta')], cols=6)))
parts.append('</div></section>')

# CAPÍTULO 5 · UNIDADES
parts.append(cap_head(5, 'Dentro de las unidades',
 'Lo que el huésped toca: el clima, la cocina, el baño, la cama, la tele. Son trabajos chicos pero son los que generan reseñas, buenas o malas. Este es el resumen de los más visibles; el anexo tiene todos.'))
parts.append('<h3>Clima</h3><div class="gal">' +
 pair('377_antes_05', '377_despues_06', 'Filtros de aire acondicionado saturados: se cambiaron en AMB-01, 02, 05 y 06 el 1 de agosto y en AMB-03 y AMB-05 el 18.') +
 pair('182_antes_01', '182_despues_01', 'AMB-01: un huésped escribió que el termostato no bajaba de 82 °F. Se atendió el mismo día (pilas) y, al repetirse en octubre, se cambió el termostato.') +
 pair('368_antes_01', '368_despues_01', 'AMB-07: la pantalla del termostato no mostraba nada; pilas nuevas y de vuelta a 77 °F.') +
 pair('401_antes_02', '401_despues_01', 'AMB-04: el clima tiraba agua porque el drenaje del condensado estaba tapado; se destapó y corrigió la salida (30 de agosto).') +
 '</div>')
parts.append('<h3 style="margin-top:30px">Cocina y electrodomésticos</h3><div class="gal">' +
 pair('348_antes_01', '348_despues_02', 'AMB-05: el circuito del microondas empotrado botaba las pastillas y dejaba sin corriente el triturador y el lavavajillas. Se corrigió el circuito y todo volvió a funcionar (14 de agosto).') +
 pair('222_antes_01', '222_despues_03', 'Secadoras: pelusa acumulada en el ducto y el filtro, un riesgo de incendio. Se limpiaron en AMB-01, 03, 04 y 05.') +
 pair('307_antes_01', '307_despues_02', 'AMB-02: los sartenes rayados se reemplazaron por un juego nuevo y se reacomodó la cocina.') +
 pair('304_antes_01', '304_despues_01', 'AMB-04: la puerta del refrigerador estaba floja; se ajustó el herraje.') +
 '</div>' + strip([('225_antes_01', 'AMB-03: microondas'), ('225_despues_01', 'Limpio y probado'), ('229_despues_01', 'AMB-07/08: lavavajillas revisados'), ('469_antes_01', 'AMB-07: pieza de lavavajillas'), ('469_despues_01', 'Repuesta'), ('227_despues_02', 'AMB-05/06: refrigeradores revisados')], cols=6))
parts.append('<h3 style="margin-top:30px">Baños</h3><div class="gal">' +
 cmp('226_antes_08', '226_despues_01', 'AMB-05: el lavamanos tenía los anclajes oxidados y la mezcladora vieja; se instaló lavamanos y llave Moen nuevos (2 de agosto).') +
 pair('386_antes_01', '386_despues_01', 'AMB-01: el riel de la puerta de la regadera no corría; se cambiaron rodillos y guías (25 de agosto).') +
 pair('374_antes_01', '374_despues_01', 'AMB-01: toallero desprendido de la pared; reinstalado con anclas nuevas.') +
 pair('234_antes_03', '234_despues_03', 'AMB-05: puerta del baño principal con hoyo y bisagras oxidadas; se resanó y se cambió el herraje.') +
 '</div>' + strip([('289_antes_01', 'AMB-05: baño tapado'), ('289_despues_01', 'Destapado'), ('267_antes_01', 'AMB-05: riel de regadera'), ('267_despues_01', 'Reparado'), ('433_antes_01', 'AMB-02: toallero'), ('433_despues_02', 'Instalado')], cols=6))
parts.append('<h3 style="margin-top:30px">Muebles, luz y tele</h3><div class="gal">' +
 pair('209_antes_01', '209_despues_01', 'AMB-01: la base de la cama king estaba rota; Beto la reforzó el 31 de julio y la base nueva quedó de repuesto.') +
 pair('310_antes_02', '310_despues_01', 'AMB-05: puerta del clóset quebrada en la bisagra; reparada y colgada de nuevo.') +
 pair('345_antes_01', '345_despues_01', 'AMB-05: la tele estaba mal montada y hubo que bajarla; se instaló soporte nuevo y se ordenó el cableado.') +
 pair('378_antes_01', '378_despues_01', 'AMB-05: el candelabro del comedor se desprendió del techo; se volvió a fijar.') +
 '</div>' + strip([('285_antes_01', 'AMB-01: focos empotrados fundidos'), ('285_despues_02', 'Cambiados'), ('283_antes_01', 'AMB-04: candelabro con focos fundidos'), ('283_despues_01', 'Completo'), ('284_antes_01', 'AMB-04: cableado expuesto'), ('284_despues_01', 'Tapado')], cols=6) +
 strip([('417_antes_02', 'AMB-02: ventilador con foco roto'), ('417_despues_01', 'Repuesto'), ('364_antes_02', 'AMB-03: bisagra de gabinete caída'), ('364_despues_02', 'Reparada'), ('389_antes_01', 'AMB-04: bisagra floja'), ('389_despues_01', 'Ajustada')], cols=6))
parts.append('</div></section>')

# CAPÍTULO 6 · EXTERIOR
parts.append(cap_head(6, 'Limpieza, jardín y áreas comunes',
 'Lo que mantiene la propiedad presentable entre huéspedes: lavado a presión de pisos y cerca, poda, pasto, fumigación y orden en la bodega. Casi todo con mano de obra propia.'))
parts.append(proj('La cerca perimetral, hidrolavada', '26–27 de septiembre · Beto',
 ['La madera de la cerca llevaba años acumulando una capa gris de sal y moho. Beto la hidrolavó completa en dos días, incluida la puerta y la zona del cuarto de máquinas, y al terminar limpió la alberca, que se había ensuciado con el trabajo.'],
 cmp('443_antes_04', '443_despues_04', 'Es la misma madera: lo que cambió es la capa de sal y moho que tenía encima.'),
 first=True,
 wide=strip([('443_antes_02', 'Junto a la alberca, antes'), ('443_despues_03', 'Después'), ('443_antes_09', 'Puerta de la cerca'), ('443_despues_05', 'Zona de equipo'), ('443_despues_11', 'Patio'), ('443_despues_12', 'Terraza del asador')], cols=6)))
parts.append(proj('Pisos y pasillos a presión, cada dos semanas', 'Agosto–octubre · áreas comunes · Beto',
 ['Los adoquines del patio, la terraza de la alberca y los pasillos se lavaron a presión en doce ocasiones entre el 31 de julio y el 10 de octubre. También se vaciaron y lavaron los botes de basura y se limpió la fuente de la entrada.'],
 pair('288_antes_01', '288_despues_02', 'Pasillo central: con sarro y manchas, y recién lavado (8 de agosto).'),
 wide=strip([('349_antes_02', 'Terraza de alberca, antes'), ('349_despues_04', 'Después (16 ago)'), ('407_antes_12', 'Patio, antes'), ('407_despues_04', 'Después (1 sep)'), ('268_antes_01', 'Entrada, antes'), ('268_despues_01', 'Después (4 ago)')], cols=6)))
parts.append(proj('Jardín y pasto', 'Julio–octubre · Beto',
 ['Se recortaron los arbustos de la entrada (31 de julio), se cortó el pasto y se perfilaron las orillas de las jardineras y banquetas (18 de agosto, 19 de septiembre y 11 de octubre). Las mangueras y cables sueltos que estorbaban en la jardinera se recogieron.'],
 pair('441_antes_02', '441_despues_10', 'Orilla de la jardinera frente a la calle: crecida y perfilada (19 de septiembre).'),
 wide=strip([('369_antes_01', 'Pasto crecido (ago)'), ('369_despues_01', 'Cortado'), ('456_antes_03', 'Camino, antes (oct)'), ('456_despues_05', 'Después')], cols=4)))
parts.append(proj('Fumigación y bodega', 'Agosto–septiembre',
 ['Después de reportes de hormigas en AMB-05 y AMB-07, se fumigaron las ocho unidades entre el 25 y el 29 de agosto, y se repitió una aplicación preventiva en todas el 20 de septiembre, sellando las puertas durante el tratamiento.',
  'La bodega de la propiedad se vació, limpió y reorganizó el 16 de agosto para tener el material y las herramientas a la mano.'],
 pair('352_antes_01', '352_despues_01', 'Bodega: antes y después de la reorganización.'),
 wide=strip([('442_despues_01', 'Puertas selladas durante la fumigación'), ('442_despues_02', 'Aplicación en entradas'), ('189_despues_01', 'Tratamiento de hormigas'), ('442_despues_07', 'Unidad tratada')], cols=4)))
parts.append('</div></section>')

# CAPÍTULO 7 · HUÉSPED
HU = {348: 'Fallas eléctricas en la cocina: se botaban las pastillas y el triturador y el lavavajillas se quedaban sin corriente', 179: 'Internet sin servicio', 209: 'Base de la cama king rota', 231: 'Dos bases de cama twin rotas', 241: 'Faltan utensilios de cocina', 244: 'La unidad no estaba limpia a la llegada', 340: 'Refrigerador: revisión', 287: 'Asador sin gas', 302: 'Limpieza deficiente a la llegada (sábanas); se reembolsó la limpieza', 316: 'Persianas dañadas', 317: 'Control remoto de la TV no funcionaba', 374: 'Toallero desprendido de la pared', 355: 'Ropa olvidada: envío a la huésped', 360: 'Focos del ventilador fundidos', 446: 'El jacuzzi no calentaba', 195: 'Microondas echa humo y el extractor falla'}
hu = sorted([v for v in PER if v['reportado'] == 'Huésped'], key=lambda v: v['f_rep'])
rows = []
for v in hu:
    d = (date.fromisoformat(v['f_cierre']) - date.fromisoformat(v['f_rep'])).days if v['f_cierre'] else None
    res = ('el mismo día' if d == 0 else f'en {d} día{"s" if d != 1 else ""}') if d is not None else ('cerrado' if v['estatus'] in ('Terminado','Cerrada/Noprocede') else v['estatus'].lower())
    if v['id'] == 232: continue
    rcls = 'p-ok' if 'mismo' in res else ('p-decision' if 'pendiente' in res else 'p-programar')
    rows.append(f'<tr><td class="u">{E(unidad_txt(v))}</td><td class="f">{E(fd(v["f_rep"]))}</td><td>{E(HU.get(v["id"], titulo_limpio(v["resumen"])))}</td><td class="r"><span class="pill {rcls}">{E(res)}</span></td></tr>')
parts.append(cap_head(7, 'Atención al huésped',
 f'De los {n_per} trabajos del periodo, {n_huesped} empezaron con un mensaje de un huésped. Los otros {n_per-n_huesped} los detectó el equipo antes. Cuando el huésped escribe, lo que cuenta es la velocidad: esta es la lista completa de lo que reportaron y en cuánto se resolvió.'))
parts.append('<div class="tbl"><table class="hu"><tr><th>Unidad</th><th>Fecha</th><th>Lo que reportó el huésped</th><th>Se resolvió</th></tr>' + ''.join(rows) + '</table></div>')
parts.append('<div class="gal" style="margin-top:26px">' +
 pair('182_antes_02', '182_despues_02', 'AMB-01, 11 de septiembre: “the thermostat has no temp set”. Beto fue ese mismo día y el termostato volvió a responder.') +
 pair('411_antes_03', '335_despues_08_p09_06', 'Finales de julio: un huésped avisó que la alberca estaba sucia. Se cambió el filtro, se trató el agua y así quedó para la siguiente llegada.') +
 '</div>')
parts.append('<div class="nota sand"><b>Mensajes, reseñas y tiempos de respuesta.</b> Esta sección se completa con los datos de Airbnb del periodo (conversaciones atendidas, tasa y tiempo de respuesta, calificación y reseñas por mes). Se integran en la siguiente versión del informe.</div>')
parts.append('</div></section>')

# CAPÍTULO 8 · OCTUBRE
parts.append(cap_head(8, 'Octubre, en curso',
 f'Al 16 de octubre van {len(OCT)} trabajos nuevos, {sum(1 for v in OCT if v["estatus"]=="Terminado")} ya cerrados. Dos de ellos son de los más grandes del año: el calentador del jacuzzi y la reparación por las lluvias en tres unidades. El cierre completo del mes se entrega con el informe de octubre.'))
parts.append(proj('Jacuzzi: calentador nuevo y cuarto de máquinas reordenado', '8–12 de octubre · Blue Creek',
 ['Desde finales de septiembre la pantalla del calentador fallaba y Blue Creek advirtió que estaba por fallar. A principios de octubre dejó de funcionar del todo; se aprobó el reemplazo y el 8 de octubre el calentador nuevo quedó instalado y encendido.',
  'En la misma intervención se movió la bomba del jacuzzi del frente a la parte trasera, se reposicionaron las bombas y el filtro para que todo cupiera con el calentador nuevo, y se retiraron las cajas eléctricas viejas que ya no servían.'],
 cmp('462_antes_01', '462_despues_02_p04_03', 'Cuarto de máquinas del jacuzzi: la instalación anterior y el calentador nuevo ya conectado (8 de octubre).'),
 first=True,
 wide=strip([('462_despues_02_p02_01', 'Equipo viejo desmontado'), ('462_despues_02_p03_02', 'Bomba del spa movida atrás'), ('462_despues_02_p05_04', 'Bombas reposicionadas'), ('462_despues_02_p06_05', 'Filtro reposicionado'), ('462_despues_02_p07_06', 'Cajas eléctricas viejas retiradas'), ('446_antes_01_p04_03', 'El control del calentador anterior')], cols=6)))
parts.append(proj('Lluvias de octubre: AMB-01, AMB-03 y AMB-05', '5–12 de octubre · Beto',
 ['La lluvia del primer fin de semana de octubre entró por ventanas y techos en tres unidades: repisones de ventana hinchados, pintura desprendida en techos y esquinas, y una junta abierta en un marco. Lily lo reportó el 5 y Beto cerró las tres unidades el 12.',
  'Se secó, se resanó, se selló cada marco de ventana con poliuretano y se pintó. Son 35 fotos de antes y después; aquí van las principales.'],
 pair('451_antes_07', '451_despues_03', 'Repisón de ventana con el agua todavía encima, y el mismo marco sellado y pintado.'),
 wide=strip([('451_antes_14', 'Techo desprendido'), ('451_despues_06', 'Resanado'), ('451_antes_18', 'Moldura con agua'), ('451_despues_07', 'Sellada'), ('451_antes_19', 'Junta abierta en el marco'), ('451_despues_02', 'Sellada')], cols=6) +
      strip([('451_antes_22', 'Pared descascarada'), ('451_despues_10', 'Pintada'), ('451_antes_05', 'Marco de ventana, antes'), ('451_despues_04', 'Después'), ('451_antes_09', 'Techo manchado'), ('451_despues_09', 'Recámara terminada')], cols=6)))
parts.append(proj('Y lo demás de octubre', '1–16 de octubre',
 ['Máquina de limpieza de fondo para la alberca y limpieza tras las lluvias; chapas nuevas en AMB-01, 03 y 06; moho en la recámara principal de AMB-06 limpiado y sellado; corte de pasto y limpieza de exteriores; riel de regadera en AMB-04; bisagra en AMB-06; focos en AMB-01; faroles exteriores terminados.',
  'Pendientes al 16 de octubre: cambiar los aspersores de riego (corroídos), manguera nueva, soporte de cama en AMB-06, extractor de cocina en AMB-06 y reconectar los timbres Ring al internet.'],
 pair('467_antes_04', '467_despues_04', 'AMB-06: moho en la esquina de la recámara principal; limpiado, sellado y pintado (15 de octubre).'),
 wide=strip([('457_antes_02', 'Alberca tras las lluvias'), ('457_despues_02', 'Aspirada'), ('454_despues_01', 'AMB-03: chapa nueva'), ('463_despues_01', 'AMB-04: riel de regadera'), ('460_antes_05', 'Aspersores corroídos (pendiente)'), ('453_despues_01', 'Patio lavado (10 oct)')], cols=6)))
parts.append('</div></section>')

# CAPÍTULO 9 · LO QUE SIGUE
pend = sorted([v for v in INC.values() if v['estatus'] in ('Pendiente', 'Cotizando', 'Pendiente de Aprobación', 'Sin estatus') and v['id'] != 266], key=lambda v: (v['f_rep'] or '9999'))
def pill(v):
    if v['estatus'] == 'Cotizando' or v['id'] in (201, 183, 1, 311): return '<span class="pill p-decision">Decisión</span>'
    if v['id'] in (210, 231, 232, 252, 450, 419, 460, 458, 464, 466, 455, 182, 368, 195, 376, 303, 258): return '<span class="pill p-proceso">En proceso</span>'
    return '<span class="pill p-programar">Programar</span>'
NOTAS = {1: 'Panel eléctrico de la alberca, corroído. La energía está restablecida; Blue Creek recomienda reemplazarlo antes de la próxima temporada. Requiere aprobación.',
 201: 'Sofá cama de AMB-04 quebrado; requiere reemplazo. Falta elegir modelo y aprobar.', 183: 'Colchón de AMB-01 hundido; conviene cambiar la base (box). Falta aprobar.',
 231: 'Dos bases de cama twin de AMB-01: compradas, falta armarlas e instalarlas.',
 210: 'Detector de AMB-01: comprado, falta instalarlo.', 252: 'Detectores: instalados en cinco unidades; completar AMB-01, 04 y 08.',
 450: 'Biseles de luces de pasillo: siete colocados, faltan piezas por llegar.', 182: 'Termostato de AMB-01 cambiado en octubre; verificar que enfríe bien.', 368: 'Termostato de AMB-07: sigue sin enfriar bien; revisar el equipo.',
 311: 'Persianas de AMB-05: falta comprar las de la medida correcta.', 195: 'Microondas de AMB-08 echa humo y el extractor falla; revisar o reemplazar.', 376: 'Piezas del refrigerador de AMB-02 (rejilla); pedir repuesto.',
 303: 'Microondas de AMB-04, viejo; cotizar reemplazo.', 258: 'Cubierta de cocina de AMB-07 por reemplazar.', 419: 'Limpieza profunda de sillones en cinco unidades; programar.', 460: 'Aspersores de riego corroídos; cambiar.',
 223: 'Revisar lavadora de AMB-07.', 228: 'Plomería pendiente en AMB-05, 06 y 08.', 217: 'Tostador de AMB-04 por reemplazar.', 241: 'Reponer utensilios en AMB-07.', 365: 'Comprar trapeador y recogedor para AMB-03.',
 415: 'Caulking en conector, AMB-02.', 416: 'Buró despintado en AMB-02; restaurar.', 455: 'Reconectar los timbres Ring al internet.', 458: 'Comprar manguera nueva.', 464: 'Soporte de cama caído en AMB-06.', 466: 'Extractor de cocina de AMB-06 no funciona.',
 249: 'Llaves: ya hay copias de AMB-01 y 02; completar el juego para el resto.', 255: 'Comprar salvavidas para la alberca.', 263: 'Poner tapete o cepillo para retirar la arena antes de entrar a las unidades.', 319: 'Reglas de la alberca: definir material del letrero.', 447: 'Compra de tapetes para las ocho unidades.', 266: 'Puertas: las ocho están terminadas; falta cerrar el registro.'}
rows = []
for v in pend:
    if v['id'] == 232: continue
    rows.append(f'<tr><td class="u">{E(unidad_txt(v))}</td><td>{E(NOTAS.get(v["id"], v["resumen"]))}</td><td class="s">{pill(v)}</td></tr>')
parts.append(cap_head(9, 'Lo que sigue',
 'Los trabajos abiertos al 16 de octubre, con lo que falta para cerrarlos. Los marcados como “Decisión” necesitan una autorización de los socios; el resto está en manos del equipo.'))
cols = {'dec': [], 'pro': [], 'prg': []}
for v in pend:
    if v['id'] == 232: continue
    pl = pill(v); g = 'dec' if 'Decisión' in pl else ('pro' if 'En proceso' in pl else 'prg')
    cols[g].append(f'<div class="item"><b>{E(unidad_txt(v))}</b>{E(NOTAS.get(v["id"], v["resumen"]))}</div>')
parts.append('<div class="cols3">'
 + f'<div class="col c-dec"><h3>Decisión de los socios<small>{len(cols["dec"])} temas que necesitan autorización</small></h3>{"".join(cols["dec"])}</div>'
 + f'<div class="col c-pro"><h3>En proceso<small>{len(cols["pro"])} trabajos ya en manos del equipo</small></h3>{"".join(cols["pro"])}</div>'
 + f'<div class="col c-prg"><h3>Por programar<small>{len(cols["prg"])} pendientes menores</small></h3>{"".join(cols["prg"])}</div>'
 + '</div>')
parts.append('</div></section>')

# ANEXO POR UNIDAD
EXCL = set('''266_fotos_01 266_fotos_02 266_fotos_03 266_fotos_04 266_fotos_05 266_fotos_06 266_fotos_07 408_antes_01 408_antes_05 408_fotos_01 174_fotos_01 174_fotos_02
382_antes_03 382_antes_04 382_antes_14 379_fotos_01 430_fotos_01 351_fotos_01 397_fotos_01 397_fotos_02 467_despues_07 252_fotos_01 252_fotos_02 252_fotos_03
454_antes_02 454_despues_03 249_despues_01 235_despues_01 278_despues_01 279_despues_01 280_despues_01 281_despues_01 342_despues_01 182_antes_07 182_antes_08 220_despues_04 348_fotos_01 348_fotos_02 448_despues_02 189_antes_01 442_antes_01 443_fotos_01 302_fotos_01'''.split())
UNITS = ['AMB-01', 'AMB-02', 'AMB-03', 'AMB-04', 'AMB-05', 'AMB-06', 'AMB-07', 'AMB-08']
def primary(v):
    us = [u.strip().upper() for u in v['unidades']]
    for u in UNITS:
        if u in us: return u
    return 'COMUN'
groups = defaultdict(list)
for v in INC.values():
    if v['cap'] is None: continue
    groups[primary(v)].append(v)
EXTRA_PDF = {462: ['462_despues_02_p02_01', '462_despues_02_p03_02', '462_despues_02_p04_03', '462_despues_02_p05_04', '462_despues_02_p06_05', '462_despues_02_p07_06']}
def inc_block(v):
    fotos = [f for f in v['fotos'] if f not in EXCL] + EXTRA_PDF.get(v['id'], [])
    est = {'Sin estatus': 'Registrado', 'Cerrada/Noprocede': 'Cerrado'}.get(v['estatus'], v['estatus'])
    hd = (f'<div class="hd"><span class="id">#{v["id"]}</span><span class="ti">{E(titulo_limpio(v["resumen"], v["id"]))}</span>'
          f'<span class="dt">{E(fd(v["f_rep"]))}' + (f' → {E(fd(v["f_cierre"]))}' if v['f_cierre'] else '') + f' · {E(est)}</span></div>')
    un = unidad_txt(v); who = {'Mantenimiento': 'mantenimiento', 'Limpieza': 'limpieza', 'Huésped': 'huésped', 'Miguel': 'administración', 'Melanny': 'administración'}.get(v['reportado'] or '', '')
    prov = ', '.join(p.split(' —')[0].replace('Filiberto Gonzalez (Beto)', 'Beto') for p in v['proveedor'])
    meta = ' · '.join(x for x in [un if len(v['unidades']) > 1 else '', f'reportó: {who}' if who else '', prov] if x)
    ds = f'<div class="ds">{E(meta)}</div>' if meta else ''
    th = ''
    if fotos:
        cells = []
        for f in fotos:
            slot = f.split('_')[1]
            tag = {'antes': 'A', 'despues': 'D'}.get(slot)
            cls = {'antes': 't-antes', 'despues': 't-despues'}.get(slot, 't-neutral')
            cells.append(f'<div class="ph">{img_tag(f, 200, 58, "center", False, "(max-width: 720px) 25vw, 120px", "")}' + (f'<span class="tag {cls}">{tag}</span>' if tag else '') + '</div>')
        th = f'<div class="thumbs">{"".join(cells)}</div>'
    return f'<div class="apx-inc">{hd}{ds}{th}</div>'
parts_index = parts
parts = [head('Por unidad · Amberjack 2026', 'Todos los trabajos de Amberjack 1–8 con sus fotos, por unidad.', home=False)]
parts.append('<section class="cap" id="anexo"><div class="in cap-body" style="padding-top:40px"><div class="cap-head"><div class="num">Anexo</div><h2>Todos los trabajos, por unidad</h2><p class="intro">Cada trabajo registrado de junio al 16 de octubre, con todas sus fotos tal como se subieron a la bitácora. <span class="pill p-programar" style="background:var(--sandbg);color:var(--sand)">A</span> antes, <span class="pill p-proceso">D</span> después. Los trabajos que abarcan varias unidades aparecen en la primera de ellas.</p></div><div class="filters" id="filters"><button type="button" data-unit="all" aria-pressed="true">Todas</button>' + ''.join(f'<button type="button" data-unit="{u}" aria-pressed="false">{u if u != "COMUN" else "Áreas comunes"}</button>' for u in UNITS + ['COMUN']) + '</div><div id="apx">')
firstu = True
for u in UNITS + ['COMUN']:
    vs = sorted(groups[u], key=lambda v: (v['f_rep'] or '9999', v['id']))
    if not vs: continue
    title = u if u != 'COMUN' else 'Áreas comunes, alberca y edificio'
    nf = sum(len([f for f in v['fotos'] if f not in EXCL]) for v in vs)
    nc = sum(1 for v in vs if v['estatus'] in ('Terminado', 'Cerrada/Noprocede'))
    parts.append(f'<div class="apx-unit {"first" if firstu else ""}" data-unit="{u}"><h2>{E(title)}</h2>'); firstu = False
    parts.append(f'<div class="sum">{len(vs)} trabajos · {nc} cerrados · {nf} fotos</div>' + ''.join(inc_block(v) for v in vs) + '</div>')

parts.append('</div></div></section>')
FOOTER = f"""<footer class="band"><div class="in"><div><b>Wanderhaus</b>Administración y mantenimiento de Amberjack 1–8 para Casasole LP</div><div>Datos y fotos: bitácora de mantenimiento, corte al 16 de octubre de 2026.<br>Este informe se actualiza cada mes en esta misma dirección. <a class="out" href="logout" style="color:inherit">Cerrar sesión</a></div></div></footer>
<script src="js/site.js?v={VER}" defer></script>
</body></html>"""
parts_anexo = parts + [FOOTER]
parts_index = parts_index + [FOOTER]
open(os.path.join(SITE, 'index.html'), 'w').write(''.join(parts_index))
open(os.path.join(SITE, 'unidades.html'), 'w').write(''.join(parts_anexo))
os.makedirs(os.path.join(SITE, 'css'), exist_ok=True); os.makedirs(os.path.join(SITE, 'js'), exist_ok=True)
open(os.path.join(SITE, 'css', 'site.css'), 'w').write(CSS + SITE_EXTRA_CSS)
open(os.path.join(SITE, 'js', 'site.js'), 'w').write(SITE_JS)
open(os.path.join(SITE, 'favicon.svg'), 'w').write(FAVICON)
import glob as _g
n_img = len(_g.glob(os.path.join(SITE, 'img', '*.webp'))); sz = sum(os.path.getsize(p) for p in _g.glob(os.path.join(SITE, 'img', '*.webp')))
print('OK site:', 'index', round(os.path.getsize(os.path.join(SITE,'index.html'))/1e3), 'KB; unidades', round(os.path.getsize(os.path.join(SITE,'unidades.html'))/1e3), 'KB;', n_img, 'imgs', round(sz/1e6,1), 'MB')
