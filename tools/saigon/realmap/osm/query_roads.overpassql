/* Real-map Saigon: everything the converter reads, for the 5 x 4 overmap box
   (S 10.729, W 106.624, N 10.886, E 106.821; doc/saigon/REALMAP_IMAGE_SPEC.md §5).
   Data © OpenStreetMap contributors, ODbL 1.0. */
[out:json][timeout:300][maxsize:536870912];
(
  way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|living_street|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link)$"](10.729,106.624,10.886,106.821);
);
out tags geom qt;
