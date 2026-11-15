"""平台教务 mock 服务。

Agent 服务通过它读取实时业务事实（报名订单、排课、退费进度、课程名额）。
只做只读查询，不实现真实支付与退费执行。

启动：python mock-academic/main.py   （默认 127.0.0.1:8081）
"""

from __future__ import annotations

import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Query

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

app = FastAPI(title="教务服务 (mock)")

# ── 种子数据 ──────────────────────────────────────────
COURSES: dict[int, dict] = {
    101: {
        "id": 101,
        "name": "考研英语全程班",
        "code": "KY-ENG-2027",
        "category": "考研",
        "price": 3980.0,
        "stock": 120,
        "active": True,
        "returnable": True,
        "highlights": "全程直播 + 作文批改；开班前可全额退费",
        "promotion": {
            "promotionName": "开学季考研专场",
            "promotionType": "term_discount",
            "discountSummary": "开学季满 3000 减 400，可与续报券叠加，同一订单最多一张券。",
            "promotionPrice": 3580.0,
            "requiredMemberLevel": "all",
            "conditionSummary": "全等级学员可参与",
        },
    },
    102: {
        "id": 102,
        "name": "少儿编程启蒙课",
        "code": "KID-CODE-L1",
        "category": "少儿",
        "price": 2380.0,
        "stock": 60,
        "active": True,
        "returnable": True,
        "highlights": "12 节直播 + 图形化项目；开课 7 天内可退",
        "promotion": {
            "promotionName": "开学季少儿专场",
            "promotionType": "term_discount",
            "discountSummary": "两科联报立减 300，续报券不可叠加。",
            "promotionPrice": 2080.0,
            "requiredMemberLevel": "all",
            "conditionSummary": "适用新学员首报",
        },
    },
    103: {
        "id": 103,
        "name": "雅思冲刺强化班",
        "code": "IELTS-SPRINT",
        "category": "出国",
        "price": 4600.0,
        "stock": 30,
        "active": True,
        "returnable": False,
        "highlights": "小班 6 人；开课后不可退费",
        "promotion": {
            "promotionName": "开学季出国专场",
            "promotionType": "term_discount",
            "discountSummary": "满 4000 减 500，不与续报券叠加。",
            "promotionPrice": 4100.0,
            "requiredMemberLevel": "gold",
            "conditionSummary": "金卡学员专享",
        },
    },
}

ENROLLMENTS: dict[str, dict] = {
    "EN20260901000001-A0921": {
        "enrollmentNo": "EN20260901000001-A0921",
        "userId": "U1001",
        "paymentStatus": "PAID",
        "enrollmentStatus": "CLASS_STARTED",
        "classProgressStatus": "CLASS_IN_PROGRESS",
        "classStartedAt": "2026-09-05T19:00:00",
        "returnable": True,
        "items": [{"productId": 101, "courseName": "考研英语全程班"}],
    },
    "EN20260901000002-B0922": {
        "enrollmentNo": "EN20260901000002-B0922",
        "userId": "U1001",
        "paymentStatus": "PAID",
        "enrollmentStatus": "PAID_PENDING_CLASS",
        "classProgressStatus": "PENDING_CLASS",
        "items": [{"productId": 102, "courseName": "少儿编程启蒙课"}],
    },
    "EN20260712000010-A0923": {
        "enrollmentNo": "EN20260712000010-A0923",
        "userId": "U1001",
        "paymentStatus": "PAID",
        "enrollmentStatus": "CLASS_STARTED",
        "classProgressStatus": "CLASS_STARTED",
        "classStartedAt": "2026-07-12T09:00:00",
        "returnable": True,
        "items": [{"productId": 102, "courseName": "少儿编程启蒙课"}],
    },
}

AFTER_SALE: dict[str, list[dict]] = {
    "EN20260901000001-A0921": [
        {
            "requestId": "RF-20260908-0009",
            "enrollmentNo": "EN20260901000001-A0921",
            "userId": "U1001",
            "requestType": "REFUND",
            "status": "REVIEWING",
            "submittedAt": "2026-09-08T10:12:00",
        }
    ]
}


def ok(data):
    return {"success": True, "data": data}


@app.get("/health")
def health():
    return {"status": "ok", "service": "academic-mock"}


@app.get("/api/orders/{enrollment_no}")
def get_order(enrollment_no: str):
    order = ENROLLMENTS.get(enrollment_no)
    if order is None:
        return {"success": False, "message": "enrollment not found"}
    return ok(order)


@app.get("/api/products")
def search_products(keyword: str = Query(default="")):
    normalized = (keyword or "").replace(" ", "")
    if not normalized:
        return ok(list(COURSES.values()))
    hits = [
        course
        for course in COURSES.values()
        if any(
            term in normalized and term in course["name"]
            for term in ("考研", "英语", "编程", "少儿", "雅思", "冲刺")
        )
        or course["name"] in normalized
    ]
    if not hits:
        hits = [c for c in COURSES.values() if c["active"]]
    return ok(hits)


@app.get("/api/products/{product_id}")
def get_product(product_id: int):
    course = COURSES.get(product_id)
    if course is None:
        return {"success": False, "message": "course not found"}
    return ok(course)


@app.get("/api/after-sale/requests")
def after_sale_requests(enrollmentNo: str = Query(default="")):
    return ok(AFTER_SALE.get(enrollmentNo, []))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8081, log_level="warning")
