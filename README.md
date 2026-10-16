# **HƯỚNG DẪN CÀI ĐẶT VÀ KHỞI CHẠY DỰ ÁN BIG DATA - FPS TELEMETRY**

Tài liệu này hướng dẫn chi tiết quy trình thiết lập môi trường và vận hành hệ thống phân tích dữ liệu lớn trên nền tảng **Apache Spark**, **Docker** và giao diện **Streamlit Dashboard** thông qua các kịch bản tự động hóa `.bat`.

<br>

## **📝 BƯỚC 1. YÊU CẦU CHUẨN BỊ TRƯỚC KHI CÀI ĐẶT**

Để đảm bảo hệ thống tự động hóa hoạt động chính xác và không bị lỗi trong quá trình thực nghiệm, máy tính cần cài đặt sẵn công cụ nền tảng sau **(Link tải ở cuối README)**:

- **Docker Desktop:** Dùng để quản lý, đóng gói và chạy tự động toàn bộ môi trường phân tán gồm Linux Debian, Java OpenJDK 21, Apache Spark 3.5.1, Python 3.10 và Streamlit.
- **Dung lượng ổ đĩa:** Ổ đĩa cài đặt dự án phải còn trống ít nhất 8GB để Docker tải các Image nền tảng và đóng gói môi trường.

<br>

**⚠️ LƯU Ý QUAN TRỌNG VỀ TỐI ƯU PHẦN CỨNG (WSL2 / RAM)**

Mặc định máy ảo Linux của Docker Desktop (WSL2) có thể chiếm dụng tới 50% tổng dung lượng RAM của máy tính. Để tránh tình trạng thiếu hụt bộ nhớ khi Spark thực thi các phép tính phân tán nặng, bạn nên cấu hình giới hạn tài nguyên như sau:

1. Nhấn tổ hợp phím `Windows + R`, gõ `%UserProfile%` rồi nhấn **Enter**.
2. Tạo một file văn bản mới tên là **`.wslconfig`** (chọn lưu dưới dạng All Files).
3. Dán nội dung cấu hình sau vào và lưu lại:
   ```ini
   [wsl2]
   memory=3GB
   processors=4
   autoMemoryReclaim=gradual
   ```
4. Mở Command Prompt (CMD) gõ `wsl --shutdown` để hệ thống áp dụng giới hạn này.

<br>

**⚠️ LƯU Ý KHI KHỞI CHẠY DOCKER**

- Trước khi thực hiện cài đặt hoặc chạy dự án, luôn đảm bảo phần mềm **Docker Desktop đã được bật và đang ở trạng thái Engine running**.
- Toàn bộ quy trình cài đặt môi trường và khởi chạy đã được tự động hóa hoàn toàn 100%, không cần cài cắm bất kỳ phần mềm nào trực tiếp vào máy chủ Windows.

<br>

## **🚀 BƯỚC 2. QUY TRÌNH KHỞI CHẠY VÀ KIỂM THỬ HỆ THỐNG (Hết)**

Hệ thống được thiết kế theo kiến trúc 2 tầng độc lập: tầng xử lý dữ liệu lớn bằng **Apache Spark Engine** và tầng hiển thị trực quan qua **Web Dashboard**.

<br>

### 1: THIẾT LẬP MÔI TRƯỜNG DOCKER BAN ĐẦU (Chỉ chạy 1 lần duy nhất)

1. Mở sẵn phần mềm Docker Desktop.
2. Di chuyển vào thư mục dự án `Du_an_Big_Data_FPS_Telemetry`.
3. Click đúp chuột để chạy file `setup.bat`.

_Cơ chế hoạt động:_ Kịch bản sẽ tự động kiểm tra Docker, tải Image nền tảng, thiết lập OpenJDK 21, Python 3.10 và nạp đầy đủ các thư viện PySpark, Pandas, Scikit-Learn, Streamlit vào container `bigdata-fps-engine`. Khi cửa sổ hiện thông báo `[OK] CAI DAT HOAN TAT!`, nhấn phím bất kỳ để kết thúc.

<br>

### 2: THỰC THI ĐƯỜNG ỐNG XỬ LÝ PHÂN TÁN APACHE SPARK

Để minh chứng năng lực xử lý phân tán dữ liệu lớn độc lập trên cụm Spark:

- Click đúp chuột để chạy file `run_spark_pipeline.bat`.

_Cơ chế hoạt động:_ Kịch bản sẽ giao việc cho bộ máy Apache Spark thực hiện:

- Đọc tập dữ liệu lớn qua **Spark DataFrame**.
- Tiền xử lý, làm sạch và chuẩn hóa dữ liệu phân tán.
- Huấn luyện mô hình phân cụm phong cách chơi qua thư viện **Spark MLlib (K-means)** kèm đánh giá hệ số **Silhouette**.
- Thực thi truy vấn **Spark SQL** để xếp hạng và đánh giá cân bằng vũ khí.
- Chuyển đổi và nén lưu trữ dữ liệu sang định dạng cột tối ưu **Parquet**.

<br>

### 3: KHỞI CHẠY GIAO DIỆN TRỰC QUAN HÓA

Để mở bảng điều khiển trực quan tương tác phục vụ báo cáo và nghiệm thu:

- Click đúp chuột để chạy file `run_demo.bat`.

_Kết quả:_ Trình duyệt web sẽ tự động mở trang Dashboard tại địa chỉ:

- Giao diện Web Demo: http://localhost:8501
- Giao diện Giám sát Spark UI: http://localhost:4040

<br>

### 4: TIỆN ÍCH DỌN DẸP DOCKER (Khi hoàn thành)

Nếu muốn giải phóng hoàn toàn dung lượng ổ đĩa và gỡ bỏ toàn bộ môi trường Docker sau khi xong:

- Click đúp chuột vào file `clean_docker.bat`.
- File sẽ tự động dừng và xóa sạch container, image và dọn sạch bộ nhớ đệm (Build Cache) của Docker chỉ với một thao tác.

<br>

## **📂 CẤU TRÚC THƯ MỤC DỰ ÁN**

Cấu trúc thư mục nguồn được tổ chức như sau:

```ini
Du_an_Big_Data_FPS_Telemetry/
│
├── dataset/                    <-- [GitHub] Thư mục chứa dữ liệu và ảnh bản đồ
│   └── ...
│
├── scripts/                    <-- [GitHub] Kịch bản thực thi độc lập với Spark
│   └── ...
│
├── src/                        <-- [GitHub] Mã nguồn ứng dụng Web Dashboard
│   └── ...
│
├── docker-compose.yml          <-- [GitHub]
│
├── Dockerfile                  <-- [GitHub]
│
├── requirements.txt            <-- [GitHub]
│
├── .gitattributes              <-- [GitHub]
│
├── .gitignore                  <-- [GitHub]
│
├── setup.bat                   <-- [GitHub] Kịch bản khởi tạo môi trường tự động
│
├── run_spark_pipeline.bat      <-- [GitHub] Kịch bản chạy Pipeline phân tán với Apache Spark
│
├── run_demo.bat                <-- [GitHub] Kịch bản khởi chạy Web Dashboard
│
├── clean_docker.bat            <-- [GitHub] Tiện ích dọn dẹp tài nguyên Docker
│
└── README.md                   <-- [GitHub]
```

<br>

## **🌐 NGUỒN GỐC DỮ LIỆU THỰC NGHIỆM**

- **Bộ dữ liệu gốc:** Bộ dữ liệu đo đạc từ xa trận đấu PUBG được công bố công khai trên nền tảng Kaggle tại đường dẫn: https://www.kaggle.com/datasets/skihikingkevin/pubg-match-deaths/data
- **Đặc điểm dữ liệu gốc:** Tập dữ liệu gốc bao gồm 2 tệp lớn là `agg_match_stats_0.csv` (dữ liệu tổng hợp chỉ số người chơi) và `kill_match_stats_final_0.csv` (dữ liệu chi tiết từng sự kiện hạ gục), với dung lượng mỗi tệp khoảng 2.0 GB (tổng cộng gần 4.0 GB với hơn 13 triệu dòng).
- **Xử lý tối ưu dung lượng trong dự án:** Do giới hạn về tài nguyên phần cứng máy tính cá nhân (RAM 8GB - 16GB) không thể nạp trực tiếp toàn bộ 4.0 GB dữ liệu thô vào bộ nhớ cùng lúc khi chạy giao diện trực quan, đồng thời để thuận tiện nén nộp bài và đưa lên kho lưu trữ GitHub, tôi đã tiến hành trích xuất có kiểm soát thành 2 tập dữ liệu mẫu chuẩn hóa:
  - **Tập mẫu thử nghiệm (50.000 dòng):** Dùng để kiểm thử nhanh các biểu đồ và giao diện với độ trễ tối thiểu.
  - **Tập thực nghiệm lớn (300.000 dòng):** Đóng vai trò là tập dữ liệu quy mô lớn đại diện cho bài toán Big Data để kiểm thử hiệu năng xử lý phân tán của Apache Spark và thuật toán phân cụm K-means.

<br>

## **📥 LINK TẢI CÔNG CỤ NỀN TẢNG**

Để thuận tiện cho việc cài đặt và kiểm thử, có thể truy cập nhanh vào đường link chính thức dưới đây để tải Docker:

- Tải Docker Desktop: https://docs.docker.com/desktop/setup/install/windows-install/
