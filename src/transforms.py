import logging
import re
from typing import Any, List, Union
from datetime import datetime
from dateutil import parser

logger = logging.getLogger(__name__)

def apply_transforms(value: Any, transforms: List[str]) -> Any:
    """
    値に対して一連の変換を適用
    
    Args:
        value: 変換対象の値
        transforms: 適用する変換のリスト
        
    Returns:
        変換後の値
    """
    if value is None:
        return None
    
    result = value
    
    for transform in transforms:
        try:
            if ":" in transform:
                transform_name, param = transform.split(":", 1)
                result = apply_single_transform(result, transform_name, param)
            else:
                result = apply_single_transform(result, transform, None)
        except Exception as e:
            logger.warning(f"Transform '{transform}' failed for value '{value}': {str(e)}")
    
    return result

def apply_single_transform(value: Any, transform_name: str, param: Any = None) -> Any:
    """単一の変換を適用"""
    
    transform_map = {
        "trim": lambda v, p: str(v).strip(),
        "upper": lambda v, p: str(v).upper(),
        "lower": lambda v, p: str(v).lower(),
        "strip_currency": strip_currency,
        "to_decimal": lambda v, p: to_decimal(v, int(p) if p else 2),
        "to_date": lambda v, p: to_date(v, p),
        "normalize_japanese": normalize_japanese,
        "extract_number": extract_number,
        "remove_spaces": lambda v, p: re.sub(r"\s+", "", str(v)),
        "zenkaku_to_hankaku": zenkaku_to_hankaku,
        "hankaku_to_zenkaku": hankaku_to_zenkaku,
        "parse_japanese_date": parse_japanese_date,
        "normalize_phone": normalize_phone,
        "normalize_postal_code": normalize_postal_code,
        "split": lambda v, p: str(v).split(p if p else ","),
        "join": lambda v, p: (p if p else ",").join(v) if isinstance(v, list) else str(v),
        "replace": lambda v, p: apply_replace(v, p),
        "regex": lambda v, p: apply_regex(v, p),
        "default": lambda v, p: v if v else p,
        "round": lambda v, p: round(float(v), int(p) if p else 0),
        "abs": lambda v, p: abs(float(v)),
        "multiply": lambda v, p: float(v) * float(p),
        "divide": lambda v, p: float(v) / float(p) if float(p) != 0 else None
    }
    
    if transform_name in transform_map:
        return transform_map[transform_name](value, param)
    else:
        logger.warning(f"Unknown transform: {transform_name}")
        return value

def strip_currency(value: str, param: Any = None) -> str:
    """通貨記号を除去"""
    value = str(value)
    
    currency_symbols = ["¥", "￥", "$", "€", "£", "円", "yen", "jpy", "USD", "EUR", "GBP"]
    
    for symbol in currency_symbols:
        value = value.replace(symbol, "")
    
    value = re.sub(r"[,，、]", "", value)
    
    value = value.strip()
    
    return value

def to_decimal(value: Any, precision: int = 2) -> float:
    """小数に変換"""
    try:
        value = strip_currency(str(value))
        
        value = re.sub(r"[^\d.-]", "", value)
        
        result = float(value)
        
        if precision >= 0:
            result = round(result, precision)
        
        return result
    except (ValueError, TypeError):
        return 0.0

def to_date(value: str, format_str: str = None) -> str:
    """日付形式に変換"""
    try:
        if not value:
            return None
        
        value = str(value).strip()
        
        if format_str:
            dt = datetime.strptime(value, format_str)
        else:
            dt = parser.parse(value, fuzzy=True)
        
        return dt.strftime("%Y-%m-%d")
        
    except Exception as e:
        parsed = parse_japanese_date(value)
        if parsed:
            return parsed
        
        logger.warning(f"Date parsing failed for '{value}': {str(e)}")
        return value

def normalize_japanese(value: str, param: Any = None) -> str:
    """日本語テキストを正規化"""
    value = str(value)
    
    value = re.sub(r"[　]+", " ", value)
    
    value = zenkaku_to_hankaku(value, alphanumeric_only=True)
    
    value = re.sub(r"\s+", " ", value)
    
    return value.strip()

def extract_number(value: str, param: Any = None) -> str:
    """数値部分を抽出"""
    value = str(value)
    
    value = zenkaku_to_hankaku(value)
    
    numbers = re.findall(r"[\d,.-]+", value)
    
    if numbers:
        return numbers[0].replace(",", "")
    
    return ""

def zenkaku_to_hankaku(value: str, alphanumeric_only: bool = False) -> str:
    """全角を半角に変換"""
    value = str(value)
    
    zenkaku_nums = "０１２３４５６７８９"
    hankaku_nums = "0123456789"
    
    zenkaku_alpha_upper = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
    hankaku_alpha_upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    zenkaku_alpha_lower = "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
    hankaku_alpha_lower = "abcdefghijklmnopqrstuvwxyz"
    
    trans = str.maketrans(
        zenkaku_nums + zenkaku_alpha_upper + zenkaku_alpha_lower,
        hankaku_nums + hankaku_alpha_upper + hankaku_alpha_lower
    )
    
    if not alphanumeric_only:
        zenkaku_symbols = "　！＂＃＄％＆＇（）＊＋，－．／：；＜＝＞？＠［￥］＾＿｀｛｜｝～"
        hankaku_symbols = " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
        
        trans.update(str.maketrans(zenkaku_symbols, hankaku_symbols))
    
    return value.translate(trans)

def hankaku_to_zenkaku(value: str, param: Any = None) -> str:
    """半角を全角に変換"""
    value = str(value)
    
    hankaku_nums = "0123456789"
    zenkaku_nums = "０１２３４５６７８９"
    
    hankaku_alpha_upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    zenkaku_alpha_upper = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
    
    hankaku_alpha_lower = "abcdefghijklmnopqrstuvwxyz"
    zenkaku_alpha_lower = "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
    
    trans = str.maketrans(
        hankaku_nums + hankaku_alpha_upper + hankaku_alpha_lower,
        zenkaku_nums + zenkaku_alpha_upper + zenkaku_alpha_lower
    )
    
    return value.translate(trans)

def parse_japanese_date(value: str) -> str:
    """日本語の日付表記を解析"""
    value = str(value).strip()
    
    era_map = {
        "令和": 2018,
        "平成": 1988,
        "昭和": 1925,
        "大正": 1911,
        "明治": 1867
    }
    
    for era, base_year in era_map.items():
        pattern = rf"{era}(\d+)年(\d+)月(\d+)日"
        match = re.search(pattern, value)
        if match:
            era_year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            year = base_year + era_year
            return f"{year:04d}-{month:02d}-{day:02d}"
    
    pattern = r"(\d{4})年(\d{1,2})月(\d{1,2})日"
    match = re.search(pattern, value)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        return f"{year:04d}-{month:02d}-{day:02d}"
    
    pattern = r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})"
    match = re.search(pattern, value)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        return f"{year:04d}-{month:02d}-{day:02d}"
    
    return None

def normalize_phone(value: str, param: Any = None) -> str:
    """電話番号を正規化"""
    value = str(value).strip()
    
    value = zenkaku_to_hankaku(value)
    
    value = re.sub(r"[^\d+-]", "", value)
    
    value = re.sub(r"[-\s]+", "-", value)
    
    return value

def normalize_postal_code(value: str, param: Any = None) -> str:
    """郵便番号を正規化"""
    value = str(value).strip()
    
    value = zenkaku_to_hankaku(value)
    
    value = re.sub(r"[^\d-]", "", value)
    
    if re.match(r"^\d{7}$", value):
        value = f"{value[:3]}-{value[3:]}"
    
    return value

def apply_replace(value: str, param: str) -> str:
    """文字列置換を適用"""
    if not param or "|" not in param:
        return value
    
    old, new = param.split("|", 1)
    return str(value).replace(old, new)

def apply_regex(value: str, param: str) -> str:
    """正規表現を適用"""
    if not param:
        return value
    
    try:
        match = re.search(param, str(value))
        if match:
            if match.groups():
                return match.group(1)
            else:
                return match.group(0)
    except Exception as e:
        logger.warning(f"Regex failed: {str(e)}")
    
    return value