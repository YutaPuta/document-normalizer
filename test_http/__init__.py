import logging
import json
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP トリガーテスト関数"""
    logging.info('Python HTTP trigger function processed a request.')
    
    # テスト用のレスポンスデータ
    response_data = {
        "status": "success",
        "message": "Document Normalizer is running!",
        "features": [
            "PDF document classification",
            "Azure Document Intelligence integration",
            "CDM schema mapping",
            "Data validation and entity resolution"
        ],
        "config_status": {
            "schemas": "✓ Loaded",
            "mappings": "✓ Loaded", 
            "validation_rules": "✓ Loaded",
            "vendor_patterns": "✓ Loaded"
        }
    }
    
    return func.HttpResponse(
        json.dumps(response_data, ensure_ascii=False, indent=2),
        status_code=200,
        headers={"Content-Type": "application/json; charset=utf-8"}
    )