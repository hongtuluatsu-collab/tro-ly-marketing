import os
import json
import httpx
from flask import Flask, render_template, request, jsonify, stream_with_context, Response

app = Flask(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
HEADERS = {
    "content-type": "application/json",
    "anthropic-version": "2023-06-01",
    "anthropic-beta": "web-search-2025-03-05",
}


def build_payload(prompt: str) -> dict:
    return {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2500,
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        "messages": [{"role": "user", "content": prompt}],
    }


def call_claude(prompt: str) -> str:
    if not ANTHROPIC_API_KEY:
        return "❌ Chưa cấu hình ANTHROPIC_API_KEY. Vui lòng thêm vào Environment Variables trên Railway."

    payload = build_payload(prompt)
    with httpx.Client(timeout=120) as client:
        resp = client.post(
            ANTHROPIC_URL,
            headers={**HEADERS, "x-api-key": ANTHROPIC_API_KEY},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        texts = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        return "\n".join(texts)


# ── Routes ──────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/research", methods=["POST"])
def api_research():
    body = request.get_json()
    query = body.get("query", "").strip()
    scope = body.get("scope", "both")
    rtype = body.get("type", "market")

    if not query:
        return jsonify({"error": "Vui lòng nhập chủ đề cần nghiên cứu."}), 400

    scope_map = {"both": "trong nước và quốc tế", "vn": "trong nước Việt Nam", "intl": "quốc tế"}
    type_map = {
        "market": "thị trường và xu hướng",
        "competitor": "đối thủ cạnh tranh",
        "legal": "văn bản pháp luật mới",
        "opportunity": "cơ hội kinh doanh",
    }

    prompt = f"""Bạn là chuyên gia phân tích thị trường pháp lý cho Công ty Luật Minh Tú tại TP.HCM.
Hãy thực hiện nghiên cứu tổng hợp {scope_map.get(scope, 'trong nước và quốc tế')} về: "{query}"
Loại phân tích: {type_map.get(rtype, 'thị trường và xu hướng')}

Viết báo cáo chuyên nghiệp bằng tiếng Việt gồm:
# Tóm tắt điều hành
## Phân tích chi tiết
## Xu hướng chính
## Cơ hội & Thách thức
## Khuyến nghị cho Công ty Luật Minh Tú

Súc tích, có số liệu cụ thể, thực tế với thị trường Việt Nam."""

    try:
        result = call_claude(prompt)
        return jsonify({"result": result})
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return jsonify({"error": "API Key không hợp lệ. Kiểm tra lại Environment Variable."}), 401
        return jsonify({"error": f"Lỗi API: {e.response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/news", methods=["POST"])
def api_news():
    body = request.get_json()
    filters = body.get("filters", ["bds", "nn", "pl", "tt"])
    content_type = body.get("contentType", "post")
    extra = body.get("extra", "").strip()

    topic_map = {
        "bds": "bất động sản",
        "nn": "người nước ngoài tại Việt Nam",
        "pl": "pháp lý doanh nghiệp",
        "tt": "tố tụng tại toà án",
    }
    topics = [topic_map[f] for f in filters if f in topic_map]

    ct_map = {
        "post": "bài viết content marketing cho Facebook/Website (hook mạnh, phân tích vấn đề, CTA liên hệ Luật Minh Tú)",
        "video": "kịch bản video ngắn 60-90 giây (Hook 5s → Intro thương hiệu → Nội dung chính → Outro CTA)",
        "mc": 'kịch bản MC cho chương trình "Alo Luật Sư" (lời dẫn → giới thiệu vấn đề → câu hỏi gợi mở luật sư → câu kết)',
    }

    prompt = f"""Bạn là chuyên gia content marketing cho Công ty Luật Minh Tú tại TP.HCM.

NHIỆM VỤ: Tìm 10 tin pháp lý nóng nhất hôm nay về: {", ".join(topics)}.
Sau đó soạn {ct_map.get(content_type, ct_map["post"])} cho tin nổi bật nhất.
{"Yêu cầu thêm: " + extra if extra else ""}

ĐỊNH DẠNG:
## 📰 10 TIN NÓNG HÔM NAY
(Mỗi tin: số thứ tự, tiêu đề, nguồn, tóm tắt 2 câu, lĩnh vực, độ hot ★)

---
## ✍️ NỘI DUNG SOẠN THẢO (tin số 1)
[Soạn đầy đủ theo định dạng đã chọn]

---
## 💡 GỢI Ý CHỦ ĐỀ TIẾP THEO (3 ý tưởng)

Viết tiếng Việt, sắc bén, thu hút."""

    try:
        result = call_claude(prompt)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/plan", methods=["POST"])
def api_plan():
    body = request.get_json()
    goals = body.get("goals", "").strip()
    revenue = body.get("revenue", "").strip()
    budget = body.get("budget", "").strip()
    focus = body.get("focus", "all")
    market = body.get("market", "hcm")
    timeframe = body.get("timeframe", "5y")

    if not goals:
        return jsonify({"error": "Vui lòng nhập mục tiêu kinh doanh."}), 400

    focus_map = {"all": "tất cả lĩnh vực", "bds": "bất động sản", "nn": "người nước ngoài", "corp": "pháp lý doanh nghiệp", "liti": "tố tụng"}
    market_map = {"hcm": "TP. Hồ Chí Minh", "hn": "Hà Nội", "national": "toàn quốc", "regional": "TP.HCM và vùng lân cận"}
    plan_map = {"5y": "5 NĂM (2025-2030)", "3y": "3 NĂM (2025-2027)", "1y": "1 NĂM (2025)", "month": "THÁNG"}

    prompt = f"""Bạn là Giám đốc Chiến lược Marketing cho Công ty Luật Minh Tú — chuyên về BĐS, người nước ngoài, pháp lý doanh nghiệp và tố tụng. Có chương trình "Alo Luật Sư" nổi tiếng tại TP.HCM.

XÂY DỰNG KẾ HOẠCH MARKETING {plan_map.get(timeframe, "5 NĂM")}:
- Doanh thu mục tiêu: {revenue or "chưa xác định"}
- Ngân sách marketing: {budget or "đề xuất phù hợp"}
- Lĩnh vực trọng tâm: {focus_map.get(focus, "tất cả")}
- Thị trường: {market_map.get(market, "TP. Hồ Chí Minh")}
- Mục tiêu chiến lược: {goals}

Kế hoạch gồm:
# PHÂN TÍCH TÌNH HÌNH (SWOT + thị trường)
# MỤC TIÊU MARKETING (KPIs SMART)
# CHIẾN LƯỢC MARKETING MIX
## Digital (SEO, Social, YouTube "Alo Luật Sư")
## Content & PR
## Offline & Networking
# PHÂN BỔ NGÂN SÁCH (bảng chi tiết theo %)
# LỘ TRÌNH TRIỂN KHAI (timeline + milestone)
# ĐO LƯỜNG & KPI DASHBOARD

Viết tiếng Việt, chuyên nghiệp, số liệu thực tế, có thể triển khai ngay."""

    try:
        result = call_claude(prompt)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "api_key_set": bool(ANTHROPIC_API_KEY),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
