/* Real-map Saigon: everything the converter reads, for the 5 x 4 overmap box
   (S 10.729, W 106.624, N 10.886, E 106.821; doc/saigon/REALMAP_IMAGE_SPEC.md §5).
   Data © OpenStreetMap contributors, ODbL 1.0. */
[out:json][timeout:300][maxsize:536870912];
(
  way["railway"="rail"](10.729,106.624,10.886,106.821);
  way["waterway"~"^(river|canal|stream)$"](10.729,106.624,10.886,106.821);
  way["natural"="water"](10.729,106.624,10.886,106.821);
  relation["natural"="water"](10.729,106.624,10.886,106.821);
  way["landuse"](10.729,106.624,10.886,106.821);
  relation["landuse"](10.729,106.624,10.886,106.821);
  way["leisure"~"^(park|garden|stadium|pitch)$"](10.729,106.624,10.886,106.821);
  way["aeroway"~"^(aerodrome|runway|taxiway|apron)$"](10.729,106.624,10.886,106.821);
);
out body geom qt;
