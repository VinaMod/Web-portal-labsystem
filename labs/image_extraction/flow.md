**<span style="color:red">Lab: Image Extraction</span>**

Bài lab này tập trung vào việc khai thác sự bất cẩn trong quá trình vận hành và chia sẻ tài liệu của doanh nghiệp, dẫn đến rò rỉ thông tin nhạy cảm qua Metadata hoặc dữ liệu văn bản bị bỏ sót. Mục tiêu là thực hiện một chuỗi tấn công phân tích, trích xuất dữ liệu từ các tệp PDF, DOCX để lắp ghép thành một tài khoản truy cập hợp lệ và đăng nhập thành công vào Employee Portal.

**Bài lab đáp ứng các CLO nào**

**CLO 6**: Nhận diện, phân loại và khai thác các lỗ hổng rò rỉ thông tin liên quan đến siêu dữ liệu (Metadata Leakage) và dữ liệu thừa (Data Remnants) trong các tệp tin công khai.

**CLO 3**: Vận dụng thành thạo các công cụ phân tích dòng lệnh (ví dụ: `exiftool`, `strings`) để quét, kiểm tra và trích xuất dữ liệu ẩn từ nhiều định dạng tài liệu khác nhau (PDF, DOCX, JPG).

**CLO 6**: Có kỹ năng thu thập và tư duy xâu chuỗi các mảnh thông tin rời rạc (Credential Assembly) để tìm ra thông tin đăng nhập mục tiêu và truy cập vào các hệ thống nội bộ.

**Kỹ thuật dự kiến làm bài Lab Image Extraction.**

1. Khai thác PDF Metadata Analysis: Thu thập các tài liệu từ website công khai của doanh nghiệp. Sử dụng công cụ `exiftool` để phân tích tệp `employee_handbook.pdf` và kiểm tra trường thông tin người tạo (Author), từ đó phát hiện và trích xuất định dạng Username đăng nhập (`manh.dev`).

2. Khai thác DOCX Strings Search: Sử dụng công cụ `strings` (hoặc thực hiện giải nén file) để rà quét toàn bộ dữ liệu thô bề mặt của tệp `meeting_notes.docx`. Tìm kiếm các đoạn ghi chú (comment) và nội dung bị bỏ quên để phục hồi lại mật khẩu tạm thời (`Summer2026!`).

3. Kỹ thuật Credential Assembly: Tổng hợp thông tin đăng nhập đã trích xuất thành công từ hai tệp trên để tạo thành một bộ tài khoản hoàn chỉnh. Truy cập trang Employee Portal (`/portal/login.php`) và thực hiện đăng nhập để lấy Flag hệ thống.
