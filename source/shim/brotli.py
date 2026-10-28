"""Minimal brotli shim backed by Node's built-in zlib brotli.

fontTools' WOFF2 writer only needs compress() and decompress(), plus the
MODE_* constants. Node ships a full brotli implementation, so we call it.
"""
import subprocess

MODE_GENERIC = 0
MODE_TEXT = 1
MODE_FONT = 2

_JS_COMPRESS = r"""
const z = require('zlib');
const chunks = [];
process.stdin.on('data', c => chunks.push(c));
process.stdin.on('end', () => {
  const [mode, quality, lgwin] = process.argv.slice(1).map(Number);
  const out = z.brotliCompressSync(Buffer.concat(chunks), { params: {
    [z.constants.BROTLI_PARAM_MODE]: mode,
    [z.constants.BROTLI_PARAM_QUALITY]: quality,
    [z.constants.BROTLI_PARAM_LGWIN]: lgwin,
  }});
  process.stdout.write(out);
});
"""

_JS_DECOMPRESS = r"""
const z = require('zlib');
const chunks = [];
process.stdin.on('data', c => chunks.push(c));
process.stdin.on('end', () => process.stdout.write(z.brotliDecompressSync(Buffer.concat(chunks))));
"""


def compress(data, mode=MODE_GENERIC, quality=11, lgwin=22, lgblock=0):
    res = subprocess.run(["node", "-e", _JS_COMPRESS, str(mode), str(quality), str(lgwin)],
                         input=bytes(data), capture_output=True, check=True)
    return res.stdout


def decompress(data):
    res = subprocess.run(["node", "-e", _JS_DECOMPRESS], input=bytes(data),
                         capture_output=True, check=True)
    return res.stdout
