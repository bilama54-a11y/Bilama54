const CACHE = 'matchlab-v2';
const STATIC_FILES = ['/', '/index.html', '/manifest.webmanifest', '/icons/matchlab.svg', '/icons/matchlab-192.png', '/icons/matchlab-512.png', '/teams/arsenal.svg', '/teams/leeds.svg', '/fonts/manrope.woff2', '/fonts/dm-sans.woff2'];
self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const response = await fetch('/index.html', { cache: 'reload' });
    const html = await response.text();
    const entries = [...html.matchAll(/(?:src|href)="([^"]+)"/g)].map(match => match[1]).filter(url => url.startsWith('/assets/') && /\.(js|css)$/.test(url));
    const cache = await caches.open(CACHE);
    await cache.addAll([...STATIC_FILES, ...entries]);
    await self.skipWaiting();
  })());
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith('matchlab-') && key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
// Ressources publiques de même origine : leur contenu ne dépend pas de l’en-tête Origin.
// ignoreVary permet aussi le rechargement hors ligne des modules CORS préchargés.
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET' || new URL(event.request.url).origin !== self.location.origin) return;
  event.respondWith(fetch(event.request).then(response => {
    if (response.ok) { const copy = response.clone(); caches.open(CACHE).then(cache => cache.put(event.request, copy)).catch(() => {}); }
    return response;
  }).catch(async () => (await caches.match(event.request, { ignoreVary: true })) || (event.request.mode === 'navigate' ? await caches.match('/index.html', { ignoreVary: true }) : Response.error())));
});
