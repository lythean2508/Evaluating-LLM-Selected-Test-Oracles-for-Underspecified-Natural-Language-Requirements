# Đối chiếu với các nghiên cứu gần nhất

Bài này đo việc chọn assertion từ một danh sách cố định khi độ chi tiết của yêu cầu thay đổi. Ba cấu hình dùng cùng kịch bản và quan sát thực thi. Phân tích chia các ứng viên có căn cứ theo bốn nhóm do LLM, quy tắc, cả hai hoặc không bên nào chọn. Hai đóng góp thực nghiệm tiếp theo là đo trần bao phủ của quy tắc đóng băng trên tập giữ lại và kiểm tra độ nhạy của so sánh 0.5B với 7B theo cách gán nhãn.

| Nghiên cứu | Thiết kế được tác giả công bố | Điểm khác trong bài này |
| --- | --- | --- |
| Ma và Eisty | Sinh mã oracle Java từ yêu cầu nghiệp vụ gắn với lỗi thực Defects4J. [Bài tác giả](https://arxiv.org/abs/2607.10277) | Cố định mã và ứng viên, thay đổi mức chi tiết của yêu cầu rồi đo phần bị mất do giao hai bộ chọn. |
| Ding | Rà test có sẵn trong benchmark coding agent để tìm kỳ vọng triển khai mà mô tả nhiệm vụ chưa nêu. [Bài tác giả](https://arxiv.org/abs/2610.30635) | Đo thực nghiệm các lựa chọn do LLM và quy tắc đưa ra trên cùng ứng viên, sau đó chấm phát hiện mutant có điều kiện. |
| Madani et al. | Đóng hoặc mở quyền bắt đầu sinh đầu ra cho toàn bộ yêu cầu dựa trên mức đủ thông tin. [Bài IEEE](https://doi.org/10.1109/RE68928.2026.00028) · [Mã tác giả](https://github.com/PedramMadani/spec-gate) | Đơn vị lọc là từng assertion. Đo riêng phần ứng viên đúng bị loại và bộ kiểm thử rỗng. |
| RESTestBench | Cung cấp yêu cầu REST API theo cặp và phép đo mutation gắn với yêu cầu. [Bài tác giả](https://arxiv.org/abs/2604.25862) | Dùng các cặp và mutant của benchmark làm nguồn dữ liệu, giữ nguyên hành động và quan sát để cô lập quyết định chọn oracle. |
| ReqTestAgent | Xử lý yêu cầu mơ hồ, sinh ca chấp nhận và dùng thực thi để kiểm chứng. [Bài nhà xuất bản](https://doi.org/10.3389/frai.2026.1960601) | Chấm căn cứ của từng assertion đối với văn bản hiển thị và đo trần của quy tắc đóng băng. |
| Req2Test-Bench | Đánh giá test do agent viết ở cấp kho mã từ yêu cầu và giao diện mục tiêu. [Bài tác giả](https://arxiv.org/abs/2610.36584) | Cố định phần thực thi để so sánh công bằng đúng ba bộ chọn assertion. |
| TOGLL và TOGBench | Sinh hoặc đánh giá oracle trong ngữ cảnh unit test Java, gồm oracle do lập trình viên viết trong TOGBench. [TOGLL](https://arxiv.org/abs/2405.03786) · [TOGBench](https://doi.org/10.1145/3805760.3814927) | Nguồn căn cứ là yêu cầu tự nhiên hiện ra ở từng biến thể. Cặp mơ hồ và chính xác dùng chung kịch bản và danh sách assertion. |
| Mughal và Bilal | Tổng quan 83 nghiên cứu theo nguồn căn cứ của oracle. [IEEE Access](https://doi.org/10.1109/ACCESS.2026.3729738) | Chuyển một loại nguồn căn cứ thành thước đo hoạt động, rồi replay các quy ước gán nhãn thay thế trên cùng dữ liệu. |

Các công trình ngoài bài này mô tả phạm vi và cách đo có liên quan. Kết quả định lượng trong bản thảo thuộc các cấu hình được chạy trong chính gói tái lập.

## Phạm vi tìm nguồn

Lượt tìm mở rộng ngày 25/11/2026 dùng tra cứu học thuật trên web, arXiv, chương trình hội nghị và trang dự án của tác giả. Các nhóm truy vấn kết hợp `natural-language requirements` với `test oracle`, `assertion selection`, `underspecified`, `requirement support`, `specification-oracle gap`, `sufficiency gating`, `retention` và `mutation testing`. Tên và DOI của các công trình gần nhất được tra riêng để đối chiếu bản tác giả và thông tin công bố. Ưu tiên công trình có chung đầu vào yêu cầu, cách quyết định tính đúng của oracle, hoặc thiết kế đo phát hiện lỗi.

[Danh mục 40 tài liệu trong bài](SOURCES.md) là tập nguồn đã đối chiếu cho bản thảo này. Hai điểm xuất phát để tiếp tục sàng lọc là bộ [267 nghiên cứu Requirements-Based Test Generation](https://github.com/aimeenorwind/SLR-on-RBTG) và [gói tái lập của tổng quan nguồn căn cứ oracle](https://zenodo.org/records/21194941).
