# Trình diễn HTTP thật với Docker

Tải toàn bộ kho và giải nén, hoặc clone kho. Mở PowerShell tại thư mục có `http_demo.py`, `http-demo-source.zip` và `requirements-http.txt`. Giữ ba tệp này cùng nhau. Không cần thư mục HTTP-Demo bên ngoài.

## Chạy trên máy trình bày hiện tại

Docker Desktop và hai image thử nghiệm đã được chuẩn bị trên máy tác giả. Chạy:

```powershell
py -3.14 .\http_demo.py --interactive
```

Trình chạy tìm Docker, kiểm tra Engine, giải nén nguồn theo mã băm và tạo môi trường Python riêng. Lần cài thư viện đầu tiên cần Internet nếu các gói chưa có. Cấu hình dùng khóa thử ngẫu nhiên được tạo tại máy, không nằm trong GitHub. Không cần kích hoạt venv hoặc đổi ExecutionPolicy.

## Điểm dừng bản gốc

Đợi thông báo:

```text
ORIGINAL: HTTP 400, detail='Not enough permissions'
Original service is running. Press ENTER here to inject the message mutant...
```

Chưa nhấn Enter. Mở http://127.0.0.1:8000/docs trong trình duyệt để xem Swagger. Trong PowerShell thứ hai, có thể gửi GET kiểm tra dịch vụ:

```powershell
Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8000/api/v1/utils/health-check/'
```

Kết quả health check là True, chỉ chứng minh dịch vụ sẵn sàng. Demo chính thực hiện POST đăng ký hai tài khoản, POST đăng nhập, POST tạo item bằng tài khoản thứ nhất và GET đọc item bằng tài khoản thứ hai, với token phù hợp. Token không được in ra màn hình.

## Áp mutant và giải thích kết quả

Quay lại cửa sổ demo và nhấn Enter một lần. Chương trình đổi thông báo, khởi động lại backend, xác minh mã đã sửa trong container và gửi HTTP lần nữa.

```text
Original response: HTTP 400, detail='Not enough permissions'
Mutant response:   HTTP 400, detail='Item not found'

Oracle                                     Original    Mutant
Vague | HTTP is 4xx                            PASS      PASS
Precise | HTTP 400 and expected detail         PASS      FAIL

PASS: Both real HTTP responses reproduced. The precise check detected the mutant.
```

FAIL trên mutant nghĩa là phát hiện thay đổi do lỗi thành công. Yêu cầu rõ ràng quy định thông báo nên cho phép kiểm tra chính xác; kiểm tra chung 4xx của yêu cầu mơ hồ vẫn chấp nhận cả hai phản hồi. Đây là một yêu cầu và một mutant minh họa, không phải 17 mutant hoặc một lần sinh LLM mới.

Nhấn Enter lần nữa để chương trình dừng và dọn container/database tạm của lần demo trước khi đóng PowerShell. Sau bước này, Swagger không còn hoạt động cho đến lần chạy tiếp theo. Có thể chạy tự động không dừng bằng `py -3.14 .\http_demo.py`.

## Nếu cổng 8000 bị chiếm

Kiểm tra:

```powershell
docker ps --format "{{.Names}} {{.Ports}}"
```

Nếu là lượt demo đang chờ Enter ở cửa sổ khác, quay lại đó và hoàn tất các điểm dừng để dọn container. Nếu cửa sổ cũ đã đóng, chỉ dừng đúng container demo cũ đã xác định, ví dụ tên bắt đầu bằng restestbench-defense-. Không dừng nhầm dịch vụ khác. Lệnh demo không tự tắt ứng dụng đang giữ cổng.

## Chuẩn bị trên máy khác

Cần Python 3.12 trở lên, Docker Desktop với Linux Engine, Internet cho lần chuẩn bị và dung lượng cho image. Các image không được đính kèm trong GitHub. Khi thiếu image, yêu cầu chuẩn bị rõ ràng bằng:

```powershell
py -3.14 .\http_demo.py --build-images --interactive
```

Chương trình chỉ build/pull image còn thiếu: postgres:17 và restestbench-codex-fastapi-backend:4decc1e. Dựng image từ Dockerfile và nguồn đóng băng có thể mất nhiều phút. Không cam kết image dựng mới giống từng byte với image gốc; ghi lại digest và môi trường nếu tái lập trên máy khác.

Để chỉ kiểm tra giải nén và tạo cấu hình, không chạy Docker hoặc HTTP:

```powershell
py -3.14 .\http_demo.py --prepare-only
```

SHA256SUMS.txt nhận diện các tệp của kho. Trình chạy cũng xác minh riêng mã băm của ZIP nguồn. Các tệp `.http-demo-*`, `.venv`, `.env` và `__pycache__` là đầu ra cục bộ, không đưa vào Git.
