"""Saigon books and papers: 20x20 item icons.

Books are drawn closed, in 3/4 view like UltimateCataclysm's books: a cover, a white
page block on the right and bottom, and a simple cover emblem.  Covers follow the
item colours in data/mods/saigon_2000s (wuxia red, almanac yellow, songbook pink...).
No readable text: names and descriptions are translated, sprites stay language-free.
"""
from draw import sprite, rgb, shade

OUTLINE = 0.38
PAGES = rgb( '#f4f0e2' )
PAGES_DARK = rgb( '#c9c2aa' )
INK = rgb( '#2a2a2a' )


def finish( c ):
    c.outline( OUTLINE )
    c.drop_shadow( 1, 1, 90 )


def book( c, cover, thick=3, x0=4, y0=5, w=11, h=11 ):
    """Closed book; returns the cover rectangle for the emblem."""
    for i in range( thick ):  # page block, offset down-right
        c.rect( x0 + 1 + i, y0 + 1 + i, x0 + w + i, y0 + h + i, PAGES if i < thick - 1 else PAGES_DARK )
    for i in range( 1, thick ):
        c.line( x0 + w + i, y0 + 2 + i, x0 + w + i, y0 + h + i - 1, PAGES_DARK if i % 2 else PAGES )
    c.rect( x0, y0, x0 + w - 1, y0 + h - 1, cover )
    c.line( x0, y0, x0 + w - 1, y0, shade( cover, 1.25 ) )
    c.line( x0, y0, x0, y0 + h - 1, shade( cover, 0.7 ) )   # spine
    c.line( x0 + 1, y0, x0 + 1, y0 + h - 1, shade( cover, 0.85 ) )
    return x0 + 2, y0 + 1, x0 + w - 2, y0 + h - 2


@sprite( 'sgn_book_wuxia', 20, 20 )
def wuxia( c ):
    x0, y0, x1, y1 = book( c, rgb( '#b8302a' ), thick=4 )
    c.line( x0 + 1, y1 - 1, x1 - 1, y0 + 2, rgb( '#e8e0d0' ) )      # a sword across the cover
    c.line( x0 + 2, y1 - 3, x0 + 4, y1 - 1, rgb( '#f2c232' ) )      # its guard
    c.rect( x0 + 1, y0 + 1, x0 + 3, y0 + 1, rgb( '#f2c232' ) )      # volume number
    finish( c )


@sprite( 'sgn_book_sutra', 20, 20 )
def sutra( c ):
    x0, y0, x1, y1 = book( c, rgb( '#d88a1e' ), thick=2, x0=5, y0=6, w=10, h=10 )
    cx, cy = ( x0 + x1 ) // 2, ( y0 + y1 ) // 2 + 1
    for dx, dy in ( ( 0, -2 ), ( -2, 0 ), ( 2, 0 ), ( -1, -1 ), ( 1, -1 ) ):  # lotus
        c.px( cx + dx, cy + dy, rgb( '#f7d8e0' ) )
    c.line( cx - 2, cy + 1, cx + 2, cy + 1, rgb( '#7a3e10' ) )
    c.px( cx, cy, rgb( '#f2c232' ) )
    finish( c )


@sprite( 'sgn_book_almanac', 20, 20 )
def almanac( c ):
    x0, y0, x1, y1 = book( c, rgb( '#c8262a' ), thick=5, x0=4, y0=4 )
    c.rect( x0 + 1, y0 + 1, x1, y0 + 2, rgb( '#f2c232' ) )
    c.ellipse( ( x0 + x1 ) / 2 + 0.5, ( y0 + y1 ) / 2 + 2.5, 2.8, 2.8, rgb( '#f2c232' ), light=rgb( '#fbe89a' ), dark=rgb( '#c8961a' ) )  # moon disc
    finish( c )


@sprite( 'sgn_karaoke_songbook', 20, 20 )
def karaoke( c ):
    # a thick laminated binder with rings on the spine
    x0, y0, x1, y1 = book( c, rgb( '#e0509a' ), thick=6, x0=3, y0=3, w=11, h=11 )
    for y in range( y0 + 1, y1 + 1, 3 ):
        c.px( x0 - 2, y, rgb( '#d8d8d8' ) )
    c.ring( x0 + 4, y0 + 5, 2.2, 2.2, rgb( '#ffffff' ) )  # a microphone
    c.line( x0 + 5, y0 + 7, x0 + 7, y0 + 9, rgb( '#303030' ) )
    c.px( x1, y0 + 1, rgb( '#80e0ff' ) )
    c.px( x1 - 1, y0 + 2, rgb( '#80e0ff' ) )
    finish( c )


def manual( c, cover, emblem ):
    x0, y0, x1, y1 = book( c, cover, thick=2, x0=4, y0=5, w=12, h=11 )
    c.rect( x0, y0 + 1, x1, y0 + 2, shade( cover, 0.6 ) )   # title band
    emblem( c, x0, y0 + 4, x1, y1 )
    finish( c )


@sprite( 'sgn_book_moto_repair', 20, 20 )
def moto_repair( c ):
    def emblem( c, x0, y0, x1, y1 ):  # a motorbike wheel and a spanner
        c.ring( x0 + 3, y0 + 3, 2.6, 2.6, INK )
        c.px( x0 + 3, y0 + 3, INK )
        c.line( x0 + 6, y1, x1, y0, rgb( '#3d6fb0' ) )
    manual( c, rgb( '#c4c8cc' ), emblem )


@sprite( 'sgn_book_southern_cooking', 20, 20 )
def cooking( c ):
    def emblem( c, x0, y0, x1, y1 ):  # a clay pot of cá kho
        c.ellipse( ( x0 + x1 ) / 2 + 0.5, y0 + 3, 3.5, 2.5, rgb( '#8a4a26' ) )
        c.line( x0 + 2, y0 + 1, x1 - 2, y0 + 1, rgb( '#f2c232' ) )
    manual( c, rgb( '#e0582a' ), emblem )


@sprite( 'sgn_book_nursing', 20, 20 )
def nursing( c ):
    def emblem( c, x0, y0, x1, y1 ):  # a green medical cross (not the protected red cross)
        cx, cy = ( x0 + x1 ) // 2, y0 + 3
        c.rect( cx - 2, cy, cx + 2, cy, rgb( '#2e9a52' ) )
        c.rect( cx, cy - 2, cx, cy + 2, rgb( '#2e9a52' ) )
    manual( c, rgb( '#f0f2f4' ), emblem )


@sprite( 'sgn_book_tailoring', 20, 20 )
def tailoring( c ):
    def emblem( c, x0, y0, x1, y1 ):  # an áo dài pattern outline
        cx = ( x0 + x1 ) // 2
        c.polygon( [ ( cx - 1, y0 ), ( cx + 2, y0 ), ( cx + 3, y1 ), ( cx - 2, y1 ) ], rgb( '#ffffff' ) )
        c.line( cx - 3, y0 + 1, cx + 4, y0 + 1, rgb( '#ffffff' ) )
    manual( c, rgb( '#e88ab4' ), emblem )


@sprite( 'sgn_book_fishing', 20, 20 )
def fishing( c ):
    def emblem( c, x0, y0, x1, y1 ):  # a fish
        c.ellipse( x0 + 4, y0 + 3, 3, 1.6, rgb( '#d0e4f0' ) )
        c.polygon( [ ( x0 + 7, y0 + 3 ), ( x0 + 9, y0 + 1 ), ( x0 + 9, y0 + 5 ) ], rgb( '#d0e4f0' ) )
        c.px( x0 + 2, y0 + 2, INK )
    manual( c, rgb( '#3f8a4a' ), emblem )


@sprite( 'sgn_book_tv_repair', 20, 20 )
def tv_repair( c ):
    def emblem( c, x0, y0, x1, y1 ):  # a CRT television
        c.rect( x0 + 1, y0, x1 - 1, y1, INK )
        c.rect( x0 + 2, y0 + 1, x1 - 3, y1 - 1, rgb( '#7ab8d8' ) )
        c.px( x1 - 2, y0 + 1, rgb( '#d8402a' ) )
    manual( c, rgb( '#f0c838' ), emblem )


@sprite( 'sgn_book_construction', 20, 20 )
def construction( c ):
    def emblem( c, x0, y0, x1, y1 ):  # a hard hat
        cx = ( x0 + x1 ) / 2 + 0.5
        c.ellipse( cx, y0 + 3, 3, 2.2, rgb( '#f2a020' ) )
        c.rect( x0 + 1, y0 + 4, x1 - 1, y0 + 4, rgb( '#f2a020' ) )
    manual( c, rgb( '#8a5a32' ), emblem )


def text_lines( c, x0, y0, x1, y1, colour, step=2, ragged=True ):
    for y in range( y0, y1 + 1, step ):
        end = x1 - ( c.rand.randint( 0, 3 ) if ragged else 0 )
        c.line( x0, y, end, y, colour )


@sprite( 'sgn_newspaper', 20, 20 )
def newspaper( c ):
    # a folded daily: masthead, a photo block, columns of grey text
    c.polygon( [ ( 3, 7 ), ( 15, 4 ), ( 17, 14 ), ( 5, 17 ) ], rgb( '#d8d4c8' ) )
    c.polygon( [ ( 3, 6 ), ( 14, 3 ), ( 16, 13 ), ( 5, 16 ) ], rgb( '#f0ece0' ) )
    c.line( 4, 7, 13, 4, rgb( '#c8262a' ) )          # red masthead rule
    c.line( 4, 8, 13, 5, rgb( '#303030' ) )
    c.polygon( [ ( 5, 10 ), ( 9, 9 ), ( 10, 12 ), ( 6, 13 ) ], rgb( '#7a8a96' ) )  # photo
    for i in range( 4 ):
        c.line( 10, 9 + i * 1.6, 14, 8 + i * 1.6, rgb( '#9a9a9a' ) )
    c.line( 6, 15, 14, 13, rgb( '#9a9a9a' ) )
    finish( c )


@sprite( 'sgn_ward_notice', 20, 20 )
def ward_notice( c ):
    # a mimeographed ward notice: national-emblem red header, typed lines, round red seal
    c.rect( 5, 3, 15, 17, rgb( '#ece6d4' ) )
    c.rect( 5, 3, 15, 4, rgb( '#c8262a' ) )
    c.px( 10, 4, rgb( '#f2c232' ) )
    text_lines( c, 6, 6, 14, 13, rgb( '#5a5a6a' ) )
    c.rect( 10, 14, 13, 16, rgb( '#d8302a' ) )   # round ward seal, 4x3 with soft corners
    for x, y in ( ( 10, 14 ), ( 13, 14 ), ( 10, 16 ), ( 13, 16 ) ):
        c.px( x, y, rgb( '#e88a7a' ) )
    c.line( 11, 15, 12, 15, rgb( '#f2c232' ) )
    finish( c )


@sprite( 'sgn_note_handwritten', 20, 20 )
def note( c ):
    # a torn scrap from a school exercise book, blue ink blurred by humidity
    c.polygon( [ ( 4, 8 ), ( 15, 6 ), ( 16, 14 ), ( 5, 15 ) ], rgb( '#f4f2ea' ) )
    for i in range( 3 ):
        y = 9 + i * 2
        c.line( 5, y, 14, y - 1, rgb( '#c8d8ec' ) )
    for i in range( 3 ):                                   # three lines of words with gaps
        y = 9 + i * 2
        x = 6
        while x < 14 - i:
            word = c.rand.randint( 1, 3 )
            c.line( x, y - 1, min( x + word, 14 - i ), y - 1, rgb( '#3050a8' ) )
            x += word + 2
    finish( c )


@sprite( 'holybook_catechism', 20, 20 )
def catechism( c ):
    # a small black catechism with a gold cross, as kept in church pews
    x0, y0, x1, y1 = book( c, rgb( '#2a2a30' ), thick=3, x0=5, y0=5, w=10, h=11 )
    cx = ( x0 + x1 ) // 2
    c.line( cx, y0 + 2, cx, y1 - 1, rgb( '#e8c040' ) )
    c.line( cx - 2, y0 + 4, cx + 2, y0 + 4, rgb( '#e8c040' ) )
    finish( c )


# --- L-loc2: the Vietnamese books that replaced dda's American ones --------------------------
@sprite( 'sgn_kinh_thanh', 20, 20 )
def kinh_thanh( c ):
    # a thick black Bible, a gold cross, ribbons hanging out of the pages
    x0, y0, x1, y1 = book( c, rgb( '#2a2a30' ), thick=4 )
    cx = ( x0 + x1 ) // 2
    c.line( cx, y0 + 2, cx, y1 - 3, rgb( '#e2c25a' ) )
    c.line( cx - 2, y0 + 4, cx + 2, y0 + 4, rgb( '#e2c25a' ) )
    c.line( x1 - 2, y1, x1 - 2, y1 + 2, rgb( '#c83030' ) )
    finish( c )


@sprite( 'sgn_sach_kinh', 20, 20 )
def sach_kinh( c ):
    # a small worn prayer book with a rosary laid over it
    x0, y0, x1, y1 = book( c, rgb( '#5a2a3a' ), thick=2, x0=5, y0=6, w=10, h=10 )
    for i in range( 6 ):
        c.px( x0 + 1 + i, y0 + 2 + ( i % 2 ), rgb( '#e8e0d0' ) )
    c.line( x0 + 6, y0 + 3, x0 + 6, y1 - 1, rgb( '#e8e0d0' ) )
    c.px( x0 + 6, y1 - 1, rgb( '#e2c25a' ) )
    finish( c )


@sprite( 'sgn_guidebook_vn', 20, 20 )
def guidebook_vn( c ):
    # a fat blue travel guide, a red flag-and-star badge, coloured page tabs
    x0, y0, x1, y1 = book( c, rgb( '#2a6ab0' ), thick=5 )
    c.rect( x0 + 2, y0 + 2, x0 + 5, y0 + 4, rgb( '#d83030' ) )
    c.px( x0 + 3, y0 + 3, rgb( '#f2c232' ) )
    for i, col in enumerate( ( '#f2c232', '#3a9a3a', '#e86a9a' ) ):
        c.px( x1 + 1, y0 + 3 + 3 * i, rgb( col ) )
    finish( c )


@sprite( 'sgn_sgk_ngu_van', 20, 20 )
def sgk_ngu_van( c ):
    # a thin school textbook, pale green cover with a printed title band
    x0, y0, x1, y1 = book( c, rgb( '#8ac08a' ), thick=1 )
    c.rect( x0 + 1, y0 + 2, x1 - 1, y0 + 4, rgb( '#f4f0e2' ) )
    c.line( x0 + 2, y0 + 3, x1 - 2, y0 + 3, INK )
    finish( c )


@sprite( 'sgn_so_tay_so_cuu', 20, 20 )
def so_tay_so_cuu( c ):
    # a white handbook with the red cross
    x0, y0, x1, y1 = book( c, rgb( '#ece8e0' ), thick=2 )
    cx, cy = ( x0 + x1 ) // 2, ( y0 + y1 ) // 2
    c.rect( cx - 1, cy - 3, cx + 1, cy + 3, rgb( '#d02828' ) )
    c.rect( cx - 3, cy - 1, cx + 3, cy + 1, rgb( '#d02828' ) )
    finish( c )
