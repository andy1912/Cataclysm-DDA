#pragma once
#ifndef CATA_SRC_DISPLAY_BUFFER_COORDS_H
#define CATA_SRC_DISPLAY_BUFFER_COORDS_H

#include <cstdint>

#include "point.h"

// The tiles build draws the whole game into a display buffer and blits it into a
// rectangle of the window's drawable pixels (sdltiles.cpp get_display_buffer_render_rect:
// an integer multiple of the buffer, top-left, the remainder left as border).  A mouse
// position SDL has already turned into render (drawable pixel) coordinates is mapped back
// into the buffer by undoing that blit.  On a HiDPI window (macOS Retina: two drawable
// pixels per window point) the blit doubles the buffer; skipping this step put every click
// twice as far from the top-left corner as the pointer (Saigon fork, A1).
// Kept free of SDL so the curses test build can check it (tests/saigon_mouse_test.cpp).
inline point display_buffer_from_render( const point &render, const point &dst_origin,
        const point &dst_size, const point &buf_size )
{
    if( dst_size.x <= 0 || dst_size.y <= 0 || buf_size.x <= 0 || buf_size.y <= 0 ) {
        return render;
    }
    return point(
               static_cast<int>( static_cast<int64_t>( render.x - dst_origin.x ) * buf_size.x / dst_size.x ),
               static_cast<int>( static_cast<int64_t>( render.y - dst_origin.y ) * buf_size.y / dst_size.y ) );
}

#endif // CATA_SRC_DISPLAY_BUFFER_COORDS_H
