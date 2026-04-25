import os
import httpx
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "minhtú-law-secret-2025")

# ── Config từ Environment Variables ──────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
LOGIN_USERNAME    = os.environ.get("LOGIN_USERNAME", "admin")
LOGIN_PASSWORD    = os.environ.get("LOGIN_PASSWORD", "minhtú2025")

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
API_HEADERS = {
    "content-type": "application/json",
    "anthropic-version": "2023-06-01",
    "anthropic-beta": "web-search-2025-03-05",
}


# ── Auth decorator ────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Claude helper ─────────────────────────────────────────────
def call_claude(prompt: str) -> str:
    if not ANTHROPIC_API_KEY:
        return "❌ Chưa cấu hình ANTHROPIC_API_KEY trong Railway Variables."
    with httpx.Client(timeout=120) as client:
        resp = client.post(
            ANTHROPIC_URL,
            headers={**API_HEADERS, "x-api-key": ANTHROPIC_API_KEY},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 2500,
                "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return "\n".join(b["text"] for b in data.get("content", []) if b.get("type") == "text")


# ── Auth routes ───────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == LOGIN_USERNAME and password == LOGIN_PASSWORD:
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("index"))
        error = "Tên đăng nhập hoặc mật khẩu không đúng."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Main app ──────────────────────────────────────────────────
@app.route("/")
@login_required
def index():
    return render_template("index.html", username=session.get("username"))


@app.route("/api/health")
@login_required
def health():
    return jsonify({"status": "ok", "api_key_set": bool(ANTHROPIC_API_KEY)})


# ── API endpoints ─────────────────────────────────────────────
@app.route("/api/research", methods=["POST"])
@login_required
def api_research():
    body  = request.get_json()
    query = body.get("query", "").strip()
    if not query:
        return jsonify({"error": "Vui lòng nhập chủ đề cần nghiên cứu."}), 400

    scope_map = {"both": "trong nước và quốc tế", "vn": "trong nước Việt Nam", "intl": "quốc tế"}
    type_map  = {"market": "thị trường và xu hướng", "competitor": "đối thủ cạnh tranh",
                 "legal": "văn bản pháp luật mới", "opportunity": "cơ hội kinh doanh"}

    prompt = f"""Bạn là chuyên gia phân tích thị trường pháp lý cho Công ty Luật Minh Tú tại TP.HCM.
Hãy nghiên cứu tổng hợp {scope_map.get(body.get('scope','both'))} về: "{query}"
Loại phân tích: {type_map.get(body.get('type','market'))}

Viết báo cáo tiếng Việt chuyên nghiệp gồm:
# Tóm tắt điều hành
## Phân tích chi tiết
## Xu hướng chính
## Cơ hội & Thách thức
## Khuyến nghị cho Công ty Luật Minh Tú

Súc tích, số liệu cụ thể, thực tế với thị trường Việt Nam."""

    try:
        return jsonify({"result": call_claude(prompt)})
    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        if code == 401:
            return jsonify({"error": "API Key không hợp lệ."}), 401
        return jsonify({"error": f"Lỗi Anthropic API: {code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/news", methods=["POST"])
@login_required
def api_news():
    body         = request.get_json()
    filters      = body.get("filters", ["bds", "nn", "pl", "tt"])
    content_type = body.get("contentType", "post")
    extra        = body.get("extra", "").strip()

    topic_map = {"bds": "bất động sản", "nn": "người nước ngoài tại Việt Nam",
                 "pl": "pháp lý doanh nghiệp", "tt": "tố tụng tại toà án"}
    ct_map = {
        "post":  "bài viết content marketing cho Facebook/Website (hook mạnh, phân tích vấn đề, CTA liên hệ Luật Minh Tú)",
        "video": "kịch bản video ngắn 60-90 giây (Hook 5s → Intro thương hiệu → Nội dung chính → Outro CTA)",
        "mc":    'kịch bản MC chương trình "Alo Luật Sư" (lời dẫn → giới thiệu vấn đề → câu hỏi gợi mở → câu kết)',
    }

    prompt = f"""Bạn là chuyên gia content marketing cho Công ty Luật Minh Tú tại TP.HCM.

NHIỆM VỤ: Tìm 10 tin pháp lý nóng nhất hôm nay về: {", ".join(topic_map[f] for f in filters if f in topic_map)}.
Sau đó soạn {ct_map.get(content_type, ct_map['post'])} cho tin nổi bật nhất.
{"Yêu cầu thêm: " + extra if extra else ""}

ĐỊNH DẠNG:
## 📰 10 TIN NÓNG HÔM NAY
(Mỗi tin: số thứ tự, tiêu đề, nguồn, tóm tắt 2 câu, lĩnh vực, độ hot ★)

---
## ✍️ NỘI DUNG SOẠN THẢO (tin số 1)
[Soạn đầy đủ]

---
## 💡 GỢI Ý CHỦ ĐỀ TIẾP THEO (3 ý tưởng)

Viết tiếng Việt, sắc bén, thu hút."""

    try:
        return jsonify({"result": call_claude(prompt)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/plan", methods=["POST"])
@login_required
def api_plan():
    body  = request.get_json()
    goals = body.get("goals", "").strip()
    if not goals:
        return jsonify({"error": "Vui lòng nhập mục tiêu kinh doanh."}), 400

    focus_map  = {"all": "tất cả lĩnh vực", "bds": "bất động sản", "nn": "người nước ngoài",
                  "corp": "pháp lý doanh nghiệp", "liti": "tố tụng"}
    market_map = {"hcm": "TP. Hồ Chí Minh", "hn": "Hà Nội",
                  "national": "toàn quốc", "regional": "TP.HCM và vùng lân cận"}
    plan_map   = {"5y": "5 NĂM (2025-2030)", "3y": "3 NĂM (2025-2027)",
                  "1y": "1 NĂM (2025)", "month": "THÁNG"}

    prompt = f"""Bạn là Giám đốc Chiến lược Marketing cho Công ty Luật Minh Tú — chuyên BĐS, người nước ngoài, pháp lý doanh nghiệp, tố tụng. Có chương trình "Alo Luật Sư" nổi tiếng tại TP.HCM.

XÂY DỰNG KẾ HOẠCH MARKETING {plan_map.get(body.get('timeframe','5y'))}:
- Doanh thu mục tiêu: {body.get('revenue') or 'chưa xác định'}
- Ngân sách marketing: {body.get('budget') or 'đề xuất phù hợp'}
- Lĩnh vực trọng tâm: {focus_map.get(body.get('focus','all'))}
- Thị trường: {market_map.get(body.get('market','hcm'))}
- Mục tiêu: {goals}

Kế hoạch gồm:
# PHÂN TÍCH TÌNH HÌNH (SWOT + thị trường)
# MỤC TIÊU MARKETING (KPIs SMART)
# CHIẾN LƯỢC MARKETING MIX
## Digital (SEO, Social, YouTube "Alo Luật Sư")
## Content & PR
## Offline & Networking
# PHÂN BỔ NGÂN SÁCH (bảng chi tiết %)
# LỘ TRÌNH TRIỂN KHAI (timeline + milestone)
# ĐO LƯỜNG & KPI DASHBOARD

Viết tiếng Việt, chuyên nghiệp, số liệu thực tế, triển khai được ngay."""

    try:
        return jsonify({"result": call_claude(prompt)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Run ───────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
