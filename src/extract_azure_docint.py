import logging
import os
import time
from typing import Dict, Any, Optional
import requests
from io import BytesIO

logger = logging.getLogger(__name__)

def extract_with_document_intelligence(pdf_bytes: bytes, doc_type: str) -> Optional[Dict[str, Any]]:
    """
    Azure AI Document Intelligenceを使用してPDFからデータを抽出
    
    Args:
        pdf_bytes: PDFファイルのバイトデータ
        doc_type: 文書種別（INVOICE or PURCHASE_ORDER）
        
    Returns:
        抽出された生データ（辞書形式）
    """
    endpoint = os.environ.get("DOCUMENT_INTELLIGENCE_ENDPOINT", "").rstrip("/")
    api_key = os.environ.get("DOCUMENT_INTELLIGENCE_API_KEY", "")
    
    if not endpoint or not api_key:
        logger.error("Document Intelligence credentials not configured")
        return None
    
    try:
        model_id = get_model_id(doc_type)
        
        analyze_url = f"{endpoint}/formrecognizer/documentModels/{model_id}:analyze"
        params = {
            "api-version": "2023-07-31",
            "locale": "ja-JP"
        }
        headers = {
            "Ocp-Apim-Subscription-Key": api_key,
            "Content-Type": "application/pdf"
        }
        
        logger.info(f"Sending document to Document Intelligence (model: {model_id})")
        response = requests.post(
            analyze_url,
            params=params,
            headers=headers,
            data=pdf_bytes,
            timeout=30
        )
        
        if response.status_code != 202:
            logger.error(f"Failed to start analysis: {response.status_code} - {response.text}")
            return None
        
        operation_location = response.headers.get("Operation-Location")
        if not operation_location:
            logger.error("No operation location returned")
            return None
        
        result = poll_for_result(operation_location, api_key)
        
        if result and result.get("status") == "succeeded":
            return process_extraction_result(result.get("analyzeResult", {}), doc_type)
        else:
            logger.error(f"Analysis failed: {result}")
            return None
            
    except Exception as e:
        logger.error(f"Document Intelligence extraction error: {str(e)}", exc_info=True)
        return None

def get_model_id(doc_type: str) -> str:
    """文書種別に応じたモデルIDを取得"""
    model_map = {
        "INVOICE": "prebuilt-invoice",
        "PURCHASE_ORDER": "prebuilt-document"
    }
    return model_map.get(doc_type, "prebuilt-document")

def poll_for_result(operation_location: str, api_key: str, max_attempts: int = 30) -> Optional[Dict]:
    """
    非同期操作の結果をポーリング
    """
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    
    for attempt in range(max_attempts):
        time.sleep(2)
        
        response = requests.get(operation_location, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Polling attempt {attempt + 1} failed: {response.status_code}")
            continue
        
        result = response.json()
        status = result.get("status")
        
        if status == "succeeded":
            logger.info("Document analysis completed successfully")
            return result
        elif status == "failed":
            logger.error(f"Analysis failed: {result.get('error')}")
            return None
        
        logger.debug(f"Analysis status: {status} (attempt {attempt + 1}/{max_attempts})")
    
    logger.error("Analysis timed out")
    return None

def process_extraction_result(analyze_result: Dict, doc_type: str) -> Dict[str, Any]:
    """
    Document Intelligenceの結果を処理
    """
    processed_data = {
        "doc_type": doc_type,
        "fields": {},
        "tables": [],
        "key_value_pairs": {},
        "raw_text": "",
        "confidence_scores": {}
    }
    
    if "documents" in analyze_result and analyze_result["documents"]:
        doc = analyze_result["documents"][0]
        processed_data["fields"] = extract_fields(doc.get("fields", {}))
        processed_data["confidence_scores"] = extract_confidence_scores(doc.get("fields", {}))
    
    if "tables" in analyze_result:
        processed_data["tables"] = extract_tables(analyze_result["tables"])
    
    if "keyValuePairs" in analyze_result:
        processed_data["key_value_pairs"] = extract_key_value_pairs(analyze_result["keyValuePairs"])
    
    if "content" in analyze_result:
        processed_data["raw_text"] = analyze_result["content"]
    
    logger.info(f"Extracted {len(processed_data['fields'])} fields, {len(processed_data['tables'])} tables")
    return processed_data

def extract_fields(fields: Dict) -> Dict[str, Any]:
    """フィールドデータを抽出"""
    extracted = {}
    
    for field_name, field_data in fields.items():
        if field_data and "content" in field_data:
            extracted[field_name] = field_data["content"]
        elif field_data and "valueString" in field_data:
            extracted[field_name] = field_data["valueString"]
        elif field_data and "valueNumber" in field_data:
            extracted[field_name] = field_data["valueNumber"]
        elif field_data and "valueDate" in field_data:
            extracted[field_name] = field_data["valueDate"]
        elif field_data and "valueObject" in field_data:
            extracted[field_name] = extract_fields(field_data["valueObject"])
        elif field_data and "valueArray" in field_data:
            extracted[field_name] = [
                extract_fields(item) if isinstance(item, dict) else item
                for item in field_data["valueArray"]
            ]
    
    return extracted

def extract_confidence_scores(fields: Dict) -> Dict[str, float]:
    """信頼度スコアを抽出"""
    scores = {}
    
    for field_name, field_data in fields.items():
        if field_data and "confidence" in field_data:
            scores[field_name] = field_data["confidence"]
    
    return scores

def extract_tables(tables: list) -> list:
    """テーブルデータを抽出"""
    extracted_tables = []
    
    for table in tables:
        rows = []
        current_row = []
        current_row_idx = 0
        
        for cell in table.get("cells", []):
            row_idx = cell.get("rowIndex", 0)
            
            if row_idx != current_row_idx:
                if current_row:
                    rows.append(current_row)
                current_row = []
                current_row_idx = row_idx
            
            current_row.append(cell.get("content", ""))
        
        if current_row:
            rows.append(current_row)
        
        if rows:
            extracted_tables.append({
                "rows": rows,
                "row_count": table.get("rowCount", len(rows)),
                "column_count": table.get("columnCount", max(len(row) for row in rows) if rows else 0)
            })
    
    return extracted_tables

def extract_key_value_pairs(kv_pairs: list) -> Dict[str, str]:
    """キーバリューペアを抽出"""
    extracted = {}
    
    for pair in kv_pairs:
        key = pair.get("key", {}).get("content", "")
        value = pair.get("value", {}).get("content", "")
        
        if key and value:
            extracted[key] = value
    
    return extracted