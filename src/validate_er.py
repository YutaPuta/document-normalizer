import logging
import re
from typing import Tuple, Dict, Any, List, Optional
from datetime import datetime
import jsonschema

logger = logging.getLogger(__name__)

def validate_and_resolve(
    cdm_data: Dict[str, Any],
    doc_type: str,
    config_loader
) -> Tuple[bool, Dict[str, Any], List[str]]:
    """
    CDMデータの検証とエンティティ解決
    
    Args:
        cdm_data: CDM形式のデータ
        doc_type: 文書種別
        config_loader: 設定ローダー
        
    Returns:
        (検証成功フラグ, 解決済みデータ, エラーリスト)
    """
    errors = []
    resolved_data = cdm_data.copy()
    
    try:
        schema = config_loader.get_cdm_schema(doc_type)
        if schema:
            schema_errors = validate_schema(resolved_data, schema)
            errors.extend(schema_errors)
        
        validation_rules = config_loader.get_validation_rules()
        
        business_errors = validate_business_rules(resolved_data, validation_rules)
        errors.extend(business_errors)
        
        resolved_data = resolve_entities(resolved_data, config_loader)
        
        duplicate_check = check_duplicates(resolved_data, config_loader)
        if duplicate_check:
            errors.append(f"Duplicate document detected: {duplicate_check}")
        
        format_errors = validate_formats(resolved_data)
        errors.extend(format_errors)
        
        is_valid = len(errors) == 0
        
        if errors:
            logger.warning(f"Validation errors: {errors}")
        else:
            logger.info("Validation passed successfully")
        
        return is_valid, resolved_data, errors
        
    except Exception as e:
        logger.error(f"Validation error: {str(e)}", exc_info=True)
        errors.append(f"Validation system error: {str(e)}")
        return False, cdm_data, errors

def validate_schema(data: Dict, schema: Dict) -> List[str]:
    """JSONスキーマ検証"""
    errors = []
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        errors.append(f"Schema validation: {e.message} at {'.'.join(str(p) for p in e.path)}")
    except jsonschema.SchemaError as e:
        errors.append(f"Schema error: {e.message}")
    
    return errors

def validate_business_rules(data: Dict, rules: Dict) -> List[str]:
    """ビジネスルール検証"""
    errors = []
    
    if "amount_checks" in rules:
        errors.extend(validate_amounts(data, rules["amount_checks"]))
    
    if "date_checks" in rules:
        errors.extend(validate_dates(data, rules["date_checks"]))
    
    if "required_fields" in rules:
        errors.extend(check_required_fields(data, rules["required_fields"]))
    
    if "field_constraints" in rules:
        errors.extend(validate_field_constraints(data, rules["field_constraints"]))
    
    return errors

def validate_amounts(data: Dict, amount_rules: Dict) -> List[str]:
    """金額計算の検証"""
    errors = []
    totals = data.get("totals", {})
    
    if amount_rules.get("check_tax_calculation", True):
        subtotal = totals.get("subtotal", 0)
        tax = totals.get("tax", 0)
        grand_total = totals.get("grand_total", 0)
        
        if subtotal and tax and grand_total:
            calculated_total = subtotal + tax
            tolerance = amount_rules.get("tolerance", 1.0)
            
            if abs(calculated_total - grand_total) > tolerance:
                errors.append(
                    f"Amount calculation mismatch: {subtotal} + {tax} = {calculated_total}, "
                    f"but grand_total is {grand_total}"
                )
    
    if amount_rules.get("check_line_totals", True):
        lines = data.get("lines", [])
        line_total = sum(
            line.get("amount", 0) for line in lines
            if isinstance(line.get("amount"), (int, float))
        )
        
        subtotal = totals.get("subtotal", 0)
        if line_total and subtotal:
            tolerance = amount_rules.get("line_tolerance", 10.0)
            if abs(line_total - subtotal) > tolerance:
                errors.append(
                    f"Line items total {line_total} doesn't match subtotal {subtotal}"
                )
    
    return errors

def validate_dates(data: Dict, date_rules: Dict) -> List[str]:
    """日付の検証"""
    errors = []
    doc = data.get("doc", {})
    
    issue_date_str = doc.get("issue_date")
    due_date_str = doc.get("due_date")
    
    if issue_date_str and due_date_str:
        try:
            issue_date = datetime.strptime(issue_date_str, "%Y-%m-%d")
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            
            if date_rules.get("due_after_issue", True):
                if due_date < issue_date:
                    errors.append(f"Due date {due_date_str} is before issue date {issue_date_str}")
            
            if "max_payment_terms" in date_rules:
                max_days = date_rules["max_payment_terms"]
                if (due_date - issue_date).days > max_days:
                    errors.append(f"Payment terms exceed {max_days} days")
                    
        except ValueError as e:
            errors.append(f"Invalid date format: {str(e)}")
    
    return errors

def check_required_fields(data: Dict, required_fields: Dict) -> List[str]:
    """必須フィールドのチェック"""
    errors = []
    
    for doc_type, fields in required_fields.items():
        if data.get("doc", {}).get("type") == doc_type:
            for field_path in fields:
                if not get_nested_value(data, field_path):
                    errors.append(f"Required field missing: {field_path}")
    
    return errors

def validate_field_constraints(data: Dict, constraints: Dict) -> List[str]:
    """フィールド制約の検証"""
    errors = []
    
    for field_path, constraint in constraints.items():
        value = get_nested_value(data, field_path)
        
        if value is not None:
            if "min_length" in constraint:
                if len(str(value)) < constraint["min_length"]:
                    errors.append(f"{field_path} is too short")
            
            if "max_length" in constraint:
                if len(str(value)) > constraint["max_length"]:
                    errors.append(f"{field_path} is too long")
            
            if "pattern" in constraint:
                if not re.match(constraint["pattern"], str(value)):
                    errors.append(f"{field_path} doesn't match required pattern")
            
            if "min_value" in constraint:
                if isinstance(value, (int, float)) and value < constraint["min_value"]:
                    errors.append(f"{field_path} is below minimum value")
            
            if "max_value" in constraint:
                if isinstance(value, (int, float)) and value > constraint["max_value"]:
                    errors.append(f"{field_path} exceeds maximum value")
    
    return errors

def resolve_entities(data: Dict, config_loader) -> Dict[str, Any]:
    """エンティティ解決（取引先マスタとの照合）"""
    resolved = data.copy()
    
    entity_dict = config_loader.get_entity_dictionary()
    if not entity_dict:
        return resolved
    
    doc = resolved.get("doc", {})
    vendor_name = doc.get("vendor")
    
    if vendor_name and vendor_name in entity_dict.get("vendors", {}):
        vendor_info = entity_dict["vendors"][vendor_name]
        doc["vendor_id"] = vendor_info.get("id")
        doc["vendor_normalized"] = vendor_info.get("normalized_name", vendor_name)
        
        if "additional_info" in vendor_info:
            doc["vendor_info"] = vendor_info["additional_info"]
    
    customer_ref = find_customer_reference(data)
    if customer_ref and customer_ref in entity_dict.get("customers", {}):
        customer_info = entity_dict["customers"][customer_ref]
        doc["customer_id"] = customer_info.get("id")
        doc["customer_normalized"] = customer_info.get("normalized_name", customer_ref)
    
    return resolved

def find_customer_reference(data: Dict) -> Optional[str]:
    """顧客参照を探す"""
    doc = data.get("doc", {})
    
    possible_fields = ["customer", "bill_to", "ship_to", "customer_name", "取引先", "得意先"]
    for field in possible_fields:
        if field in doc:
            return doc[field]
    
    return None

def check_duplicates(data: Dict, config_loader) -> Optional[str]:
    """重複チェック（簡易版）"""
    doc = data.get("doc", {})
    document_no = doc.get("document_no")
    vendor = doc.get("vendor")
    
    if not document_no or not vendor:
        return None
    
    duplicate_key = f"{vendor}:{document_no}"
    
    return None

def validate_formats(data: Dict) -> List[str]:
    """フォーマット検証"""
    errors = []
    doc = data.get("doc", {})
    
    if "currency" in doc:
        currency = doc["currency"]
        if not re.match(r"^[A-Z]{3}$", currency):
            errors.append(f"Invalid currency code: {currency}")
    
    if "document_no" in doc:
        doc_no = doc["document_no"]
        if len(doc_no) > 50:
            errors.append(f"Document number too long: {doc_no}")
    
    date_fields = ["issue_date", "due_date"]
    for field in date_fields:
        if field in doc:
            date_str = doc[field]
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
                errors.append(f"Invalid date format for {field}: {date_str}")
    
    return errors

def get_nested_value(data: Dict, path: str) -> Any:
    """ネストされた辞書から値を取得"""
    keys = path.split(".")
    value = data
    
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
    
    return value