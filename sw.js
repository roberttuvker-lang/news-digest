/* Brighter — offline shell.
 *
 * Two rules, and no more than two:
 *
 *   1. The shell (page, icons, manifest) is cache-first. It changes rarely, so
 *      serving it from disk is why the installed app opens instantly.
 *   2. The news (data.js) is network-first with a cache fallback. It changes
 *      three times a day, so the network wins when there is one, and the last
 *      issue is still there when there is not.
 *
 * CACHE is stamped by add.py from the same timestamp it writes onto
 * data.js?v=. Never edit it by hand — a forgotten bump means the phone serves
 * yesterday's news forever, and it looks like the routine broke.
 */
var CACHE = "brighter-20260730070623";

var SHELL = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./favicon.ico",
  "./icons/icon-192.png",
  "./icons/icon-512.png"
];

self.addEventListener("install", function (e) {
  e.waitUntil(
    // addAll is all-or-nothing: one 404 and the whole worker fails to install,
    // leaving no offline copy at all. Individual puts degrade instead.
    caches.open(CACHE).then(function (c) {
      return Promise.all(SHELL.map(function (url) {
        return c.add(url).catch(function () {});
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        return k === CACHE ? null : caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET") return;

  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // The news: network first.
  if (url.pathname.indexOf("data.js") !== -1) {
    e.respondWith(
      fetch(req).then(function (res) {
        var copy = res.clone();
        caches.open(CACHE).then(function (c) { c.put(req, copy); });
        return res;
      }).catch(function () {
        // Offline. Ignore the ?v= cache-buster so yesterday's copy still
        // matches today's request — without ignoreSearch the app would open
        // blank on a train.
        return caches.match(req, { ignoreSearch: true });
      })
    );
    return;
  }

  // The shell: cache first, refreshed quietly in the background.
  e.respondWith(
    caches.match(req, { ignoreSearch: true }).then(function (hit) {
      var net = fetch(req).then(function (res) {
        var copy = res.clone();
        caches.open(CACHE).then(function (c) { c.put(req, copy); });
        return res;
      }).catch(function () { return hit; });
      return hit || net;
    })
  );
});
