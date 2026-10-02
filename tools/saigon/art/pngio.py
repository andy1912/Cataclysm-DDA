"""Minimal dependency-free PNG reader/writer (RGBA, non-interlaced) for the sprite packer.

Reads bit depths 1/2/4/8 for grey, palette (with tRNS), RGB, grey+alpha and RGBA;
writes 8-bit RGBA.  Enough for hand-drawn pixel art and Blender renders without
needing Pillow or pyvips.
"""
import struct
import zlib

SIGNATURE = b'\x89PNG\r\n\x1a\n'
CHANNELS = { 0: 1, 2: 3, 3: 1, 4: 2, 6: 4 }


class Image:
    def __init__( self, width, height, pixels=None ):
        self.width = width
        self.height = height
        # flat RGBA bytes, row-major
        self.pixels = bytearray( pixels if pixels is not None else width * height * 4 )

    def get( self, x, y ):
        i = ( y * self.width + x ) * 4
        return tuple( self.pixels[i:i + 4] )

    def set( self, x, y, rgba ):
        i = ( y * self.width + x ) * 4
        self.pixels[i:i + 4] = bytes( rgba )

    def paste( self, other, ox, oy ):
        for y in range( other.height ):
            src = y * other.width * 4
            dst = ( ( oy + y ) * self.width + ox ) * 4
            self.pixels[dst:dst + other.width * 4] = other.pixels[src:src + other.width * 4]


def _paeth( a, b, c ):
    p = a + b - c
    pa, pb, pc = abs( p - a ), abs( p - b ), abs( p - c )
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def read( path ):
    with open( path, 'rb' ) as f:
        data = f.read()
    if data[:8] != SIGNATURE:
        raise ValueError( '%s: not a PNG' % path )
    pos = 8
    idat = b''
    palette = None
    trns = None
    while pos < len( data ):
        length, ctype = struct.unpack( '>I4s', data[pos:pos + 8] )
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b'IHDR':
            width, height, depth, color, _, _, interlace = struct.unpack( '>IIBBBBB', chunk )
        elif ctype == b'PLTE':
            palette = [ tuple( chunk[i:i + 3] ) for i in range( 0, len( chunk ), 3 ) ]
        elif ctype == b'tRNS':
            trns = chunk
        elif ctype == b'IDAT':
            idat += chunk
        elif ctype == b'IEND':
            break
    if interlace:
        raise ValueError( '%s: interlaced PNGs are not supported; re-save without interlacing' % path )
    channels = CHANNELS[color]
    bits_pp = channels * depth
    stride = ( width * bits_pp + 7 ) // 8
    bpp = max( 1, bits_pp // 8 )
    raw = zlib.decompress( idat )
    rows = []
    prev = bytearray( stride )
    for y in range( height ):
        ftype = raw[y * ( stride + 1 )]
        line = bytearray( raw[y * ( stride + 1 ) + 1:( y + 1 ) * ( stride + 1 )] )
        for i in range( stride ):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ftype == 1:
                line[i] = ( line[i] + a ) & 0xff
            elif ftype == 2:
                line[i] = ( line[i] + b ) & 0xff
            elif ftype == 3:
                line[i] = ( line[i] + ( ( a + b ) >> 1 ) ) & 0xff
            elif ftype == 4:
                line[i] = ( line[i] + _paeth( a, b, c ) ) & 0xff
        rows.append( line )
        prev = line
    img = Image( width, height )
    for y, line in enumerate( rows ):
        for x in range( width ):
            if depth == 8:
                px = line[x * channels:( x + 1 ) * channels]
            elif depth == 16:
                px = line[x * channels * 2:( x + 1 ) * channels * 2:2]
            else:
                per_byte = 8 // depth
                byte = line[x // per_byte]
                shift = 8 - depth * ( x % per_byte + 1 )
                v = ( byte >> shift ) & ( ( 1 << depth ) - 1 )
                px = [ v if color == 3 else v * 255 // ( ( 1 << depth ) - 1 ) ]
            if color == 6:
                rgba = tuple( px )
            elif color == 2:
                rgba = ( px[0], px[1], px[2], 255 )
            elif color == 0:
                rgba = ( px[0], px[0], px[0], 255 )
            elif color == 4:
                rgba = ( px[0], px[0], px[0], px[1] )
            else:
                idx = px[0]
                r, g, b = palette[idx]
                alpha = trns[idx] if trns is not None and idx < len( trns ) else 255
                rgba = ( r, g, b, alpha )
            img.set( x, y, rgba )
    return img


def _chunk( ctype, payload ):
    return struct.pack( '>I', len( payload ) ) + ctype + payload + struct.pack(
        '>I', zlib.crc32( ctype + payload ) & 0xffffffff )


def write( path, img ):
    raw = bytearray()
    row = img.width * 4
    for y in range( img.height ):
        raw.append( 0 )
        raw += img.pixels[y * row:( y + 1 ) * row]
    with open( path, 'wb' ) as f:
        f.write( SIGNATURE )
        f.write( _chunk( b'IHDR', struct.pack( '>IIBBBBB', img.width, img.height, 8, 6, 0, 0, 0 ) ) )
        f.write( _chunk( b'IDAT', zlib.compress( bytes( raw ), 9 ) ) )
        f.write( _chunk( b'IEND', b'' ) )
