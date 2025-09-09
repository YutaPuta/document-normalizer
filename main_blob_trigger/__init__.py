import logging
import os
import sys
import json
from pathlib import Path

import azure.functions as func

# プロジェクトのsrcディレクトリをPythonパスに追加
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

# モック関数を定義（Azureリソース未設定時用）
def run_pipeline(blob_name, pdf_bytes):
    """簡易パイプライン実行（モック版）"""
    try:
        validation_report = {
            "blob_name": blob_name,
            "errors": [],
            "warnings": ["This is a mock execution - Azure services not configured"],
            "info": [{"step": "mock_processing", "message": "Successfully processed in mock mode"}]
        }
        
        # 簡単なパターンマッチングで請求書を判定
        pdf_text = pdf_bytes.decode('utf-8', errors='ignore')
        
        cdm_data = {
            "doc": {
                "type": "INVOICE",
                "schema_version": "1.0", 
                "document_no": "MOCK-001",
                "issue_date": "2024-01-15",
                "currency": "JPY",
                "extraction_timestamp": "2024-01-15T10:00:00Z"
            },
            "lines": [],
            "totals": {},
            "metadata": {
                "confidence_scores": {},
                "unmapped_fields": []
            }
        }
        
        return True, cdm_data, validation_report, {"mock": True}
        
    except Exception as e:
        validation_report = {
            "blob_name": blob_name,
            "errors": [f"Mock pipeline error: {str(e)}"],
            "warnings": [],
            "info": []
        }
        return False, None, validation_report, {}

def save_artifacts(blob_name, raw_data, cdm_data, validation_report, container="artifacts"):
    """成果物保存（モック版）"""
    logging.info(f"[MOCK] Would save artifacts for {blob_name} to {container}")

def save_to_cosmos(cdm_data):
    """Cosmos DB保存（モック版）"""
    logging.info(f"[MOCK] Would save CDM data to Cosmos DB")

def main(inputBlob: func.InputStream) -> None:
    """Azure Functions Blob Trigger エントリポイント"""
    blob_name = inputBlob.name
    pdf_bytes = inputBlob.read()
    
    logging.info(f"Processing {blob_name} ({len(pdf_bytes)} bytes)")
    
    try:
        success, cdm_data, validation_report, raw_extraction = run_pipeline(blob_name, pdf_bytes)
        
        save_artifacts(
            blob_name=blob_name,
            raw_data=raw_extraction,
            cdm_data=cdm_data,
            validation_report=validation_report,
            container="artifacts"
        )
        
        if success and cdm_data:
            save_to_cosmos(cdm_data)
            logging.info(f"Successfully processed {blob_name}")
        else:
            logging.warning(f"Validation failed for {blob_name}: {validation_report}")
            
    except Exception as e:
        logging.error(f"Failed to process {blob_name}: {str(e)}", exc_info=True)
        raise