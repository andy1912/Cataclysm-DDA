#!/usr/bin/env python3
"""Write the small fixture tests/saigon_realmap_test.cpp loads: overmap (40,40) of
data/mods/saigon_2000s/realmap_test, a field with one road and one five-storey shophouse
column (z 0-5), so the test can check that every layer loads and nothing procedural is added.
Overmap (40, 40) so no other test has saved it (saved overmaps load before pregenerated ones).
Run from the repo root:  python3 tools/saigon/realmap/make_test_fixture.py
"""
import os
import sys

sys.path.insert( 0, os.path.dirname( __file__ ) )
from omap import Overmap  # noqa: E402

om = Overmap( 40, 40 )
for x in range( 80, 101 ):
    om.set( x, 90, 0, 'road_ew' )
for z in range( 0, 6 ):
    om.set( 90, 89, z, 'sgn_nh_solo_z%d_south' % z )
print( om.write( 'data/mods/saigon_2000s/realmap_test' ) )
