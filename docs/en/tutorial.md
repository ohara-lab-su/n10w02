# Basic Tutorial


This tutorial explains the basic concepts and usage of the N10-W02 library.

The library is designed to make the **Canon N10-W02** easy to use from Python.

---

# Philosophy

Using the N10-W02 typically requires knowledge of:

- ORiN2 SDK
- COM
- Canon Provider
- Windows-specific APIs

However, many application developers only need to:

> Capture an image.

The library therefore uses the following architecture:

```
Application
        │
        ▼
N10W02Ctrl
        │
 ORiN2 / COM
        │
 Canon N10-W02
```

Applications do not need to deal with ORiN2 at all.

---

# Remote First

The N10-W02 is a network camera.

Accordingly, the library is designed around:

> Remote control

rather than:

> Local control

```
          Ethernet

Client ---------------- Server
                            │
                       N10W02Ctrl
                            │
                        ORiN2 COM
                            │
                         Camera
```

Image acquisition is also handled as an ordinary RPC.

```
client.capture_bmp_bytes()

        ↓

server

        ↓

N10W02Ctrl.capture_bmp_bytes()

        ↓

BMP bytes
```

No dedicated streaming server is required to transfer images.

BMP binary data is sent and received as ordinary gRPC messages.

---

# Dynamic RPC

Conventional gRPC development requires:

- Editing proto files
- Generating stubs
- Creating wrappers

By using `grpc_frame`, this library instead provides the following structure:

```
N10W02Ctrl

↓

Exposed directly

↓

Called directly from the client
```

In other words, when a method is added on the server side, it becomes available under the same name on the client side.

There is no need to reimplement a client API.

---

# Local Usage

To use the camera directly on a local PC:

```python
from n10w02 import N10W02Ctrl

camera = N10W02Ctrl(
    camera_ip="10.170.10.42",
)

image = camera.capture_bmp_bytes()

with open("capture.bmp", "wb") as f:
    f.write(image)
```

This is all that is needed to capture an image.

---

# gRPC Server

The server can be started with just a few lines:

```python
from n10w02.grpc_server import n10w02_grpc_server

n10w02_grpc_server(
    camera_ip="10.170.10.42",
    grpc_host="0.0.0.0",
    grpc_port=50051,
)
```

The server automatically performs:

- COM initialization
- ORiN2 connection
- Camera Provider connection

---

# Remote Client

To access the camera from another PC:

```python
from n10w02.grpc_client import N10W02GrpcClient

client = N10W02GrpcClient(
    server_ip="10.170.10.38",
    grpc_port=50051,
)

image = client.capture_bmp_bytes()
```

The experience is nearly identical to using the local API.

---

# Why BMP?

The library uses BMP rather than JPEG as its primary image format because:

- It preserves the camera's raw image data.
- No compression processing is required.
- The data can be passed directly to OpenCV and similar tools.
- Image quality is not altered.

Convert the images to JPEG or PNG in the consuming application when needed.

---

# Error Handling

Connection setup is performed by the constructor:

```python
camera = N10W02Ctrl(...)
```

An exception is raised if the connection fails.

This prevents a situation in which:

> An object exists even though the connection could not be established.

The application therefore completes its connection check during startup.

---

# Logging

The entire library is designed to use `x_logger`.

Operations log events such as:

- Connection start
- Connection completion
- COM initialization
- Provider connection
- Image acquisition
- Disconnection

This also makes troubleshooting easier.

---

# Summary

The library has the following characteristics:

- Hides ORiN2 implementation details.
- Exposes Python objects directly.
- Avoids manually implementing gRPC APIs.
- Provides the same API for local and remote use.
- Transfers images using ordinary RPCs.
- Enables applications to be built with a simple architecture.

Application developers can use the N10-W02 much like a conventional Python library, without dealing with the details of ORiN2 or COM.

---

## Author

- Kengo NAKADA (kengo.nakada@gmail.com)
