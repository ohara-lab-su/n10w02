# Changelog

## 0.0.2, 2026-07-15, nakada

- improve
  - `N10W02Ctrl` に x_logger 対応を追加
  - 制御処理のログ出力を強化
  - サーバー運用向けに例外処理を改善
    - 起動時の接続失敗のみ例外を送出
    - 起動後の制御処理は例外を内部で処理し、ログ出力後に `False` を返すよう変更

## 0.0.1, 2026-07-15, nakada

- fix

## 0.0.0, 2026-07-03, nakada
 
- Initial release
  - grpc_server
  - local_ctrl