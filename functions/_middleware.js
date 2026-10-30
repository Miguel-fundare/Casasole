// Acceso con usuario y contraseña para casasole.com (Cloudflare Pages Functions).
// Variables de entorno (Settings → Environment variables, tipo "Secret"):
//   AUTH_USERS  = "usuario:contraseña;otro:contraseña2"   (una cuenta por socio, o una compartida)
//   AUTH_SECRET = texto largo y aleatorio (firma las sesiones; si lo cambias, todos vuelven a entrar)
// Rutas: /login (pantalla de acceso), /logout (cerrar sesión). Todo lo demás requiere sesión.

const COOKIE = 'cs_sesion';
const DIAS = 30;

export async function onRequest(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);
  const path = url.pathname;

  if (path === '/login') return login(request, env, url);
  if (path === '/logout') return logout(url);
  if (path === '/robots.txt') return new Response('User-agent: *\nDisallow: /\n', { headers: { 'content-type': 'text/plain' } });

  const user = await sesionValida(request, env);
  if (!user) {
    if (path.startsWith('/img/') || path.startsWith('/css/') || path.startsWith('/js/')) {
      return new Response('No autorizado', { status: 401 });
    }
    const siguiente = encodeURIComponent(path + url.search);
    return Response.redirect(`${url.origin}/login?next=${siguiente}`, 302);
  }

  const res = await next();
  const out = new Response(res.body, res);
  out.headers.set('X-Robots-Tag', 'noindex, nofollow');
  out.headers.set('X-Frame-Options', 'SAMEORIGIN');
  out.headers.set('Referrer-Policy', 'same-origin');
  if (path.startsWith('/img/')) out.headers.set('Cache-Control', 'private, max-age=31536000, immutable');
  else if (path.startsWith('/css/') || path.startsWith('/js/')) out.headers.set('Cache-Control', 'private, max-age=604800');
  else out.headers.set('Cache-Control', 'private, no-cache');
  return out;
}

// ---------------------------------------------------------------- cuentas
function cuentas(env) {
  const raw = (env.AUTH_USERS || '').trim();
  const map = new Map();
  if (!raw) return map;
  for (const par of raw.split(/[;\n]/)) {
    const i = par.indexOf(':');
    if (i > 0) map.set(par.slice(0, i).trim().toLowerCase(), par.slice(i + 1).trim());
  }
  return map;
}

function igual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

// ---------------------------------------------------------------- sesiones firmadas
async function firmar(texto, secreto) {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secreto), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(texto));
  return [...new Uint8Array(sig)].map(b => b.toString(16).padStart(2, '0')).join('');
}

async function crearSesion(usuario, env) {
  const exp = Date.now() + DIAS * 86400 * 1000;
  const cuerpo = `${btoa(unescape(encodeURIComponent(usuario)))}.${exp}`;
  const sig = await firmar(cuerpo, env.AUTH_SECRET || 'sin-secreto');
  return `${cuerpo}.${sig}`;
}

async function sesionValida(request, env) {
  const m = (request.headers.get('Cookie') || '').match(new RegExp(`(?:^|;\\s*)${COOKIE}=([^;]+)`));
  if (!m) return null;
  const partes = m[1].split('.');
  if (partes.length !== 3) return null;
  const [u64, exp, sig] = partes;
  if (Number(exp) < Date.now()) return null;
  const esperada = await firmar(`${u64}.${exp}`, env.AUTH_SECRET || 'sin-secreto');
  if (!igual(sig, esperada)) return null;
  try { return decodeURIComponent(escape(atob(u64))); } catch { return null; }
}

function cookie(valor, maxAge) {
  return `${COOKIE}=${valor}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAge}`;
}

// ---------------------------------------------------------------- login / logout
async function login(request, env, url) {
  let next = url.searchParams.get('next') || '/';
  let error = '';
  if (request.method === 'POST') {
    const form = await request.formData();
    const usuario = String(form.get('usuario') || '').trim().toLowerCase();
    const clave = String(form.get('clave') || '');
    next = String(form.get('next') || next);
    const lista = cuentas(env);
    if (lista.size === 0) {
      error = 'El sitio todavía no tiene cuentas configuradas (variable AUTH_USERS).';
    } else if (lista.has(usuario) && igual(lista.get(usuario), clave)) {
      const valor = await crearSesion(usuario, env);
      if (!next.startsWith('/') || next.startsWith('//')) next = '/';
      return new Response(null, { status: 303, headers: { Location: next, 'Set-Cookie': cookie(valor, DIAS * 86400) } });
    } else {
      error = 'Usuario o contraseña incorrectos.';
    }
  }
  return new Response(paginaLogin(next, error), { status: error ? 401 : 200, headers: { 'content-type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex' } });
}

function logout(url) {
  return new Response(null, { status: 303, headers: { Location: `${url.origin}/login`, 'Set-Cookie': cookie('', 0) } });
}

function esc(s) { return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }

function paginaLogin(next, error) {
  return `<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>Acceso · Casasole</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500&family=Inter:wght@400;500;600&display=swap">
<style>
:root{--navy:#0F2B46;--navy2:#143A5C;--teal:#1C7293;--sand:#C9A86A;--fg:#1B2730;--muted:#5B6B78;--rule:#D8E1E7}
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--navy);font-family:Inter,"Helvetica Neue",Arial,sans-serif;color:var(--fg);padding:24px}
.card{width:100%;max-width:400px;background:#fff;border-radius:16px;padding:34px 30px 30px;box-shadow:0 20px 50px rgba(0,0,0,.35)}
.k{font-size:11.5px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--teal);margin:0 0 6px}
h1{font-family:Newsreader,Georgia,serif;font-weight:500;font-size:30px;line-height:1.05;margin:0 0 6px;color:var(--navy)}
p.s{margin:0 0 22px;color:var(--muted);font-size:14.5px}
label{display:block;font-size:13px;font-weight:600;margin:14px 0 6px;color:var(--navy)}
input{width:100%;font:inherit;font-size:16px;padding:11px 12px;border:1px solid var(--rule);border-radius:9px;background:#fff;color:var(--fg)}
input:focus{outline:2px solid var(--teal);outline-offset:1px;border-color:var(--teal)}
button{width:100%;margin-top:22px;font:inherit;font-weight:600;font-size:15px;padding:12px;border:0;border-radius:9px;background:var(--navy);color:#fff;cursor:pointer}
button:hover{background:var(--navy2)}
.err{background:#FBF1E4;color:#8A4A0B;border-radius:8px;padding:10px 12px;font-size:14px;margin-top:16px}
.f{margin-top:22px;font-size:12.5px;color:var(--muted);text-align:center}
</style></head><body>
<form class="card" method="post" action="/login" autocomplete="on">
  <p class="k">Casasole LP · Amberjack 1–8</p>
  <h1>Informe para los socios</h1>
  <p class="s">Acceso privado. Escribe el usuario y la contraseña que te compartió la administración.</p>
  <input type="hidden" name="next" value="${esc(next)}">
  <label for="usuario">Usuario</label>
  <input id="usuario" name="usuario" type="text" autocapitalize="none" autocorrect="off" autocomplete="username" required autofocus>
  <label for="clave">Contraseña</label>
  <input id="clave" name="clave" type="password" autocomplete="current-password" required>
  ${error ? `<div class="err">${esc(error)}</div>` : ''}
  <button type="submit">Entrar</button>
  <p class="f">Wanderhaus LLC · administración y mantenimiento</p>
</form>
</body></html>`;
}
