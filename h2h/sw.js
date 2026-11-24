/* H2H Scanner — Service Worker
   data/*.json -> network-first (cotes toujours fraîches)
   navigations -> network-first + cache
   assets      -> cache-first + rafraîchissement
*/
const CACHE = 'h2hscan-v1';
const SHELL = [
  './', './index.html', './manifest.webmanifest',
  './icon.svg', './icon-192.png', './icon-512.png', './apple-touch-icon.png'
];

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await Promise.all(SHELL.map(async url => {
      try { await cache.add(new Request(url, { cache: 'reload' })); } catch (e) {}
    }));
    try { await cache.add(new Request('./data/h2h-odds.json', { cache: 'reload' })); } catch (e) {}
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

const isData = url => /\.json(\?|$)/.test(url.pathname + (url.search || ''));

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (isData(url)) {
    event.respondWith((async () => {
      try {
        const fresh = await fetch(req, { cache: 'no-store' });
        if (fresh && fresh.ok) caches.open(CACHE).then(c => c.put(req, fresh.clone())).catch(() => {});
        return fresh;
      } catch (e) {
        const hit = await caches.match(req, { ignoreSearch: true });
        return hit || new Response('{"matches":[]}', { headers: { 'Content-Type': 'application/json' }, status: 503 });
      }
    })());
    return;
  }

  if (req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html')) {
    event.respondWith((async () => {
      try {
        const fresh = await fetch(req);
        if (fresh && fresh.ok) caches.open(CACHE).then(c => c.put(req, fresh.clone())).catch(() => {});
        return fresh;
      } catch (e) {
        return (await caches.match(req)) || (await caches.match('./index.html')) ||
          new Response('<h1>Hors-ligne</h1>', { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
      }
    })());
    return;
  }

  event.respondWith((async () => {
    const hit = await caches.match(req);
    if (hit) {
      fetch(req).then(r => { if (r && r.ok) caches.open(CACHE).then(c => c.put(req, r)).catch(() => {}); }).catch(() => {});
      return hit;
    }
    try {
      const resp = await fetch(req);
      if (resp && resp.ok) caches.open(CACHE).then(c => c.put(req, resp.clone())).catch(() => {});
      return resp;
    } catch (e) {
      return caches.match('./index.html');
    }
  })());
});
