# N10-W02 gRPC

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/ohara-lab-su/n10w02/blob/main/README.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/ohara-lab-su/n10w02/blob/main/README.ja.md)

[![GitHub](https://img.shields.io/badge/GitHub-ohara--lab--su%2Fn10w02-181717?logo=github)](https://github.com/ohara-lab-su/n10w02/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Documentation-222222?logo=githubpages&logoColor=white)](https://ohara-lab-su.github.io/n10w02/ja/)
[![Ohara Lab](https://img.shields.io/badge/Ohara%20Lab-Home-4B5563?logo=homeassistant&logoColor=white)](https://ohara-lab-su.github.io/)


`N10W02Ctrl` をそのまま `grpc_frame` に載せる最小構成である。

## 修正点

BMP が 8 MB 程度になるため、gRPC Python の既定受信上限 4 MB に当たる。  
`grpc_frame` に `grpc_options` を渡す口を追加し、N10-W02 の server/client では 64 MB を指定する。

## 画像取得

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

## サーバー

```bash
python n10w02_grpc_server.py
```

`N10W02Ctrl` は `create_com_grpc_server()` に直接載せる。  
EventBus、stream、画像ラッパーは使わない。
