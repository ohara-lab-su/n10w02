[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/n10w02/en/changelog.html)
[![ja](https://img.shields.io/badge/lang-ja-blue.svg)](https://ohara-lab-su.github.io/n10w02/ja/changelog.html)

# Changelog

## v0.0.4, 2026-08-10, nakada

- gRPC 画像転送機能を拡張
  - `grpc_frame` の `StreamCall` 対応(v0.5.11)に合わせて server-streaming による連続画像転送を追加
  - 従来の `capture_bmp_bytes()` による1枚単位の画像取得はそのまま維持
  - 新たに `stream_bmp_bytes()` を追加し、1つの gRPC 接続上で画像を連続取得可能に変更
  - 通常の API 呼び出しと画像ストリームを分離
    - 通常 API：`Call` による unary RPC
    - 連続画像転送：`StreamCall` による server-streaming RPC
  - 画像の取得周期を指定する `fps` に対応
  - `focus=True` の場合、ストリーム開始時のみフォーカスを実行
  - COM アクセスは従来どおり `ComExecutionRunner` / `ThreadSafeCtrlProxy` を経由し、既存の COM 実行モデルを維持
  - 画像サーバーは画像の取得・転送までを担当し、画像処理、物体認識、座標抽出等はクライアント側で自由に実装できる構成とした

- example を更新
  - `n10w02_server.py` を streaming 対応サーバー構成に更新
  - 従来の1枚取得用 `n10w02_client.py` を維持
  - server-streaming を利用する `n10w02_client_stream.py` を追加
  - 現在のパッケージ構成 `n10w02.grpc_server` に合わせて import path を修正

- 後方互換性
  - 既存の `capture_bmp_bytes()` および従来の gRPC クライアント API は変更なし
  - streaming は追加機能として実装し、従来の1回呼び出し型 API をそのまま利用可能

## v0.0.3, 2026-07-28, nakada

- after cobotta3/4 setup
 
## v0.0.2, 2026-07-15, nakada

- improve
  - `N10W02Ctrl` に x_logger 対応を追加
  - 制御処理のログ出力を強化
  - サーバー運用向けに例外処理を改善
    - 起動時の接続失敗のみ例外を送出
    - 起動後の制御処理は例外を内部で処理し、ログ出力後に `False` を返すよう変更

## v0.0.1, 2026-07-15, nakada

- fix

## v0.0.0, 2026-07-03, nakada
 
- Initial release
  - grpc_server
  - local_ctrl
