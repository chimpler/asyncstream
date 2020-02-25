from typing import Optional, Union

from asyncstream.codecs import error_import_usage


class AsyncFileObj(object):
    MODE_DEFAULT = 0
    MODE_BINARY = 1
    MODE_TEXT = 2

    def __init__(self, afd, mode, compressor, decompressor, ignore_header=False, buffer_size=1024 * 1024):
        self._afd = afd
        self._mode = mode
        self._compressor = compressor
        self._decompressor = decompressor
        self._ignore_header = ignore_header
        self._header = None
        self._buffer_size = buffer_size
        self._eof = False
        self._lines = []
        self._index = 0
        self._filename = None
        self._has_flushed = True
        self._is_closed = False
        self._buffer = b''

        if 'b' in mode:
            self._file_type = self.MODE_BINARY
        else:
            self._file_type = self.MODE_TEXT

        if 'w' in mode:
            self.write = self._write
        else:
            self.write = self._cannot_write

    def convert_to(self, value: Union[bytes, str]) -> Union[bytes, str]:
        if isinstance(value, str):
            return value if self._file_type == self.MODE_TEXT else value.encode('UTF-8')
        else:
            return value if self._file_type == self.MODE_BINARY else value.decode('UTF-8')

    async def _cannot_write(self, buffer: bytes):
        raise IOError('Cannot write because mode is not set to write')

    async def read(self, n: Optional[int] = None):
        """
        return content of size n (all if n is not specified)
        :param n: size of data to return
        :return: content of size n
        """
        buffer_size = n if n else 1024 * 1024
        while True:
            if self._eof or len(self._buffer) >= buffer_size:
                result = self._buffer[:buffer_size]
                self._buffer = self._buffer[buffer_size:]
                return self.convert_to(result)

            data = await self._afd.read(buffer_size)
            if data:
                self._buffer += self._decompressor.decompress(data)
            else:
                if hasattr(self._decompressor, 'flush'):
                    data = self._decompressor.flush()
                    if data:
                        self._buffer += data
                self._eof = True

        return self.convert_to(self._buffer)

    async def _write(self, buffer: bytes):
        self._has_flushed = False
        compressed_data = self._compressor.compress(buffer)
        if compressed_data:
            return await self._afd.write(compressed_data)
        else:
            return 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        while True:
            if not self._lines and self._eof:
                raise StopAsyncIteration

            if self._index >= len(self._lines) - 1:
                tmp = await self.read(self._buffer_size)
                if tmp:
                    lines = tmp.splitlines(True)
                    self._index = 0
                    if self._lines:
                        result = self._lines[0] + lines[0]
                    else:
                        result = lines[0]
                    self._lines = lines[1:]
                    return result
                else:
                    self._eof = True
                    if not self._lines:
                        raise StopAsyncIteration
                    result = self._lines[-1]
                    self._lines = []
                    return result
            else:
                result = self._lines[self._index]
                self._index += 1
                return result

    async def flush(self) -> None:
        """
        Flush file descriptor
        :return: nothing
        """
        if self._has_flushed:
            return b''

        self._has_flushed = True
        compressed_data = self._compressor.flush()
        if compressed_data:
            return await self._afd.write(compressed_data)

    async def close(self) -> None:
        """
        close file descriptor
        :return None:
        """
        if self._is_closed:
            return

        await self.flush()
        if hasattr(self._decompressor, 'close'):
            self._decompressor.close()

        if hasattr(self._compressor, 'close'):
            buf = self._compressor.close()
            if buf:
                self._afd.write(buf)

        if hasattr(self._afd, 'flush'):
            await self._afd.flush()
        # If we pass a filename, then we close the file otherwise it's the
        # responsibility of the caller
        if self._filename:
            self._afd.close()

        self._is_closed = True

    async def __aenter__(self):
        if isinstance(self._afd, str):
            try:
                from aiofiles.threadpool import _open
            except ImportError:
                error_import_usage('aiofiles')

            # always open file in binary
            file_mode = self._mode.replace('t', 'b')
            fd = await _open(self._afd, file_mode)
            self._filename = self._afd
            self._afd = fd
        return self

    async def __aexit__(self, *exc_info):
        await self.close()
