# Tái lập thí nghiệm sinh ca kiểm thử

Thí điểm đo phần sinh kết quả mong đợi của ca kiểm thử hộp đen. Dữ liệu gồm 12 cặp yêu cầu tổng hợp bằng tiếng Anh và bảy đầu vào thử mỗi văn bản. Mỗi đầu vào có nhãn A, B, C hoặc `?` nếu yêu cầu chưa đủ căn cứ. Mô hình chạy cục bộ trên CPU.

## Đọc kết quả

- `results/summary.csv` chứa số đếm và mẫu số theo phương pháp, biến thể và kiểu thiếu thông tin.
- `results/oracles.csv` đối chiếu oracle với nhãn tham chiếu theo yêu cầu, đầu vào, prompt và seed. Dấu `?` là hoãn để làm rõ.
- `results/mutation.csv` ghi mỗi bộ ca từ yêu cầu đầy đủ, cảnh báo sai, số mutant đủ điều kiện, số bị loại và định danh các mutant bị loại. Bộ ca có ít nhất một oracle sai nhận 0 lượt loại mutant hữu hiệu.
- `results/runs.jsonl` lưu đúng 144 lần gọi, gồm prompt, tham số, đầu ra và thời gian. Hai prompt sinh 144 bộ nhãn thật. `abstain+gate` dùng cùng đầu ra của `abstain`, còn `rules` là đối chứng tất định.
- `requirements.json` là dữ liệu quan sát được. `reference.json` là nhãn và luật tham chiếu dùng khi chấm. Cột theo thứ tự là mã, toán tử, ngưỡng, nhãn nhánh đúng, nhãn nhánh còn lại và loại thành phần bị lược bỏ.
- `sources.tsv` là danh mục nguồn dạng bảng. `references-key.bib` chứa trích dẫn BibTeX cho các công trình cốt lõi đã xác minh thông tin tác giả.

## Tính lại số liệu

Mở thư mục vừa giải nén tại terminal. Dùng Python 3.10 trở lên. Trình chấm chỉ dùng thư viện chuẩn.

```powershell
python study.py score
```

Lệnh đọc dữ liệu đã chạy, kiểm tra toàn bộ tổ hợp, rồi ghi lại ba tệp CSV trong `results/`. Tám biến Dạng yêu cầu × Phương pháp trong báo cáo dùng các dòng `exact` hoặc `partial`. Ba dòng theo `comparator`, `cutoff` và `fallback` cung cấp phân tích theo thành phần bị lược bỏ ở bản thiếu thông tin.

Mỗi yêu cầu đầy đủ có sáu mutant đủ điều kiện trong miền 0–10. Các mutant của hai toán tử có thể có cùng hành vi nhưng được đếm riêng. Một vài mutant khác tham chiếu ở đầu vào ngoài bảy giá trị cố định. Nhóm này vẫn thuộc mẫu số và thể hiện giới hạn bao phủ đầu vào. Bản thiếu thông tin được chấm về căn cứ logic, vì việc dùng một hiện thực làm trọng tài cho mọi trường hợp mơ hồ sẽ tự chọn một cách diễn giải.

## Sinh lại từ mô hình

1. Tải [llama.cpp b5046](https://github.com/ggml-org/llama.cpp/releases/tag/b5046). Máy thí nghiệm dùng bản Windows x64 AVX2, mã nguồn `74d4f5b0`. SHA-256 của ZIP là `5d534b910f803fd5d4e137edcd58ebeb225a6b6d046ab6b3813d2c0d0ee8dcaf`.
2. Tải [Qwen2.5-0.5B-Instruct Q4_K_M tại revision đã dùng](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/blob/9217f5db79a29953eb74d5343926648285ec7e67/qwen2.5-0.5b-instruct-q4_k_m.gguf). SHA-256 đã kiểm tra với LFS của kho tác giả là `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`.
3. Khởi động server trên loopback. Chạy lệnh sau từ thư mục chứa bản llama.cpp và trọng số, hoặc thay bằng đường dẫn tương ứng.

```powershell
.\llama-server.exe --host 127.0.0.1 --port 18786 -t 4 -c 1024 -ngl 0 -m qwen2.5-0.5b-instruct-q4_k_m.gguf
```

4. Trong terminal khác, tại thư mục gói thí nghiệm, chạy vào thư mục kết quả mới.

```powershell
python study.py all --output rerun
```

Lần chạy mới dùng seed 11, 23 và 47, temperature 0,3, top-k 40 và top-p 0,95. Thứ tự gọi được xáo cố định bằng seed 20261115. Đầu ra bị ràng buộc vào bảy nhãn A/B/C/? phân tách bằng dấu phẩy. Thời gian và đầu ra lấy mẫu có thể thay đổi theo bản dựng và phần cứng. Nếu lượt sinh bị ngắt giữa chừng, chạy lại đúng lệnh để tiếp tục từ các lượt đã lưu.

## Phạm vi

Corpus dùng mẫu ngôn ngữ có cấu trúc để kiểm tra từng trường hợp. Quy luật và bộ tham chiếu được viết riêng nhưng dựa trên cùng cấu trúc. Số liệu dùng cho nghiên cứu thăm dò. Báo cáo đề xuất benchmark công khai, tách dự án và chấm độc lập cho bước tiếp theo.
