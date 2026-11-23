# Tái lập thí nghiệm 6 cặp RESTestBench

## Chấm lại từ kết quả lưu sẵn

Giải nén và chạy lệnh sau tại thư mục gốc của gói với Python 3.11 trở lên.

```text
python restest-extension/pilot.py score
```

Lệnh dùng thư viện chuẩn và ghi lại `restest-extension/results/comparison.csv` và `summary.csv`. Thư mục `RESTestBench/` trong gói là bản trích của commit `4decc1e36ea3dd41b64ce3e3ac6a85bc72df36ae` gồm 6 yêu cầu, OpenAPI và giấy phép AGPL-3.0. Bản trích đủ để chấm lại và tạo prompt. Kho đầy đủ cần thiết khi muốn khởi động FastAPI và áp mutant mới.

## Dữ liệu đã lưu

- `runs.jsonl` chứa 36 yêu cầu suy luận, định cấu hình giải mã và mask Y/N đã nhận.
- `observations.jsonl` chứa 6 quan sát bản gốc và 17 quan sát mutant. Các trường `checks` ghi kết quả của từng oracle ứng viên, `http_status` giữ mã phản hồi. Mã băm lưu cho tệp mutant đã xác minh trong container. Nhật ký không xuất token đăng nhập.
- `semantic_gold.json` chứa rubric gán nhãn một người. Kết quả đầu vào của mô hình lấy từ các văn bản yêu cầu, fixture và OpenAPI. `design.py` cố định kịch bản cùng mẫu luật. Bộ lọc dùng đúng mẫu của luật thuần và giữ giao với LLM.

## Sinh lại đầu ra mô hình

Khởi động [llama.cpp b5046](https://github.com/ggml-org/llama.cpp/releases/tag/b5046) trên `127.0.0.1:18787`, dùng [Qwen2.5-0.5B-Instruct Q4_K_M](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/blob/9217f5db79a29953eb74d5343926648285ec7e67/qwen2.5-0.5b-instruct-q4_k_m.gguf), chế độ CPU, 4 luồng, context 2048. SHA-256 của trọng số là `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`.

```text
python restest-extension/pilot.py generate --url http://127.0.0.1:18787 --output rerun
```

## Thu lại phản hồi API

Lấy kho [RESTestBench](https://github.com/casablancahotelsoftware/RESTestBench) đầy đủ tại commit `4decc1e36ea3dd41b64ce3e3ac6a85bc72df36ae` và đặt cạnh `restest-extension/`. Dùng hướng dẫn của tác giả để chuẩn bị bản `working` của FastAPI và image Docker. `compose-local.yml` là override cục bộ đã dùng để giới hạn API về loopback, bỏ xuất cổng cơ sở dữ liệu và đưa UI vào profile riêng. Lệnh `docker compose` của trình thực thi dùng thư mục `RESTestBench/services/fastapi/working` và kế thừa cấu hình Compose của terminal.

Trong một terminal PowerShell, trỏ `$env:COMPOSE_FILE` đến `docker-compose.yml|docker-compose.override.yml|docker-compose.codex.yml`, đặt `$env:COMPOSE_PATH_SEPARATOR='|'` và đặt tên project Compose riêng. Chép `compose-local.yml` thành `services/fastapi/working/docker-compose.codex.yml` rồi khởi động `docker compose up -d db prestart backend` từ thư mục working. Từ gốc gói, dùng Python có Requests 2.34.2 và chạy `python restest-extension/observe.py --output rerun`. Sau khi kết thúc, dừng nhóm Docker thử nghiệm. Các đoạn nguồn sửa trong working được trình thực thi phục hồi sau mỗi mutant. Cần hai tập log `rerun/runs.jsonl` và `rerun/observations.jsonl` để gọi `python restest-extension/pilot.py score --output rerun`.
