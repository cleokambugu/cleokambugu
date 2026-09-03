// UG service worker.
//
// The shell works offline; the API is always live. One rule matters more than the rest:
//
//   THE DOCUMENT IS NETWORK-FIRST.
//
// It used to be cache-first like everything else, keyed to a hand-edited version string. That
// meant an installed user kept being served a frozen index.html — a frozen price table, a frozen
// safety claim, a frozen quality board — until somebody remembered to bump a constant. A reviewer
// saw two different versions of this product inside one session because of it. On a page whose
// whole argument is that the numbers are honest, serving a stale copy is not a caching decision,
// it is a correctness bug.
//
// So: the document goes to the network first and falls back to cache only when offline. Static
// shell assets stay cache-first, because a frozen icon hurts nobody.
const CACHE = 'ug-shell-v1.4.0';
const SHELL = ['./', './index.html', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png'];

/* The forty language packs. The document used to carry all of them and cost four seconds of every
   cold load; now a person fetches only the one they chose. The cost of that trade is that the FIRST
   switch to a new language needs the network — so once the shell is in, warm them all in the
   background, quietly, one at a time, at the lowest priority the platform gives us. After that the
   picker is instant and works on a dead connection, which is the promise the welcome screen makes. */
const PACK_DIR = './i18n/';
async function warmPacks(codes) {
  const c = await caches.open(CACHE);
  for (const code of codes) {
    const url = PACK_DIR + code + '.json';
    if (await c.match(url)) continue;
    try { const r = await fetch(url, { cache: 'no-cache' }); if (r && r.ok) await c.put(url, r.clone()); } catch { /* try again next activation */ }
  }
}

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL).catch(() => {})).then(() => self.skipWaiting()));
});
self.addEventListener('message', (e) => {
  if (e.data && e.data.type === 'warm-packs' && Array.isArray(e.data.codes)) e.waitUntil(warmPacks(e.data.codes));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys()
    .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

const isDocument = (req, url) =>
  req.mode === 'navigate' || req.destination === 'document' ||
  url.pathname === '/' || url.pathname.endsWith('/') || url.pathname.endsWith('.html');

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.pathname.includes('/api/')) return;
  if (url.origin !== location.origin) return;            // fonts and CDNs go straight to the network

  if (isDocument(e.request, url)) {
    // Always try the live page. Cache is the offline fallback, never the default answer.
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          if (res && res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(e.request, copy)); }
          return res;
        })
        .catch(() => caches.match(e.request).then((hit) => hit || caches.match('./index.html')))
    );
    return;
  }

  // Everything else: cache first, refreshed in the background.
  e.respondWith(caches.match(e.request).then((hit) => {
    const net = fetch(e.request).then((res) => {
      if (res && res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(e.request, copy)); }
      return res;
    }).catch(() => hit);
    return hit || net;
  }));
});
