async-stream
============

```
UNDER CONSTRUCTION
```

Simple library to compress/uncompress Async streams using file iterator and readers.

It supports the following compression format:

* gzip
* bzip2
* snappy
* zstandard
* parquet (experimental)
* orc (experimental)

## Getting started

Install the library as follows:

    pip install asyncstream

Compress a regular file to gzip (`examples/simple_compress_gzip.py`):
```python
import asyncstream
import asyncio


async def run():
    async with asyncstream.open('samples/animals.txt', 'rb') as fd:
        async with asyncstream.open('samples/animals.txt.gz',  compression='gzip') as gzfd:
            async for line in fd:
                await gzfd.write(line)

if __name__ == '__main__':
    asyncio.run(run())
```

or you can also open from an async file descriptor using aiofiles (`examples/simple_compress_gzip_with_aiofiles.py`):

    pip install aiofiles
    
And then run the following code:        
```python
import aiofiles
import asyncstream
import asyncio


async def run():
    async with aiofiles.open('examples/animals.txt', 'rb') as fd:
        async with aiofiles.open('/tmp/animals.txt.gz', 'wb') as wfd:
            async with asyncstream.open(wfd, 'wb', compression='gzip') as gzfd:
                async for line in fd:
                    await gzfd.write(line)


if __name__ == '__main__':
    asyncio.run(run())
```

You can also uncompress an S3 file on the fly using aiobotocore:

    pip install aiobotocore

And then run the following code (`examples/simple_uncompress_bzip2_from_s3.py`):
```python
import aiobotocore
import asyncstream
import asyncio

async def run():
    session = aiobotocore.get_session()
    async with session.create_client('s3') as s3:
        obj = await s3.get_object(Bucket='test-bucket', Key='path/to/file.gz')
        async with asyncstream.open(obj['Body'], 'rt', compression='bzip2') as fd:
            async for line in fd:
                print(line)
    

if __name__ == '__main__':
    asyncio.run(run())
```

### Convert a gzip file to a snappy file

```python
import asyncstream
import asyncio

async def run():
    async with asyncstream.open('samples/animals.txt.gz', 'rb', compression='gzip') as inc_fd:
        async with asyncstream.open('samples/animals.txt.snappy', 'wb', compression='snappy') as outc_fd:
            async for line in inc_fd:
                await outc_fd.write(line)


if __name__ == '__main__':
    asyncio.run(run())
```

### Use an async reader and writer to filter and update data on the fly
 ```python
import asyncstream
import asyncio
 
async def run():
    async with asyncstream.open('/tmp/animals.txt.bz2', 'rb') as in_fd:
        async with asyncstream.open('/tmp/animals.txt.snappy', 'wb') as out_fd:
            async with asyncstream.reader(in_fd) as reader:
                async with asyncstream.writer(out_fd) as writer:
                    async for name, color, age in reader:
                        if color != 'white':
                            await writer.writerow([name, color, age * 2])
 
asyncio.run(run())
```

### Simple parquet encoding

You will need to install `pyarrow` and `pandas`:

    pip install pyarrow pandas

To compress using `snappy`, you can install `snappy`:

    pip install snappy
    
The code below converts a csv file and convert it to parquet
```python
import asyncstream
import asyncio

async def run():
    async with asyncstream.open('examples/animals.txt', 'rb') as fd:
        async with asyncstream.open('output.parquet', 'wb', encoding='parquet', compression='snappy') as wfd:
            async with asyncstream.writer(wfd) as writer:
                async for line in fd:
                    await writer.write(line)

asyncio.run(run())
```

### Simple parquet decoding
```python
import asyncstream
import asyncio

async def run():
    async with asyncstream.open('output.parquet', 'rb', encoding='parquet') as fd:
            async with asyncstream.reader(fd) as reader:
                async for line in reader:
                    print(line)

asyncio.run(run())
```

### Simple orc encoding
```python
import asyncstream
import asyncio

async def run():
    async with asyncstream.open('examples/animals.txt', 'rb') as fd:
        async with asyncstream.open('output.orc.snappy', 'wb', encoding='orc', compression='snappy') as wfd:
            async with asyncstream.writer(wfd) as writer:
                async for line in fd:
                    await writer.write(line)

asyncio.run(run())
```
### Simple orc decoding

```python
import asyncstream
import asyncio

async def run():
    async with asyncstream.open('output.orc.snappy', 'rb', encoding='orc') as fd:
            async with asyncstream.reader(fd) as reader:
                async for line in reader:
                    print(line)

asyncio.run(run())
```

### Usage

#### asyncstream.open(afd: Union[str, AsyncBufferedIOBase], mode=None, encoding=None, compression=None, compress_level=-1)

Open an async file (using its filename or an AsyncBufferedIOBase) and compress or decompress on the fly depending on
the mode (`r` or `w`).

Inputs:

* `mode`: `r` or `w` and `t` (text) or `b` (binary)
* `encoding`: `None`, `parquet` or `orc`
* `compression`: See the compression supported section
* `compress_level`: Optional if compression is used

The `AsyncFileObj` object returned has the following methods:

* `flush()`: used when open in write mode
* `close()`: close file descriptor and release resources. It is done automatically when the `async with` block is exited 

#### afd: AsyncFileObj, columns=Optional[Iterable[str]], column_types=Optional[Iterable[str]], has_header=False, sep=',', eol='\n')

Open an async reader using AsyncFileObj returned by the `asyncstream.open` method. It must be open in text mode (`t`).

Inputs:

* `afd`: AsyncFileObj created with `asyncstream.open`
* `columns`: optional list of column names to use. If it is not set and has_header is true, then it will use the first row as the column names
* `column_types`: optional list of column types (by default it will consider all the columns to be `string`)
* `has_header`: the file has the first line set as header
* `sep`: separator between values
* `eol`: end of line character 

#### writer(afd: AsyncFileObj, has_header: bool = True, columns: Optional[Iterable[str]] = None, column_types: Optional[Iterable[str]] = None):



## Compression supported

Compression                                  | Status
-------------------------------------- | :-----:
`gzip` / `zlib`                          | :white_check_mark:
`bzip2`                          | :white_check_mark:
`snappy`                          | :white_check_mark:
`zstd`                          | :white_check_mark:

### Parquet
Compression                                  | Status
-------------------------------------- | :-----:
none                    | :white_check_mark:
`brotli`                  | :white_check_mark:
`bzip2`                  | :x: 
`gzip`                  | :x: 
`snappy`                  | :white_check_mark:
`zstd`                  | :x:
`zlib`                  | :white_check_mark:

### Orc

Compression                       | Status
-------------------------------------- | :-----:
none                    | :white_check_mark:
`bzip2`                  | :x: 
`gzip` / `zlib`                 | :white_check_mark:
`snappy`                  | :white_check_mark:
`zlib`                  | :white_check_mark:
`zstd`                  | :white_check_mark:
