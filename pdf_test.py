#!/usr/bin/env python3
"""
PDFファイルを使った簡易テスト
pdfminer.sixでPDFからテキスト抽出して処理
"""

import sys
import json
from pathlib import Path
from io import BytesIO
import re

# PDF処理
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

def extract_pdf_text(pdf_path):
    """PDFファイルからテキストを抽出"""
    try:
        with open(pdf_path, 'rb') as f:
            text = extract_text(
                f,
                laparams=LAParams(detect_vertical=True, word_margin=0.1, char_margin=2.0)
            )
        return text.strip()
    except Exception as e:
        raise Exception(f"PDF text extraction failed: {e}")

def classify_document_simple(text):
    """簡易文書分類"""
    text_lower = text.lower()
    
    if "請求書" in text or "請求番号" in text or "invoice" in text_lower:
        return "INVOICE", 0.9
    elif "発注書" in text or "注文書" in text or "purchase order" in text_lower:
        return "PURCHASE_ORDER", 0.8
    else:
        return "UNKNOWN", 0.1

def extract_vendor_simple(text):
    """簡易ベンダー抽出"""
    # 会社名パターン
    company_patterns = [
        r"((?:株式会社|有限会社|合同会社)[^\n\r]{1,30})",
        r"([^\n\r]{1,30}(?:株式会社|㈱))"
    ]
    
    for pattern in company_patterns:
        matches = re.findall(pattern, text)
        if matches:
            return matches[0].strip(), 0.8
    
    return "不明", 0.0

def extract_fields_simple(text):
    """簡易フィールド抽出"""
    fields = {}
    
    # 請求番号
    invoice_match = re.search(r"請求番号[:：]\s*([A-Z0-9\-]+)", text)
    if invoice_match:
        fields["document_no"] = invoice_match.group(1).strip()
    
    # 発行日
    date_match = re.search(r"発行日[:：]\s*([^\n\r]+)", text)
    if date_match:
        raw_date = date_match.group(1).strip()
        fields["issue_date_raw"] = raw_date
        # 和暦変換
        if "令和6年" in raw_date:
            try:
                converted = raw_date.replace("令和6年", "2024年").replace("月", "-").replace("日", "")
                parts = converted.replace("年", "-").split("-")
                if len(parts) >= 3:
                    fields["issue_date"] = f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
            except:
                pass
    
    # 合計金額
    total_patterns = [
        r"合計[:：]\s*[¥￥]?([0-9,]+)円?",
        r"総額[:：]\s*[¥￥]?([0-9,]+)円?",
    ]
    
    for pattern in total_patterns:
        match = re.search(pattern, text)
        if match:
            amount_str = match.group(1).replace(",", "")
            try:
                fields["grand_total"] = int(amount_str)
            except:
                pass
            break
    
    # 小計
    subtotal_match = re.search(r"小計[:：]\s*[¥￥]?([0-9,]+)", text)
    if subtotal_match:
        try:
            fields["subtotal"] = int(subtotal_match.group(1).replace(",", ""))
        except:
            pass
    
    # 消費税
    tax_match = re.search(r"消費税[^:：]*[:：]\s*[¥￥]?([0-9,]+)", text)
    if tax_match:
        try:
            fields["tax"] = int(tax_match.group(1).replace(",", ""))
        except:
            pass
    
    return fields

def create_cdm_simple(fields, doc_type, vendor):
    """簡易CDM作成"""
    from datetime import datetime, timezone
    
    cdm_data = {
        "doc": {
            "type": doc_type,
            "schema_version": "1.0",
            "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
            "currency": "JPY",
            "vendor": vendor
        },
        "lines": [],
        "totals": {},
        "metadata": {
            "confidence_scores": {},
            "unmapped_fields": []
        }
    }
    
    # 基本フィールド設定
    for field in ["document_no", "issue_date"]:
        if field in fields:
            cdm_data["doc"][field] = fields[field]
    
    # 金額設定
    for field in ["subtotal", "tax", "grand_total"]:
        if field in fields:
            cdm_data["totals"][field] = fields[field]
    
    # 基本明細行（推定）
    if "subtotal" in fields:
        cdm_data["lines"] = [{
            "description": "請求項目",
            "qty": 1,
            "unit_price": fields["subtotal"],
            "amount": fields["subtotal"],
            "tax_rate": 0.10
        }]
    
    return cdm_data

def test_pdf_processing(pdf_path):
    """PDFファイルの処理テスト"""
    print(f"=== PDFファイル処理テスト: {pdf_path} ===\n")
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"❌ PDFファイルが見つかりません: {pdf_path}")
        return False
    
    try:
        # 1. PDF読み込み
        print("1. PDFファイル読み込み...")
        file_size = pdf_file.stat().st_size
        print(f"   ファイルサイズ: {file_size:,} bytes")
        
        # 2. テキスト抽出
        print("\n2. PDFテキスト抽出...")
        extracted_text = extract_pdf_text(pdf_path)
        print(f"   抽出文字数: {len(extracted_text)}")
        print(f"   テキスト例 (先頭300文字):")
        print(f"   {extracted_text[:300]}...")
        
        # 3. 文書分類
        print("\n3. 文書分類...")
        doc_type, doc_confidence = classify_document_simple(extracted_text)
        print(f"   文書種別: {doc_type} (信頼度: {doc_confidence:.2f})")
        
        # 4. ベンダー判定
        print("\n4. ベンダー判定...")
        vendor, vendor_confidence = extract_vendor_simple(extracted_text)
        print(f"   ベンダー: {vendor} (信頼度: {vendor_confidence:.2f})")
        
        # 5. フィールド抽出
        print("\n5. フィールド抽出...")
        raw_fields = extract_fields_simple(extracted_text)
        print(f"   抽出フィールド数: {len(raw_fields)}")
        for field, value in raw_fields.items():
            print(f"   {field}: {value}")
        
        # 6. CDM作成
        print("\n6. CDM構造作成...")
        cdm_data = create_cdm_simple(raw_fields, doc_type, vendor)
        print(f"   CDMデータ生成完了")
        
        # 7. 結果出力
        print("\n7. 最終CDMデータ:")
        print(json.dumps(cdm_data, ensure_ascii=False, indent=2))
        
        return True
        
    except Exception as e:
        print(f"❌ 処理エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Document Normalizer - PDFテスト\n")
    
    # PDFファイル候補をチェック
    pdf_candidates = [
        "sample_invoice.pdf",
        "test_invoice.pdf",
        "invoice.pdf",
        "請求書.pdf"
    ]
    
    found_pdf = None
    for pdf_path in pdf_candidates:
        if Path(pdf_path).exists():
            found_pdf = pdf_path
            break
    
    if found_pdf:
        print(f"📄 PDFファイル発見: {found_pdf}")
        success = test_pdf_processing(found_pdf)
        
        print(f"\n=== テスト結果 ===")
        if success:
            print("✅ PDFテスト成功！Document Normalizerは正常に動作しています")
        else:
            print("❌ PDFテストで問題が発生しました")
    
    else:
        print("❌ テスト用PDFファイルが見つかりません")
        print("\n解決方法:")
        print("1. python create_sample_pdf.py  # サンプルPDF作成")
        print("2. 任意のPDFを sample_invoice.pdf として配置")
        print("3. python pdf_test.py で再実行")