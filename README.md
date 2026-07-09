# N10-W02 gRPC image transfer

N10-W02 の BMP 画像取得を `grpc_frame` で gRPC 化する構成である。

今回の構造は、COM 用の `orin2_grpc_server.py` / `orin2_grpc_client.py` を主参照にしている。

## ファイル

```text
server_grpc/
├── n10w02_image_ctrl.py
├── n10w02_grpc_server.py
├── n10w02_grpc_client.py
├── make_n10w02_pyi.py
├── __init__.py
└── README.md
```

## 責務分離

`n10w02_image_ctrl.py` は gRPC に公開する ctrl facade である。`N10W02Ctrl` を内部に持ち、画像取得、フォーカス、ホワイトバランス、状態取得だけを公開する。gRPC server の起動、protobuf、stub、通信処理は持たない。

`n10w02_grpc_server.py` はサーバー起動だけを担当する。`create_com_grpc_server()` に `ctrl_factory` を渡す。これは `orin2_grpc_server.py` と同じ構造である。

`n10w02_grpc_client.py` は `GrpcClient` の薄い派生だけである。client 側は ctrl を import しない。stub / pb2 も import しない。`capture_bmp()`、`capture_bmp_bytes()`、`get_status()` などは `grpc_frame` の `Describe` により動的に bind される。

`make_n10w02_pyi.py` は `grpc_frame.make_pyi.generate_client_pyi()` による `.pyi` 自動生成用である。`.pyi` は手書きしない。

## COM と gRPC の扱い

N10-W02 は ORiN2 / CAO COM 経由で制御される。gRPC handler は worker thread 上で動くため、通常の `create_grpc_server(ctrl_obj=...)` に COM ctrl を直接渡すと、COM オブジェクトを複数 thread から呼ぶ構造になる。

このため、`create_com_grpc_server()` を使う。

```text
gRPC client
  -> grpc_frame GrpcClient
  -> ctrl.Control/Call
  -> ThreadSafeCtrlProxy
  -> ComExecutionRunner
  -> N10W02ImageCtrl
  -> N10W02Ctrl / ORiN2 COM
```

COM の生成と public method の実行は `ComExecutionRunner` の COM thread に固定される。サーバー側はこの既存の COM 用 frame 構造を使うだけで、N10-W02 専用の新しい server framework は作らない。

## .pyi 生成

```bash
python server_grpc/make_n10w02_pyi.py
```

## サーバー起動

```bash
python server_grpc/n10w02_grpc_server.py
```

IP などは `__main__` の定数を編集する。プログラムから起動する場合は次を呼ぶ。

```python
from n10w02.server_grpc.n10w02_grpc_server import n10w02_grpc_server

n10w02_grpc_server(
    grpc_host="0.0.0.0",
    grpc_port=50051,
    camera_ip="10.170.10.42",
)
```

## クライアント例

```python
from n10w02.server_grpc.n10w02_grpc_client import N10W02GrpcClient

client = N10W02GrpcClient(
    server_ip="127.0.0.1",
    grpc_port=50051,
)

payload = client.capture_bmp()
client.save_bmp_payload(payload, "n10w02_capture.bmp")

image = client.capture_bmp_bytes()
client.save_bmp_bytes(image, "n10w02_capture_2.bmp")
```
