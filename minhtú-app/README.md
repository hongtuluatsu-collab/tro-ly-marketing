# Minh Tú Law — Marketing Intelligence App

Ứng dụng hỗ trợ marketing chuyên nghiệp cho Công ty Luật Minh Tú, xây dựng bằng Python Flask + Claude AI.

## Tính năng

- **Module 01** — Nghiên cứu tổng hợp thị trường pháp lý trong và ngoài nước
- **Module 02** — Tìm 10 tin nóng mỗi ngày & soạn content / kịch bản video / kịch bản MC "Alo Luật Sư"
- **Module 03** — Hoạch định kế hoạch marketing chiến lược (5 năm / 3 năm / 1 năm / tháng)

## Cấu trúc project

```
minhtú-app/
├── app.py              # Flask backend
├── requirements.txt    # Python dependencies
├── Procfile            # Gunicorn start command
├── railway.json        # Railway config
└── templates/
    └── index.html      # Frontend
```

## Deploy lên Railway

### Bước 1 — Push lên GitHub
```bash
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/[username]/[repo-name].git
git push -u origin main
```

### Bước 2 — Tạo project trên Railway
1. Vào [railway.app](https://railway.app) → New Project
2. Chọn **Deploy from GitHub repo**
3. Chọn repo vừa push

### Bước 3 — Cấu hình Environment Variable
Trong Railway dashboard:
1. Vào tab **Variables**
2. Nhấn **New Variable**
3. Thêm: `ANTHROPIC_API_KEY` = `sk-ant-...`

### Bước 4 — Deploy
Railway tự động build và deploy. Sau vài phút sẽ có link dạng:
`https://[tên-project].up.railway.app`

## Chạy local (để test)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python app.py
```

Mở trình duyệt: `http://localhost:5000`
