# Changelog

## v0.0.4, 2026-08-10, nakada

- Extended gRPC image transfer functionality
  - Added continuous image transfer using server-streaming, in line with `grpc_frame` support for `StreamCall` (v0.5.11).
  - Preserved the existing single-image acquisition method, `capture_bmp_bytes()`.
  - Added `stream_bmp_bytes()` to allow continuous image acquisition over a single gRPC connection.
  - Separated ordinary API calls from image streaming:
    - Ordinary API: unary RPC via `Call`.
    - Continuous image transfer: server-streaming RPC via `StreamCall`.
  - Added support for `fps` to specify the image acquisition interval.
  - When `focus=True`, focusing is performed only when the stream starts.
  - COM access continues to go through `ComExecutionRunner` / `ThreadSafeCtrlProxy`, preserving the existing COM execution model.
  - The image server is responsible only for image acquisition and transfer; image processing, object recognition, coordinate extraction, and related tasks can be implemented freely on the client side.

- Updated examples
  - Updated `n10w02_server.py` to use a server configuration that supports streaming.
  - Retained the existing single-image client, `n10w02_client.py`.
  - Added `n10w02_client_stream.py`, which uses server-streaming.
  - Corrected import paths to match the current `n10w02.grpc_server` package structure.

- Backward compatibility
  - The existing `capture_bmp_bytes()` method and conventional gRPC client API are unchanged.
  - Streaming is an additional feature; the existing single-call API remains available.

## v0.0.3, 2026-07-28, nakada

- After cobotta3/4 setup.

## v0.0.2, 2026-07-15, nakada

- Improvements
  - Added `x_logger` support to `N10W02Ctrl`.
  - Enhanced logging for control operations.
  - Improved exception handling for server operation:
    - Only connection failures during startup raise exceptions.
    - After startup, control operations handle exceptions internally, log them, and return `False`.

## v0.0.1, 2026-07-15, nakada

- Fixes.

## v0.0.0, 2026-07-03, nakada

- Initial release
  - grpc_server
  - local_ctrl
