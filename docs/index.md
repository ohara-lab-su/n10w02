# n10w02

cobotta のカメラをただの web カメラのように使う

---
```{toctree}
:maxdepth: 2
:caption: Contents:

api/modules
```
---

# Basic Tutorial

このチュートリアルでは、N10-W02 ライブラリの基本的な考え方と利用方法を説明します。

このライブラリは **Canon N10-W02** を Python から簡単に扱うことを目的としています。

---

# Philosophy

一般的に N10-W02 を利用するには、

- ORiN2 SDK
- COM
- Canon Provider
- Windows 固有 API

などを理解する必要があります。

しかし、多くのアプリケーション開発者に必要なのは

> 「画像を取得する」

だけです。

そこで本ライブラリでは

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

という構造を採用しています。

アプリケーションは ORiN2 を一切意識する必要がありません。

---

# Remote First

N10-W02 はネットワークカメラです。

そのため、このライブラリでは

> ローカル制御

ではなく

> リモート制御

を基本思想にしています。

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

画像取得も通常の RPC として扱われます。

```
client.capture_bmp_bytes()

        ↓

server

        ↓

N10W02Ctrl.capture_bmp_bytes()

        ↓

BMP bytes
```

画像転送のための特殊なストリーミングサーバーは必要ありません。

BMP バイナリを通常の gRPC メッセージとして送受信します。

---

# Dynamic RPC

通常の gRPC では

- proto を編集
- stub を生成
- wrapper を作成

という作業が必要になります。

本ライブラリでは grpc_frame を利用することで

```
N10W02Ctrl

↓

そのまま公開

↓

Clientからそのまま呼び出す
```

という構成になっています。

つまり

サーバー側にメソッドを追加すると、
クライアント側でも同じ名前で利用できます。

クライアント用 API を再実装する必要はありません。

---

# Local Usage

ローカル PC 上で直接利用する場合は

```python
from n10w02 import N10W02Ctrl

camera = N10W02Ctrl(
    camera_ip="10.170.10.42",
)

image = camera.capture_bmp_bytes()

with open("capture.bmp", "wb") as f:
    f.write(image)
```

これだけで画像を取得できます。

---

# gRPC Server

サーバーは数行で起動できます。

```python
from n10w02.grpc_server import n10w02_grpc_server

n10w02_grpc_server(
    camera_ip="10.170.10.42",
    grpc_host="0.0.0.0",
    grpc_port=50051,
)
```

サーバー内部では

- COM 初期化
- ORiN2 接続
- Camera Provider 接続

を自動で実行します。

---

# Remote Client

別 PC から利用する場合は

```python
from n10w02.grpc_client import N10W02GrpcClient

client = N10W02GrpcClient(
    server_ip="10.170.10.38",
    grpc_port=50051,
)

image = client.capture_bmp_bytes()
```

ローカル API とほぼ同じ感覚で利用できます。

---

# Why BMP?

本ライブラリでは JPEG ではなく BMP を基本形式としています。

理由は

- カメラの生データを保持できる
- 圧縮処理が不要
- OpenCV 等へそのまま渡せる
- 画像品質が変化しない

ためです。

必要に応じて利用側で JPEG や PNG へ変換してください。

---

# Error Handling

接続処理はコンストラクタで実行されます。

```python
camera = N10W02Ctrl(...)
```

接続できない場合は例外が送出されます。

これは

> 接続できない状態でオブジェクトだけ存在する

ことを避けるためです。

アプリケーションは起動時に接続確認が完了した状態になります。

---

# Logging

ライブラリ全体は x_logger を前提に設計されています。

各処理では

- 接続開始
- 接続完了
- COM 初期化
- Provider 接続
- 画像取得
- 切断

などのログを出力します。

そのため、障害解析も容易になっています。

---

# Summary

このライブラリの特徴は以下の通りです。

- ORiN2 を隠蔽する
- Python オブジェクトをそのまま公開する
- gRPC の API を手作業で実装しない
- ローカル・リモートで同じ API を利用できる
- 画像を通常の RPC として転送する
- シンプルな構成でアプリケーションを作成できる

アプリケーション開発者は ORiN2 や COM の詳細を意識することなく、通常の Python ライブラリと同じ感覚で N10-W02 を利用できます。

---
## 作者
- Kengo NAKADA (kengo.nakada@gmail.com)
