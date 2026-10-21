#include <string>
#include "cata_catch.h"
#include "display_buffer_coords.h"
#include "point.h"

// Saigon fork, A1: in the tiles build a click has to land on the tile under the pointer.
// SDL gives the click in render (drawable pixel) coordinates; the game's display buffer is
// blitted into those pixels at an integer scale (src/sdltiles.cpp
// get_display_buffer_render_rect), so the click must be scaled back into the buffer.  The
// first playtest on a Retina Mac found clicks landing twice as far from the top-left corner
// as the pointer: the scale-back was missing.
// Run with: tests/cata_test "[saigon]"

TEST_CASE( "saigon_mouse_click_maps_to_display_buffer", "[saigon]" )
{
    SECTION( "Retina: two drawable pixels per window point" ) {
        // a 1280x800-point window, 2560x1600 drawable pixels, the buffer drawn at 2x
        const point buffer( 1280, 800 );
        const point blit( 2560, 1600 );
        // the pointer at window point (100, 50) is render pixel (200, 100)
        const point click = display_buffer_from_render( point( 200, 100 ), point::zero, blit, buffer );
        CHECK( click == point( 100, 50 ) );
        // the old mapping used the render pixel as the buffer position
        CHECK( click != point( 200, 100 ) );
        // the bottom-right corner stays inside the buffer
        CHECK( display_buffer_from_render( point( 2559, 1599 ), point::zero, blit, buffer ) ==
               point( 1279, 799 ) );
    }
    SECTION( "standard display: one pixel per point, no change" ) {
        const point buffer( 1280, 800 );
        CHECK( display_buffer_from_render( point( 640, 400 ), point::zero, buffer, buffer ) ==
               point( 640, 400 ) );
    }
    SECTION( "buffer smaller than the window: integer scale with a border" ) {
        // borderless fullscreen: a 1000x700 buffer drawn at 2x into 2560x1600 pixels
        const point buffer( 1000, 700 );
        const point blit( 2000, 1400 );
        CHECK( display_buffer_from_render( point( 1000, 700 ), point::zero, blit, buffer ) ==
               point( 500, 350 ) );
        // a click on the border lands past the buffer's edge, not wrapped back inside it
        CHECK( display_buffer_from_render( point( 2200, 100 ), point::zero, blit, buffer ).x >= 1000 );
    }
    SECTION( "no blit yet: the point passes through" ) {
        CHECK( display_buffer_from_render( point( 7, 9 ), point::zero, point::zero, point( 10, 10 ) ) ==
               point( 7, 9 ) );
    }
}
