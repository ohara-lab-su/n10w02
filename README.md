# N10-W02 gRPC

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/ohara-lab-su/n10w02/blob/main/README.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/ohara-lab-su/n10w02/blob/main/README.ja.md)

[![GitHub](https://img.shields.io/badge/GitHub-ohara--lab--su%2Fn10w02-181717?logo=github)](https://github.com/ohara-lab-su/n10w02/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Documentation-222222?logo=githubpages&logoColor=white)](https://ohara-lab-su.github.io/n10w02/en/)
[![Ohara Lab](https://img.shields.io/badge/Ohara%20Lab-Home-4B5563?logo=homeassistant&logoColor=white)](https://ohara-lab-su.github.io/index.en.html)



This is a minimal setup that exposes `N10W02Ctrl` directly through `grpc_frame`.

## Changes

BMP images are approximately 8 MB, exceeding the default 4 MB receive-message limit in gRPC Python.  
Support for passing `grpc_options` has been added to `grpc_frame`, and the N10-W02 server and client are configured with a 64 MB limit.

## Image Capture

```python
client = N10W02GrpcClient(
    server_ip="127.0.0.1",
    grpc_port=50051,
    max_message_mb=64,
)

image = client.capture_bmp_bytes(focus=False)

with open("capture.bmp", "wb") as f:
    f.write(image)
```

## Server

```bash
python n10w02_grpc_server.py
```

`N10W02Ctrl` is passed directly to `create_com_grpc_server()`.  
EventBus, streaming, and image wrappers are not used.
