import logging
import re
from typing import Tuple, Optional
from io import BytesIO
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

logger = logging.getLogger(__name__)

def classify_document(pdf_bytes: bytes, config_loader) -> Tuple[Optional[str], Optional[str], float]:
    """
    PDFから文書種別とベンダーを判定
    
    Args:
        pdf_bytes: PDFファイルのバイトデータ
        config_loader: 設定ローダー
        
    Returns:
        (文書種別, ベンダー名, 信頼度スコア)
    """
    try:
        text = extract_text(
            BytesIO(pdf_bytes),
            laparams=LAParams(detect_vertical=True)
        )
        
        text_lower = text.lower()
        text_normalized = normalize_japanese_text(text)
        
        doc_type = detect_document_type(text_lower, text_normalized)
        vendor_name = detect_vendor(text, config_loader)
        confidence = calculate_confidence(doc_type, vendor_name, text)
        
        logger.info(f"Classification result: type={doc_type}, vendor={vendor_name}, confidence={confidence}")
        return doc_type, vendor_name, confidence
        
    except Exception as e:
        logger.error(f"Classification error: {str(e)}", exc_info=True)
        return None, None, 0.0

def detect_document_type(text_lower: str, text_normalized: str) -> Optional[str]:
    """文書種別を判定"""
    invoice_keywords = [
        "請求書", "invoice", "bill", "請求番号", "請求金額",
        "お支払い", "payment", "支払期限", "振込先"
    ]
    
    po_keywords = [
        "発注書", "purchase order", "注文書", "発注番号", "注文番号",
        "納期", "delivery", "納品先", "発注金額"
    ]
    
    invoice_score = sum(1 for kw in invoice_keywords if kw in text_lower or kw in text_normalized)
    po_score = sum(1 for kw in po_keywords if kw in text_lower or kw in text_normalized)
    
    if invoice_score > po_score and invoice_score >= 2:
        return "INVOICE"
    elif po_score > invoice_score and po_score >= 2:
        return "PURCHASE_ORDER"
    
    return None

def detect_vendor(text: str, config_loader) -> Optional[str]:
    """ベンダーを判定"""
    try:
        vendor_config = config_loader.get_vendor_config()
        if not vendor_config:
            return None
        
        for vendor_name, patterns in vendor_config.items():
            for pattern_type, pattern_list in patterns.items():
                if pattern_type == "company_names":
                    for name in pattern_list:
                        if name in text:
                            return vendor_name
                            
                elif pattern_type == "phone_patterns":
                    for phone in pattern_list:
                        phone_regex = phone.replace("-", r"[\-\s]?")
                        if re.search(phone_regex, text):
                            return vendor_name
                            
                elif pattern_type == "domains":
                    for domain in pattern_list:
                        if domain in text:
                            return vendor_name
                            
                elif pattern_type == "addresses":
                    for addr in pattern_list:
                        if addr in text:
                            return vendor_name
        
        return extract_vendor_from_text(text)
        
    except Exception as e:
        logger.warning(f"Vendor detection error: {str(e)}")
        return None

def extract_vendor_from_text(text: str) -> Optional[str]:
    """テキストから直接ベンダー名を抽出する試み"""
    company_patterns = [
        r"(株式会社[\s　]*[\u4e00-\u9faf\u3040-\u309f\u30a0-\u30ff]+)",
        r"([\u4e00-\u9faf\u3040-\u309f\u30a0-\u30ff]+[\s　]*株式会社)",
        r"(合同会社[\s　]*[\u4e00-\u9faf\u3040-\u309f\u30a0-\u30ff]+)",
        r"(有限会社[\s　]*[\u4e00-\u9faf\u3040-\u309f\u30a0-\u30ff]+)"
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    
    return None

def normalize_japanese_text(text: str) -> str:
    """日本語テキストの正規化"""
    text = re.sub(r"[　\s]+", " ", text)
    
    fullwidth_to_halfwidth = str.maketrans(
        "０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ",
        "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    )
    text = text.translate(fullwidth_to_halfwidth)
    
    return text

def calculate_confidence(doc_type: Optional[str], vendor_name: Optional[str], text: str) -> float:
    """分類の信頼度スコアを計算"""
    score = 0.0
    
    if doc_type:
        score += 0.5
    
    if vendor_name:
        score += 0.3
    
    required_fields = ["金額", "日付", "番号"]
    found_fields = sum(1 for field in required_fields if field in text)
    score += (found_fields / len(required_fields)) * 0.2
    
    return min(score, 1.0)