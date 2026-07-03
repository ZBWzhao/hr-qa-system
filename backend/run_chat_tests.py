#!/usr/bin/env python3
"""
智能问答模块自动化测试

用法:
  python run_chat_tests.py                  # 单元 + API 集成
  python run_chat_tests.py --unit-only      # 仅单元测试
  python run_chat_tests.py --api-only       # 仅 API 集成（需后端运行）
  python run_chat_tests.py --report out.json
  python run_chat_tests.py --base-url http://127.0.0.1:8000/api/v1
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import uuid
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

BACKEND_DIR = Path(__file__).resolve().parent
CASES_FILE = BACKEND_DIR / "test_cases_chat.json"

ANSWER_TYPE_LABELS = {
    "faq": "标准答案",
    "rule": "规则答案",
    "rag": "已查阅制度文档",
    "clarification": "需要补充信息",
    "miss": "未找到明确依据",
    "ticket_clarification": "工单申请",
    "ticket_confirm": "待确认工单",
    "ticket_submitted": "工单已提交",
    "ticket_qa": "工单咨询",
}


@dataclass
class StepResult:
    step_index: int
    question: str
    action: Optional[str]
    passed: bool
    expected_types: list[str]
    actual_type: str
    must_contain: list[str]
    missing_keywords: list[str]
    answer_preview: str
    error: Optional[str] = None


@dataclass
class CaseResult:
    case_id: str
    module: str
    kind: str  # single | multi
    passed: bool
    description: str = ""
    steps: list[StepResult] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class UnitResult:
    script: str
    passed: bool
    duration_sec: float
    output_tail: str
    error: Optional[str] = None


def load_cases() -> dict:
    with open(CASES_FILE, encoding="utf-8") as f:
        return json.load(f)


def http_json(method: str, url: str, data: Optional[dict] = None, token: Optional[str] = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_server(base_url: str) -> tuple[bool, str]:
    try:
        res = http_json("GET", f"{base_url.rstrip('/')}/health")
        if res.get("code") == 0:
            return True, "ok"
        return False, res.get("message", "health check failed")
    except urllib.error.URLError as e:
        return False, str(e.reason if hasattr(e, "reason") else e)
    except Exception as e:
        return False, str(e)


def login(base_url: str, username: str, password: str) -> str:
    res = http_json("POST", f"{base_url.rstrip('/')}/auth/login", {
        "username": username,
        "password": password,
    })
    if res.get("code") != 0:
        raise RuntimeError(f"登录失败: {res.get('message')}")
    token = res["data"]["access_token"]
    return token


def chat(
    base_url: str,
    token: str,
    question: str,
    conversation_id: Optional[str] = None,
    action: Optional[str] = None,
) -> dict:
    payload: dict[str, Any] = {"question": question}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    if action:
        payload["action"] = action
    res = http_json("POST", f"{base_url.rstrip('/')}/chat", payload, token=token)
    if res.get("code") != 0:
        raise RuntimeError(res.get("message") or "chat failed")
    return res["data"]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "").lower()


def check_must_contain(answer: str, keywords: list[str]) -> list[str]:
    """任一关键词组命中即可；同一关键词内逗号分隔为 OR"""
    if not keywords:
        return []
    norm_answer = normalize_text(answer)
    missing = []
    for kw in keywords:
        alternatives = [k.strip() for k in kw.split("|") if k.strip()]
        if not alternatives:
            alternatives = [kw]
        if not any(normalize_text(alt) in norm_answer for alt in alternatives):
            missing.append(kw)
    return missing


def evaluate_step(
    step_index: int,
    question: str,
    action: Optional[str],
    expected_types: list[str],
    must_contain: list[str],
    data: dict,
) -> StepResult:
    actual_type = data.get("answer_type") or ""
    answer = data.get("answer") or ""
    type_ok = actual_type in expected_types if expected_types else True
    missing = check_must_contain(answer, must_contain)
    passed = type_ok and not missing
    preview = answer.replace("\n", " ")[:120]
    error_parts = []
    if not type_ok:
        expected_labels = [ANSWER_TYPE_LABELS.get(t, t) for t in expected_types]
        actual_label = ANSWER_TYPE_LABELS.get(actual_type, actual_type)
        error_parts.append(f"类型期望 {expected_labels}，实际 {actual_label}({actual_type})")
    if missing:
        error_parts.append(f"缺少关键词: {missing}")
    return StepResult(
        step_index=step_index,
        question=question,
        action=action,
        passed=passed,
        expected_types=expected_types,
        actual_type=actual_type,
        must_contain=must_contain,
        missing_keywords=missing,
        answer_preview=preview,
        error="; ".join(error_parts) if error_parts else None,
    )


def run_single_turn_case(base_url: str, token: str, case: dict) -> CaseResult:
    conv_id = str(uuid.uuid4())
    try:
        data = chat(base_url, token, case["question"], conversation_id=conv_id)
        step = evaluate_step(
            1,
            case["question"],
            None,
            case.get("expected_types", []),
            case.get("must_contain", []),
            data,
        )
        return CaseResult(
            case_id=case["id"],
            module=case.get("module", ""),
            kind="single",
            passed=step.passed,
            description=case.get("summary", case["question"]),
            steps=[step],
        )
    except Exception as e:
        return CaseResult(
            case_id=case["id"],
            module=case.get("module", ""),
            kind="single",
            passed=False,
            description=case.get("summary", case["question"]),
            error=str(e),
        )


def run_multi_turn_case(base_url: str, token: str, case: dict) -> CaseResult:
    conv_id = str(uuid.uuid4())
    steps: list[StepResult] = []
    all_pass = True
    err: Optional[str] = None
    try:
        for i, step_def in enumerate(case["steps"], start=1):
            data = chat(
                base_url,
                token,
                step_def["question"],
                conversation_id=conv_id,
                action=step_def.get("action"),
            )
            step = evaluate_step(
                i,
                step_def["question"],
                step_def.get("action"),
                step_def.get("expected_types", []),
                step_def.get("must_contain", []),
                data,
            )
            steps.append(step)
            if not step.passed:
                all_pass = False
                break
            time.sleep(0.15)
    except Exception as e:
        all_pass = False
        err = str(e)
    return CaseResult(
        case_id=case["id"],
        module=case.get("module", ""),
        kind="multi",
        passed=all_pass and not err,
        description=case.get("description", ""),
        steps=steps,
        error=err,
    )


def run_unit_script(script_name: str) -> UnitResult:
    script_path = BACKEND_DIR / script_name
    if not script_path.exists():
        return UnitResult(script=script_name, passed=False, duration_sec=0, output_tail="", error="文件不存在")
    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BACKEND_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
        duration = time.time() - start
        output = (proc.stdout or "") + (proc.stderr or "")
        tail = output[-2000:] if len(output) > 2000 else output
        passed = proc.returncode == 0 and "ALL PASSED" in output
        return UnitResult(
            script=script_name,
            passed=passed,
            duration_sec=round(duration, 2),
            output_tail=tail.strip(),
            error=None if passed else f"exit_code={proc.returncode}",
        )
    except subprocess.TimeoutExpired:
        return UnitResult(script=script_name, passed=False, duration_sec=300, output_tail="", error="timeout")
    except Exception as e:
        return UnitResult(script=script_name, passed=False, duration_sec=0, output_tail="", error=str(e))


def print_header(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def print_case_result(cr: CaseResult) -> None:
    status = "PASS" if cr.passed else "FAIL"
    print(f"\n[{status}] {cr.case_id} ({cr.module}) - {cr.description}")
    if cr.error:
        print(f"  错误: {cr.error}")
    for step in cr.steps:
        mark = "  +" if step.passed else "  -"
        action_note = f" [action={step.action}]" if step.action else ""
        label = ANSWER_TYPE_LABELS.get(step.actual_type, step.actual_type)
        print(f"{mark} step{step.step_index}: {step.question!r}{action_note}")
        print(f"      type: {label} ({step.actual_type})")
        if step.error:
            print(f"      {step.error}")
        print(f"      answer: {step.answer_preview}...")


def print_unit_result(ur: UnitResult) -> None:
    status = "PASS" if ur.passed else "FAIL"
    print(f"[{status}] {ur.script} ({ur.duration_sec}s)")
    if not ur.passed:
        if ur.error:
            print(f"  {ur.error}")
        if ur.output_tail:
            print("  --- output tail ---")
            for line in ur.output_tail.splitlines()[-8:]:
                print(f"  {line}")


def build_report(
    unit_results: list[UnitResult],
    api_results: list[CaseResult],
    server_ok: bool,
    server_msg: str,
) -> dict:
    unit_pass = sum(1 for u in unit_results if u.passed)
    api_pass = sum(1 for c in api_results if c.passed)
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "server": {"reachable": server_ok, "message": server_msg},
        "summary": {
            "unit_total": len(unit_results),
            "unit_passed": unit_pass,
            "unit_failed": len(unit_results) - unit_pass,
            "api_total": len(api_results),
            "api_passed": api_pass,
            "api_failed": len(api_results) - api_pass,
            "all_passed": (
                (not unit_results or unit_pass == len(unit_results))
                and (not api_results or api_pass == len(api_results))
            ),
        },
        "unit_tests": [asdict(u) for u in unit_results],
        "api_tests": [asdict(c) for c in api_results],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="智能问答模块自动化测试")
    parser.add_argument("--unit-only", action="store_true", help="仅运行单元测试脚本")
    parser.add_argument("--api-only", action="store_true", help="仅运行 API 集成测试")
    parser.add_argument("--report", default="test_chat_report.json", help="JSON 报告路径")
    parser.add_argument("--base-url", default=None, help="API 根路径，默认读 test_cases_chat.json")
    parser.add_argument("--user", default=None, help="登录用户名")
    parser.add_argument("--password", default=None, help="登录密码")
    args = parser.parse_args()

    cases = load_cases()
    meta = cases.get("meta", {})
    base_url = args.base_url or meta.get("api_base", "http://127.0.0.1:8000/api/v1")
    username = args.user or meta.get("default_user", "emp001")
    password = args.password or meta.get("default_password", "123456")

    run_unit = not args.api_only
    run_api = not args.unit_only

    unit_results: list[UnitResult] = []
    api_results: list[CaseResult] = []
    server_ok = False
    server_msg = "skipped"

    if run_unit:
        print_header("单元测试（离线，无需启动服务）")
        for script in cases.get("unit_scripts", []):
            ur = run_unit_script(script)
            unit_results.append(ur)
            print_unit_result(ur)

    if run_api:
        print_header("API 集成测试（需后端已启动）")
        server_ok, server_msg = check_server(base_url)
        if not server_ok:
            print(f"无法连接后端: {server_msg}")
            print(f"请先启动: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload")
        else:
            print(f"后端正常: {base_url}")
            try:
                token = login(base_url, username, password)
                print(f"已登录: {username}")
            except Exception as e:
                print(f"登录失败: {e}")
                token = None

            if token:
                print_header("单轮问答用例")
                for case in cases.get("single_turn", []):
                    cr = run_single_turn_case(base_url, token, case)
                    api_results.append(cr)
                    print_case_result(cr)

                print_header("多轮工单 / 追问用例")
                for case in cases.get("multi_turn", []):
                    cr = run_multi_turn_case(base_url, token, case)
                    api_results.append(cr)
                    print_case_result(cr)

    report = build_report(unit_results, api_results, server_ok, server_msg)
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = BACKEND_DIR / report_path
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print_header("汇总")
    s = report["summary"]
    if run_unit:
        print(f"单元测试: {s['unit_passed']}/{s['unit_total']} 通过")
    if run_api:
        if not server_ok:
            print(f"API 测试: 跳过（后端不可用）")
        else:
            print(f"API 测试: {s['api_passed']}/{s['api_total']} 通过")
    print(f"报告已写入: {report_path}")

    if run_unit and s["unit_failed"] > 0:
        return 1
    if run_api and server_ok and s["api_failed"] > 0:
        return 1
    if run_api and not server_ok:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
