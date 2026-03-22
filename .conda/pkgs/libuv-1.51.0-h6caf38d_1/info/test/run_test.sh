

set -ex



test -f "$PREFIX/include/uv.h"
test -f "$PREFIX/lib/libuv.a"
test -f "$PREFIX/lib/libuv.1.dylib"
test -f "$PREFIX/lib/libuv${SHLIB_EXT}"
test -f "$PREFIX/lib/pkgconfig/libuv.pc"
exit 0
