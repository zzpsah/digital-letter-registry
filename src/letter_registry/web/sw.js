const CACHE="dlr-shell-v1";
const SHELL=["/","/manifest.webmanifest"];

self.addEventListener("install",event=>{
  event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate",event=>{
  event.waitUntil(
    caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener("fetch",event=>{
  const url=new URL(event.request.url);
  if(event.request.method!=="GET" || url.pathname.startsWith("/api/")){
    return;
  }
  if(url.origin!==self.location.origin){
    return;
  }
  event.respondWith(
    caches.match(event.request).then(hit=>hit||fetch(event.request))
  );
});
