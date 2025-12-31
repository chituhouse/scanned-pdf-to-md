#!/usr/bin/env python3
"""
火山引擎OCR API调用模块
封装通用文字识别和智能文档解析两个API
"""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from urllib.parse import urlencode, quote
import requests

from config import (
    AK, SK, API_HOST, API_REGION, API_SERVICE,
    OCR_NORMAL_ACTION, OCR_NORMAL_VERSION,
    OCR_PDF_ACTION, OCR_PDF_VERSION,
    REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY
)


def hmac_sha256(key: bytes, msg: str) -> bytes:
    """HMAC-SHA256签名"""
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def hash_sha256(content: str) -> str:
    """SHA256哈希"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def create_authorization(action: str, version: str, body: str) -> tuple:
    """
    创建API请求的Authorization头
    返回: (authorization, x_date)
    """
    now = datetime.now(timezone.utc)
    x_date = now.strftime('%Y%m%dT%H%M%SZ')
    short_date = now.strftime('%Y%m%d')

    # Query参数
    query_params = {"Action": action, "Version": version}
    query_string = "&".join([f"{k}={quote(str(v), safe='')}" for k, v in sorted(query_params.items())])

    # 规范请求
    method = "POST"
    canonical_uri = "/"
    canonical_headers = f"content-type:application/x-www-form-urlencoded\nhost:{API_HOST}\nx-date:{x_date}\n"
    signed_headers = "content-type;host;x-date"
    hashed_payload = hash_sha256(body)

    canonical_request = f"{method}\n{canonical_uri}\n{query_string}\n{canonical_headers}\n{signed_headers}\n{hashed_payload}"

    # 待签名字符串
    algorithm = "HMAC-SHA256"
    credential_scope = f"{short_date}/{API_REGION}/{API_SERVICE}/request"
    string_to_sign = f"{algorithm}\n{x_date}\n{credential_scope}\n{hash_sha256(canonical_request)}"

    # 计算签名
    k_date = hmac_sha256(SK.encode('utf-8'), short_date)
    k_region = hmac_sha256(k_date, API_REGION)
    k_service = hmac_sha256(k_region, API_SERVICE)
    k_signing = hmac_sha256(k_service, "request")
    signature = hmac.new(k_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    # Authorization头
    authorization = f"{algorithm} Credential={AK}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"

    return authorization, x_date, query_string


def call_api(action: str, version: str, body_params: dict) -> dict:
    """
    调用火山引擎API

    Args:
        action: API名称 (OCRNormal / OCRPdf)
        version: API版本
        body_params: Body参数字典

    Returns:
        API响应JSON
    """
    body = urlencode(body_params)
    authorization, x_date, query_string = create_authorization(action, version, body)

    url = f"https://{API_HOST}/?{query_string}"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": API_HOST,
        "X-Date": x_date,
        "Authorization": authorization
    }

    # 重试机制
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(url, headers=headers, data=body, timeout=REQUEST_TIMEOUT)
            result = resp.json()

            # 检查是否成功
            if result.get("code") == 10000:
                return result

            # API返回错误
            error_info = result.get("ResponseMetadata", {}).get("Error", {})
            error_code = error_info.get("Code", result.get("code"))
            error_msg = error_info.get("Message", result.get("message", ""))

            # 某些错误不需要重试
            if error_code in [50205, 50207]:  # 文件大小/格式错误
                return result

            last_error = f"{error_code}: {error_msg}"

        except requests.exceptions.Timeout:
            last_error = "请求超时"
        except requests.exceptions.RequestException as e:
            last_error = f"请求异常: {str(e)}"
        except json.JSONDecodeError:
            last_error = "响应解析失败"

        # 重试前等待
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY * (attempt + 1))

    # 所有重试都失败
    return {"code": -1, "message": f"重试{MAX_RETRIES}次后失败: {last_error}"}


def ocr_normal(image_path: str) -> dict:
    """
    通用文字识别

    Args:
        image_path: 图片文件路径

    Returns:
        {
            "success": bool,
            "line_texts": [...],  # 识别的文本行
            "line_probs": [...],  # 每行置信度
            "raw_response": {...}  # 原始响应
        }
    """
    # 读取图片
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode()

    body_params = {
        "image_base64": image_base64,
    }

    result = call_api(OCR_NORMAL_ACTION, OCR_NORMAL_VERSION, body_params)

    if result.get("code") == 10000:
        data = result.get("data", {})
        return {
            "success": True,
            "line_texts": data.get("line_texts", []),
            "line_probs": data.get("line_probs", []),
            "raw_response": result
        }
    else:
        return {
            "success": False,
            "error": result.get("message", "未知错误"),
            "line_texts": [],
            "line_probs": [],
            "raw_response": result
        }


def ocr_pdf(image_path: str, table_mode: str = "markdown") -> dict:
    """
    智能文档解析

    Args:
        image_path: 图片文件路径
        table_mode: 表格输出格式 ("markdown" / "html")

    Returns:
        {
            "success": bool,
            "markdown": str,  # Markdown格式结果
            "textblocks": [...],  # 结构化文本块
            "has_table": bool,  # 是否包含表格
            "raw_response": {...}
        }
    """
    # 读取图片
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode()

    body_params = {
        "image_base64": image_base64,
        "version": "v3",
        "file_type": "image",
        "table_mode": table_mode,
        "filter_header": "true"
    }

    result = call_api(OCR_PDF_ACTION, OCR_PDF_VERSION, body_params)

    if result.get("code") == 10000:
        data = result.get("data", {})
        markdown = data.get("markdown", "")

        # 解析detail获取textblocks
        textblocks = []
        has_table = False
        detail = data.get("detail", "")
        if detail:
            try:
                detail_json = json.loads(detail) if isinstance(detail, str) else detail
                if isinstance(detail_json, list) and len(detail_json) > 0:
                    textblocks = detail_json[0].get("textblocks", [])
                    # 检查是否有表格
                    has_table = any(block.get("label") == "table" for block in textblocks)
            except (json.JSONDecodeError, KeyError, IndexError):
                pass

        return {
            "success": True,
            "markdown": markdown,
            "textblocks": textblocks,
            "has_table": has_table,
            "raw_response": result
        }
    else:
        return {
            "success": False,
            "error": result.get("message", "未知错误"),
            "markdown": "",
            "textblocks": [],
            "has_table": False,
            "raw_response": result
        }


# 测试
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        test_image = sys.argv[1]
    else:
        test_image = "../PDF_image/三级历年真题及解析_08.png"

    print(f"测试图片: {test_image}")
    print("=" * 50)

    # 测试通用OCR
    print("\n【通用文字识别】")
    result1 = ocr_normal(test_image)
    if result1["success"]:
        print(f"成功，识别到 {len(result1['line_texts'])} 行")
        for line in result1['line_texts'][:5]:
            print(f"  {line}")
    else:
        print(f"失败: {result1['error']}")

    # 测试智能文档解析
    print("\n【智能文档解析】")
    result2 = ocr_pdf(test_image)
    if result2["success"]:
        print(f"成功，包含表格: {result2['has_table']}")
        print(f"Markdown前200字符:\n{result2['markdown'][:200]}")
    else:
        print(f"失败: {result2['error']}")
