import logging
from typing import Tuple, Dict, Any, Optional
from .classify import classify_document
from .extract_azure_docint import extract_with_document_intelligence
from .map_to_cdm import map_to_cdm
from .validate_er import validate_and_resolve
from .config_loader import ConfigLoader

logger = logging.getLogger(__name__)

def run_pipeline(blob_name: str, pdf_bytes: bytes) -> Tuple[bool, Optional[Dict], Dict, Dict]:
    """
    PDF処理パイプライン
    
    Args:
        blob_name: 処理対象のBLOB名
        pdf_bytes: PDFファイルのバイトデータ
        
    Returns:
        (成功フラグ, CDMデータ, 検証レポート, 生抽出データ)
    """
    logger.info(f"Starting pipeline for {blob_name}")
    
    validation_report = {
        "blob_name": blob_name,
        "errors": [],
        "warnings": [],
        "info": []
    }
    
    try:
        config_loader = ConfigLoader()
        
        logger.info("Step 1: Classifying document")
        doc_type, vendor_name, confidence = classify_document(pdf_bytes, config_loader)
        validation_report["info"].append({
            "step": "classification",
            "doc_type": doc_type,
            "vendor": vendor_name,
            "confidence": confidence
        })
        
        if not doc_type:
            validation_report["errors"].append("Failed to classify document type")
            return False, None, validation_report, {}
        
        logger.info(f"Document classified as {doc_type} from {vendor_name or 'unknown vendor'}")
        
        logger.info("Step 2: Extracting with Document Intelligence")
        raw_extraction = extract_with_document_intelligence(
            pdf_bytes=pdf_bytes,
            doc_type=doc_type
        )
        
        if not raw_extraction:
            validation_report["errors"].append("Failed to extract data from document")
            return False, None, validation_report, {}
        
        logger.info("Step 3: Mapping to CDM")
        cdm_data = map_to_cdm(
            raw_data=raw_extraction,
            doc_type=doc_type,
            vendor_name=vendor_name,
            config_loader=config_loader
        )
        
        if not cdm_data:
            validation_report["errors"].append("Failed to map data to CDM schema")
            return False, None, validation_report, raw_extraction
        
        logger.info("Step 4: Validating and resolving entities")
        is_valid, resolved_data, validation_errors = validate_and_resolve(
            cdm_data=cdm_data,
            doc_type=doc_type,
            config_loader=config_loader
        )
        
        if validation_errors:
            validation_report["errors"].extend(validation_errors)
        
        if is_valid:
            logger.info("Pipeline completed successfully")
            return True, resolved_data, validation_report, raw_extraction
        else:
            logger.warning("Document validation failed")
            return False, cdm_data, validation_report, raw_extraction
            
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}", exc_info=True)
        validation_report["errors"].append(f"Pipeline error: {str(e)}")
        return False, None, validation_report, {}