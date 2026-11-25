# Kiểm tra bản tái lập ngày 25 tháng 11 năm 2026

Lượt kiểm tra bắt đầu từ bản clone mới của commit `238468ff2ccdb20d08c648ed5ba4b5d98ebeb8d0`. Đã đối chiếu mã băm các tệp công bố, chạy lại bộ chấm điểm của pilot, tái tạo đầu ra mô hình và quan sát lại FastAPI trên Docker Linux cục bộ. Các lần tái tạo dùng thư mục đầu ra riêng.

| Kiểm tra | Kết quả |
| --- | --- |
| Hai pilot lưu trữ | Lệnh `verify_paper_results.py score` tính lại cả hai bảng và trả về PASS. |
| Đầu ra Qwen 0.5B và 7B | Cả hai mô hình khớp 36/36 bộ chọn FastAPI và 24/24 bộ chọn TodoApp, tổng cộng 120/120. Prompt và thiết lập lấy mẫu khớp từng lượt. Lượt 7B tiếp tục từ checkpoint sau một lỗi kết nối cục bộ. |
| Trọng số và runtime | SHA-256 của tệp Qwen 0.5B, hai shard 7B và tệp thực thi llama.cpp Vulkan khớp với [metadata](followup/environment.json). |
| Quan sát FastAPI mới | Chạy lại 6 ca bản gốc và 17 mutant trên Docker Linux riêng. Cả 23/23 bản ghi khớp từng mã HTTP, mã phản hồi phụ, kết quả assertion và mã băm nguồn mutant. |
| Demo HTTP độc lập | Trình chạy từ clone sạch trả về HTTP 400 cho cả hai phiên bản. Chi tiết đổi từ `Not enough permissions` thành `Item not found`. Assertion chính xác phát hiện sự thay đổi. |
| Bảng follow-up | Ba CSV đã công bố được tái tạo nguyên byte từ bộ chọn vừa sinh lại. Hai CSV bổ sung ghi phân hoạch ứng viên và 8 chính sách nhãn, với chính sách `000` kiểm tra lại đúng số liệu gốc. |

Lệnh `python verify_all.py --output verification-run` kiểm tra mã băm và tái tạo các bảng từ dữ liệu đã lưu. Để sinh lại mask, xem [lệnh và cấu hình](followup/README.md#regenerate-model-completions). Để thu lại 23 quan sát FastAPI, dùng [hướng dẫn chuẩn bị Docker và chạy observe](api/README.md).

Các phép kiểm tra này xác nhận khả năng tái lập trong môi trường đã ghi. TodoApp chỉ có dữ liệu chọn assertion và nhãn status. Bằng chứng về phát hiện mutant thuộc FastAPI. Phân tích độ nhạy dùng ba cách diễn giải thay thế. Độ đồng thuận giữa người chấm vẫn cần đo độc lập.

## Rà soát bản thảo sau v1.2.0

- Chấm lại hai pilot và tái tạo nguyên byte năm CSV follow-up, gồm 32 hàng độ nhạy cho tám chính sách nhãn. Đối chiếu 10 bảng trong bản thảo và 12 tỷ lệ ở Hình 2 với kết quả. Bảng ví dụ R4 kiểm tra riêng mã HTTP và thông điệp lỗi.
- Đối chiếu với commit RESTestBench được ghim. Sáu tệp yêu cầu FastAPI, đặc tả OpenAPI FastAPI và giấy phép khớp nguyên byte. Bốn cặp TodoApp khớp văn bản và phần đặc tả được trích.
- Đọc lại dữ liệu của lần tái lập trước. Cả 120 bộ chọn Vulkan khớp theo yêu cầu, biến thể, seed và thiết lập. Cả 23 quan sát HTTP khớp theo yêu cầu và mutant. Lượt rà soát bản thảo này dùng các bản ghi đã lưu.
- Đối chiếu 48 tài liệu tham khảo và 32 DOI với bản ghi chính thức. Sửa liên kết ClarifyGPT và bài về mơ hồ đại từ của Ezzini et al. Ghim bản arXiv v1 của Konstantinou et al. để tiêu đề khớp với phiên bản trích dẫn.
