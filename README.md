# Py3AMF

Py3AMF is a Python 3 fork of [PyAMF](https://github.com/hydralabs/pyamf).
It provides Action Message Format (AMF0 and AMF3) encoding, decoding, and
remoting support for Python applications.

## Current support

The 0.9.0 release line keeps the supported surface small and focused:

- CPython 3.11, 3.12, 3.13, and 3.14 are tested with the
  `python:3.11-slim`, `python:3.12-slim`, `python:3.13-slim`, and
  `python:3.14-slim` container images.
- Older Python 3 versions are not intentionally blocked, but they are not part
  of the active test matrix.
- AMF0, AMF3, core remoting, the WSGI gateway, and pure Python runtime code are
  supported.
- `pyamf.adapters` remains available as helper and compatibility modules.
- Jython, Cython extension builds, framework gateways, and automatic conversion
  of third-party framework models are no longer officially supported.

Applications should convert framework-specific objects at the application layer
before passing data to Py3AMF.

## Install

Install the released package with pip:

```sh
python -m pip install Py3AMF
```

For local development:

```sh
git clone git@github.com:StdCarrot/Py3AMF.git
cd Py3AMF
python -m pip install -r test-requirements.txt
python -c "import pyamf.tests; pyamf.tests.main()"
python -m pip install .
```

### Simple example
Everything is same with PyAMF, but you have to concern str and bytes types.
```python
import pyamf
from pyamf import remoting
from pyamf.flex import messaging
import uuid
import requests

msg = messaging.RemotingMessage(operation='retrieveUser', 
                                destination='so.stdc.flexact.common.User',
                                messageId=str(uuid.uuid4()).upper(),
                                body=['user_id'])
req = remoting.Request(target='UserService', body=[msg])
ev = remoting.Envelope(pyamf.AMF3)        
ev['/0'] = req

# Encode request 
bin_msg = remoting.encode(ev)

# Send request; You can use other channels like RTMP
resp = requests.post('http://example.com/amf', 
                     data=bin_msg.getvalue(), 
                     headers={'Content-Type': 'application/x-amf'})

# Decode response
resp_msg = remoting.decode(resp.content)
print(resp_msg.bodies)
```

------------------------------------------------------

[Action Message Format](http://en.wikipedia.org/wiki/Action_Message_Format) is a compact binary format used by Adobe Flash Player and Adobe AIR applications. Py3AMF keeps the AMF codec and WSGI remoting pieces current for modern Python 3 runtimes.

The [Adobe Integrated Runtime](http://en.wikipedia.org/wiki/Adobe_AIR) and [Adobe Flash Player](http://en.wikipedia.org/wiki/Flash_Player) use AMF to communicate between an application and a remote server. AMF encodes remote procedure calls (RPC) into a compact binary representation that can be transferred over HTTP/HTTPS or the [RTMP/RTMPS](http://en.wikipedia.org/wiki/Real_Time_Messaging_Protocol) protocol. Objects and data values are serialized into this binary format, which increases performance, allowing applications to load data up to 10 times faster than with text-based formats such as XML or SOAP.

AMF3, the default serialization for ActionScript 3.0, provides various advantages over AMF0, which is used for ActionScript 1.0 and 2.0. AMF3 sends data over the network more efficiently than AMF0. AMF3 supports sending `int` and `uint` objects as integers and supports data types that are available only in ActionScript 3.0, such as `ByteArray`, `ArrayCollection`, `ObjectProxy`, and `IExternalizable`.
