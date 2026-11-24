/* UCL Over/Under 2026-27 — Service Worker
   Stratégies :
   - data/*.json  -> network-first (jamais de données périmées quand Internet est là)
   - navigation   -> network-first + fallback cache (app shell hors-ligne)
   - assets       -> cache-first + mise à jour en tâche de fond
*/
const CACHE = 'uclou-v1';
const SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icon.svg',
  './icon-192.png',
  './icon-512.png',
  './apple-touch-icon.png'
];

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await Promise.all(SHELL.map(async url => {
      try { await cache.add(new Request(url, { cache: 'reload' })); } catch (e) { /* on continue */ }
    }));
    // pré-cache du dernier instantané si disponible (ignore l'échec)
    try { await cache.add(new Request('./data/ucl-2026-27.json', { cache: 'reload' })); } catch (e) {}
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

const isData = url => /\/data\/.*\.json(\?|$)/.test(url.pathname + (url.search || ''));

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Domaines tiers (ESPN, raw.githubusercontent) : laisser le réseau décider, pas de cache opaque
  if (url.origin !== self.location.origin) return;

  // 1) Données : réseau d'abord
  if (isData(url)) {
    event.respondWith((async () => {
      try {
        const fresh = await fetch(req, { cache: 'no-store' });
        if (fresh && fresh.ok) {
          const cache = await caches.open(CACHE);
          cache.put(req, fresh.clone()).catch(() => {});
        }
        return fresh;
      } catch (e) {
        const hit = await caches.match(req, { ignoreSearch: true });
        if (hit) return hit;
        return new Response(JSON.stringify({ error: 'offline', teams: [] }), {
          headers: { 'Content-Type': 'application/json' }, status: 503
        });
      }
    })());
    return;
  }

  // 2) Pages : réseau d'abord, puis cache
  if (req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html')) {
    event.respondWith((async () => {
      try {
        const fresh = await fetch(req);
        if (fresh && fresh.ok) {
          const cache = await caches.open(CACHE);
          cache.put(req, fresh.clone()).catch(() => {});
        }
        return fresh;
      } catch (e) {
        return (await caches.match(req)) || (await caches.match('./index.html')) ||
          new Response('<h1>Hors-ligne</h1>', { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
      }
    })());
    return;
  }

  // 3) Assets : cache d'abord
  event.respondWith((async () => {
    const hit = await caches.match(req);
    if (hit) {
      fetch(req).then(resp => {
        if (resp && resp.ok) caches.open(CACHE).then(c => c.put(req, resp)).catch(() => {});
      }).catch(() => {});
      return hit;
    }
    try {
      const resp = await fetch(req);
      if (resp && resp.ok) {
        const cache = await caches.open(CACHE);
        cache.put(req, resp.clone()).catch(() => {});
      }
      return resp;
    } catch (e) {
      return caches.match('./index.html');
    }
  })());
});
