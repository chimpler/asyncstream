from typing import Optional, Iterable

from asyncstream import AsyncFileObj


class AsyncReader(object):
    def __init__(self, afd: AsyncFileObj, columns=Optional[Iterable[str]], column_types=Optional[Iterable[str]], has_header=False, sep=',', eol='\n'):
        """
        :param afd:
        :type AsyncFileObj:
        :param columns: list of column names (optional)
        :param column_types: list of column types (optional, default is string)
        :param has_header: if has header is set and no columns is provided, column names will be determined from the first line
        :type bool:
        :param sep: separator (e.g., `,`, `|`, `\t`). Default is `,`
        :type str:
        :param eol: end of line character (default is `\n`)
        :type str:
        """
        self._afd = afd
        self._sep = sep
        self._eol = eol
        self._columns = columns
        self._column_types = column_types
        self._has_header = has_header

    async def __aenter__(self):
        return self

    def __aiter__(self):
        return self

    async def __aexit__(self, *exc):
        return None

    async def __anext__(self):
        next_line = await self._afd.__anext__()
        if next_line:
            return next_line.rstrip(self._eol).split(self._sep)
        else:
            raise StopAsyncIteration

