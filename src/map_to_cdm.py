import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from .transforms import apply_transforms

logger = logging.getLogger(__name__)

def map_to_cdm(
    raw_data: Dict[str, Any],
    doc_type: str,
    vendor_name: Optional[str],
    config_loader
) -> Optional[Dict[str, Any]]:
    """
    抽出データをCDMスキーマにマッピング
    
    Args:
        raw_data: Document Intelligenceから抽出された生データ
        doc_type: 文書種別
        vendor_name: ベンダー名
        config_loader: 設定ローダー
        
    Returns:
        CDM形式のデータ
    """
    try:
        mapping_config = config_loader.get_mapping_config(doc_type, vendor_name)
        
        if not mapping_config:
            logger.warning(f"No mapping config found for {doc_type}/{vendor_name}")
            mapping_config = config_loader.get_mapping_config(doc_type, None)
        
        cdm_data = {
            "doc": {
                "type": doc_type,
                "schema_version": "1.0",
                "extraction_timestamp": datetime.utcnow().isoformat(),
                "vendor": vendor_name
            },
            "lines": [],
            "totals": {},
            "metadata": {
                "confidence_scores": raw_data.get("confidence_scores", {}),
                "unmapped_fields": []
            }
        }
        
        cdm_data["doc"].update(map_document_fields(raw_data, mapping_config))
        
        cdm_data["lines"] = extract_line_items(raw_data, mapping_config)
        
        cdm_data["totals"] = extract_totals(raw_data, mapping_config)
        
        apply_post_compute(cdm_data, mapping_config)
        
        identify_unmapped_fields(raw_data, cdm_data, mapping_config)
        
        logger.info(f"Mapped {len(cdm_data['doc'])} doc fields, {len(cdm_data['lines'])} line items")
        return cdm_data
        
    except Exception as e:
        logger.error(f"Mapping error: {str(e)}", exc_info=True)
        return None

def map_document_fields(raw_data: Dict, mapping_config: Dict) -> Dict[str, Any]:
    """ドキュメントレベルのフィールドをマッピング"""
    mapped_fields = {}
    mappings = mapping_config.get("mappings", {})
    
    fields_data = raw_data.get("fields", {})
    kv_pairs = raw_data.get("key_value_pairs", {})
    
    all_source_data = {**fields_data, **kv_pairs}
    
    for target_field, mapping in mappings.items():
        if target_field == "lines":
            continue
            
        source_fields = mapping.get("from", [])
        transforms = mapping.get("transform", [])
        default_value = mapping.get("default")
        
        value = find_value_from_sources(all_source_data, source_fields)
        
        if value is not None:
            value = apply_transforms(value, transforms)
            mapped_fields[target_field] = value
        elif default_value is not None:
            mapped_fields[target_field] = default_value
    
    return mapped_fields

def find_value_from_sources(source_data: Dict, source_fields: List[str]) -> Optional[Any]:
    """ソースフィールドリストから値を探す"""
    for field_name in source_fields:
        for key, value in source_data.items():
            if normalize_field_name(key) == normalize_field_name(field_name):
                return value
            
            if field_name.lower() in key.lower():
                return value
    
    return None

def normalize_field_name(field_name: str) -> str:
    """フィールド名を正規化"""
    normalized = field_name.lower()
    normalized = re.sub(r"[　\s]+", "", normalized)
    normalized = re.sub(r"[（）()【】\[\]「」]", "", normalized)
    return normalized

def extract_line_items(raw_data: Dict, mapping_config: Dict) -> List[Dict]:
    """明細行を抽出"""
    line_items = []
    lines_config = mapping_config.get("lines", {})
    
    if not lines_config:
        return []
    
    tables = raw_data.get("tables", [])
    if not tables:
        return []
    
    table_config = lines_config.get("table", {})
    headers_mapping = table_config.get("headers", {})
    defaults = table_config.get("defaults", {})
    
    for table in tables:
        rows = table.get("rows", [])
        if len(rows) < 2:
            continue
        
        header_row = rows[0]
        header_map = map_headers(header_row, headers_mapping)
        
        for row in rows[1:]:
            if is_data_row(row):
                line_item = extract_line_item(row, header_map, defaults)
                if line_item:
                    line_items.append(line_item)
    
    return line_items

def map_headers(header_row: List[str], headers_mapping: Dict) -> Dict[int, str]:
    """ヘッダー行をマッピング"""
    header_map = {}
    
    for idx, header in enumerate(header_row):
        normalized_header = normalize_field_name(header)
        
        for target_field, source_headers in headers_mapping.items():
            for source_header in source_headers:
                if normalize_field_name(source_header) == normalized_header:
                    header_map[idx] = target_field
                    break
    
    return header_map

def is_data_row(row: List[str]) -> bool:
    """データ行かどうか判定"""
    non_empty = [cell for cell in row if cell and cell.strip()]
    return len(non_empty) >= 2

def extract_line_item(row: List[str], header_map: Dict[int, str], defaults: Dict) -> Optional[Dict]:
    """1行分のデータを抽出"""
    line_item = {}
    
    for idx, value in enumerate(row):
        if idx in header_map and value:
            field_name = header_map[idx]
            
            if field_name in ["qty", "unit_price", "amount"]:
                try:
                    cleaned_value = re.sub(r"[,￥¥$]", "", value)
                    line_item[field_name] = float(cleaned_value)
                except ValueError:
                    line_item[field_name] = value
            else:
                line_item[field_name] = value
    
    for key, default_value in defaults.items():
        if key not in line_item:
            line_item[key] = default_value
    
    return line_item if line_item else None

def extract_totals(raw_data: Dict, mapping_config: Dict) -> Dict[str, Any]:
    """合計金額関連を抽出"""
    totals = {}
    
    total_fields = {
        "subtotal": ["小計", "税抜金額", "subtotal", "net_amount"],
        "tax": ["消費税", "税額", "tax", "vat"],
        "grand_total": ["合計", "総額", "合計金額", "total", "grand_total", "お支払金額"]
    }
    
    all_source_data = {**raw_data.get("fields", {}), **raw_data.get("key_value_pairs", {})}
    
    for target_field, source_fields in total_fields.items():
        value = find_value_from_sources(all_source_data, source_fields)
        if value is not None:
            try:
                cleaned_value = re.sub(r"[,￥¥$]", "", str(value))
                totals[target_field] = float(cleaned_value)
            except ValueError:
                pass
    
    return totals

def apply_post_compute(cdm_data: Dict, mapping_config: Dict):
    """後処理計算を適用"""
    post_compute = mapping_config.get("post_compute", [])
    
    for computation in post_compute:
        try:
            local_vars = {
                "doc": cdm_data.get("doc", {}),
                "lines": cdm_data.get("lines", []),
                "totals": cdm_data.get("totals", {}),
                "round": round
            }
            
            exec(computation, {"__builtins__": {}}, local_vars)
            
            cdm_data["totals"] = local_vars["totals"]
            
        except Exception as e:
            logger.warning(f"Post-compute error: {str(e)}")

def identify_unmapped_fields(raw_data: Dict, cdm_data: Dict, mapping_config: Dict):
    """マッピングされなかったフィールドを記録"""
    all_raw_fields = set()
    all_raw_fields.update(raw_data.get("fields", {}).keys())
    all_raw_fields.update(raw_data.get("key_value_pairs", {}).keys())
    
    mapped_fields = set()
    for mapping in mapping_config.get("mappings", {}).values():
        if isinstance(mapping, dict):
            mapped_fields.update(mapping.get("from", []))
    
    unmapped = []
    for field in all_raw_fields:
        is_mapped = False
        for mapped_field in mapped_fields:
            if normalize_field_name(field) == normalize_field_name(mapped_field):
                is_mapped = True
                break
        
        if not is_mapped:
            value = raw_data.get("fields", {}).get(field) or raw_data.get("key_value_pairs", {}).get(field)
            if value:
                unmapped.append({
                    "field": field,
                    "value": str(value)[:100],
                    "source": "fields" if field in raw_data.get("fields", {}) else "key_value_pairs"
                })
    
    if unmapped:
        cdm_data["metadata"]["unmapped_fields"] = unmapped
        logger.info(f"Found {len(unmapped)} unmapped fields")