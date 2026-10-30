# casasole.com · Informe para los socios de Casasole LP

Sitio privado (usuario y contraseña) con el programa de renovación y operación de Amberjack 1–8.
Se publica en **Cloudflare Pages** desde este repositorio: cada vez que se sube un cambio a `main`, el sitio se actualiza solo en uno o dos minutos.

```
site/        ← el sitio (lo que se publica): index.html, unidades.html, css/, js/, img/ (fotos en WebP)
functions/   ← pantalla de acceso y control de sesión (Cloudflare Pages Functions)
build/       ← scripts y datos con los que se genera el sitio desde la bitácora de Airtable
archivo/     ← presentación anterior (junio 2026)
```

## Publicar por primera vez (10 minutos)

1. **GitHub.** Este repositorio debe ser **privado**: Settings → General → Danger Zone → *Change visibility* → Private.
2. **Cloudflare.** Crea una cuenta gratis en cloudflare.com (o entra a la que ya tengas).
3. **Workers & Pages → Create → Pages → Connect to Git.** Autoriza GitHub y elige `Miguel-fundare/casasole`.
   - Production branch: `main`
   - Framework preset: `None`
   - Build command: *(vacío)*
   - Build output directory: `site`
   - *Save and Deploy*. En un minuto tienes el sitio en `casasole-xxx.pages.dev`, ya con pantalla de acceso.
4. **Cuentas.** En el proyecto: Settings → Environment variables → Production → *Add variable*, las dos como **Secret** (Encrypt):
   - `AUTH_USERS` → las cuentas, separadas por punto y coma: `socio1:Clave-Segura-1;socio2:Clave-Segura-2`
     (puede ser una cuenta por socio o una sola compartida; el usuario no distingue mayúsculas, la contraseña sí).
   - `AUTH_SECRET` → cualquier texto largo y aleatorio (30+ caracteres). Firma las sesiones.
   Después: Deployments → el último → *Retry deployment*, para que tome las variables.
5. **Dominio.** Custom domains → *Set up a custom domain* → `casasole.com` (y otra vez para `www.casasole.com`).
   - Si el dominio se compró en Cloudflare, queda listo solo.
   - Si se compró en otro lado (GoDaddy, Namecheap…), Cloudflare muestra el registro CNAME que hay que poner ahí, o se cambian los nameservers a Cloudflare.
6. Abre `casasole.com`: debe pedir usuario y contraseña. Listo.

## Cuentas y accesos

- Alta o baja de un socio: edita `AUTH_USERS` y vuelve a desplegar (Retry deployment).
- Sacar a todos (por ejemplo, si se filtró una contraseña): cambia `AUTH_SECRET`; todas las sesiones caducan y hay que volver a entrar.
- La sesión dura 30 días en cada teléfono o computadora; `/logout` cierra la sesión.
- Nada se ve sin entrar: ni las páginas ni las fotos. El sitio está marcado como no indexable para Google.

## Actualización mensual

1. Se vuelve a generar el sitio desde la bitácora (Airtable) con los scripts de `build/`.
2. Se sube el cambio a `main` (`git push`).
3. Cloudflare publica solo. Los socios ven la versión nueva en la misma dirección, sin reinstalar nada.

## Costos

- Cloudflare Pages: gratis (hasta 100,000 visitas a archivos por día, más que suficiente).
- Dominio: lo que cobre el registrador (≈ 10–15 USD al año).
