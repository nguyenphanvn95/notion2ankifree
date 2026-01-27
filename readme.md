# Notion2Anki (Ổn định Anki 25+)

Addon này cho phép **đồng bộ nội dung từ Notion sang Anki** một cách tự động, hỗ trợ:
- Đồng bộ nhiều trang Notion
- Đổ thẻ vào deck hoặc sub-deck Anki
- Cập nhật toàn bộ hoặc cập nhật tăng dần
- Tự động đồng bộ theo chu kỳ

---

## 1. Yêu cầu hệ thống

- **Anki**: phiên bản **25.02+**
- **Python**: 3.9.x (đi kèm Anki)
- **Hệ điều hành**: Windows / macOS / Linux
- **Tài khoản Notion**: có quyền truy cập trang cần đồng bộ

---

## 2. Cài đặt addon

### Cách 1: Cài từ file zip (khuyến nghị)

1. Thoát Anki hoàn toàn
2. Giải nén addon vào thư mục:
```

C:\Users<USERNAME>\AppData\Roaming\Anki2\addons21\1826463337

```
3. Đảm bảo trong thư mục có các file:
- `__init__.py`
- `seeting_gui.py`
- `notion_client.py`
- `schemas/config_schema.json`
4. Mở lại Anki

👉 Nếu Anki mở không báo lỗi → addon đã load thành công.

---

## 3. Cách lấy Notion Token (bắt buộc)

Addon sử dụng **Notion token v2** (token đăng nhập trình duyệt).

### Các bước:
1. Mở Notion trên trình duyệt
2. Nhấn `F12` → tab **Application**
3. Vào:
```

Cookies → [https://www.notion.so](https://www.notion.so)

```
4. Tìm cookie có tên:
```

token_v2

```
5. Copy **giá trị token** (chuỗi rất dài)

⚠️ **Không chia sẻ token này cho người khác**

---

## 4. Mở giao diện cấu hình addon

Trong Anki:
- Menu **Tools → Notion2Anki → Settings**

Giao diện cài đặt đã được **dịch hoàn toàn sang tiếng Việt**.

---

## 5. Giải thích các trường cấu hình

### 5.1. Cài đặt chung

| Trường | Ý nghĩa |
|------|-------|
| **Notion Namespace** | Tên người dùng Notion (phần sau `notion.so/`) |
| **Notion Token** | Token lấy từ trình duyệt |
| **Sync every (minutes)** | Chu kỳ tự đồng bộ (phút). Đặt `0` để tắt auto sync |
| **Debug mode** | Bật để ghi log khi cần debug |

---

### 5.2. Bảng cấu hình trang Notion

Mỗi dòng tương ứng **một trang Notion** cần đồng bộ.

| Cột | Ý nghĩa |
|---|---|
| **PageID** | ID của trang Notion (32 ký tự) |
| **TargetDeck** | Tên deck Anki đích |
| **Recursive** | Đồng bộ cả trang con |
| **AbsUpdate** | Cập nhật toàn bộ |
| **IncUpdate** | Cập nhật tăng dần |

#### Cách lấy PageID
Ví dụ URL:
```

[https://www.notion.so/username/18cc2a7c7ba74d2b9b3fdd9f83d591e1?pvs=4](https://www.notion.so/username/18cc2a7c7ba74d2b9b3fdd9f83d591e1?pvs=4)

```
→ PageID là:
```

18cc2a7c7ba74d2b9b3fdd9f83d591e1

```

---

## 6. Giải thích chế độ cập nhật

### 🔁 Incremental Update (IncUpdate)
- Chỉ **thêm thẻ mới**
- Không xoá thẻ cũ
- Phù hợp dùng hằng ngày

### 🔄 Absolute Update (AbsUpdate)
- Đồng bộ **toàn bộ deck theo Notion**
- Thẻ không còn trong Notion sẽ **bị xoá**
- Phù hợp khi reset dữ liệu

⚠️ **Không bật đồng thời AbsUpdate và IncUpdate**

---

## 7. Cấu trúc deck & sub-deck

Addon hỗ trợ tạo **sub-deck** bằng dấu `:`.

Ví dụ:
```

TargetDeck = IELTS:Reading:Cambridge19

```

→ Anki sẽ tạo:
```

IELTS
└── Reading
└── Cambridge19

```

---

## 8. Đồng bộ thủ công

Sau khi cấu hình xong:
- Nhấn **Sync now** trong cửa sổ addon  
hoặc  
- Menu **Tools → Notion2Anki → Sync**

---

## 9. Các lỗi thường gặp & cách xử lý

### ❌ Lỗi: Page không sync, không có thẻ
- Kiểm tra PageID đúng chưa
- Đảm bảo trang Notion **không phải private**
- Token có còn hiệu lực không

---

### ❌ Lỗi: `IndexError: list index out of range`
✔️ Đã được **fix trong bản này**  
Nguyên nhân cũ: Notion trả về `results = []` khi task chưa sẵn sàng.

---

### ❌ Anki không load addon
- Xoá addon cũ hoàn toàn
- Giải nén lại đúng thư mục
- Kiểm tra không thiếu file `.py`

---

## 10. Điểm khác biệt của bản này

✔ Không yêu cầu đăng nhập user/password  
✔ Ổn định để dùng lâu dài

---

## 11. Ghi chú quan trọng

- Addon **không thuộc Notion chính thức**
- Không dùng cho dữ liệu nhạy cảm
- Nên backup deck Anki trước khi dùng **AbsUpdate**

---

## 12. Hỗ trợ & tuỳ biến

Bạn có thể:
- Tự chỉnh template thẻ Anki
- Kết hợp với AnkiConnect
- Gắn workflow học IELTS / Y khoa / Từ vựng chuyên ngành

---

Chúc bạn học tập hiệu quả với Notion & Anki 🚀
```

