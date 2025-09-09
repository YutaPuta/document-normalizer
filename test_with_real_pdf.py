#!/usr/bin/env python3
"""
実際のPDFファイルを使ったローカルテスト
Azure Document Intelligenceなしでpdfminer.sixによるテキスト抽出テスト
"""

import sys
import json
from pathlib import Path

# プロジェクトのルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

from classify import classify_document
from map_to_cdm import map_to_cdm
from config_loader import ConfigLoader
import transforms

# PDFテキスト抽出機能を直接実装
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
from io import BytesIO

def extract_pdf_text_local(pdf_bytes):
    """PDFからテキストを抽出（ローカル実装）"""
    try:
        text = extract_text(
            BytesIO(pdf_bytes),
            laparams=LAParams(detect_vertical=True, word_margin=0.1, char_margin=2.0)
        )
        return text.strip()
    except Exception as e:
        raise Exception(f"PDF text extraction failed: {e}")

def test_real_pdf_processing(pdf_path):
    """実PDFファイルの処理テスト"""
    print(f"=== 実PDFファイル処理テスト: {pdf_path} ===\n")
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"❌ PDFファイルが見つかりません: {pdf_path}")
        return False
    
    validation_report = {
        "pdf_file": str(pdf_file.name),
        "errors": [],
        "warnings": [],
        "info": []
    }
    
    try:
        # 1. PDFファイル読み込み
        print("1. PDFファイル読み込み...")
        with open(pdf_file, 'rb') as f:
            pdf_bytes = f.read()
        
        print(f"   ファイルサイズ: {len(pdf_bytes):,} bytes")
        validation_report["info"].append({
            "step": "pdf_load",
            "file_size": len(pdf_bytes)
        })
        
        # 2. PDFテキスト抽出
        print("\n2. PDFテキスト抽出...")
        try:
            extracted_text = extract_pdf_text_local(pdf_bytes)
            print(f"   抽出文字数: {len(extracted_text)}")
            print(f"   テキスト例 (先頭200文字):")
            print(f"   {extracted_text[:200]}...")
            
            validation_report["info"].append({
                "step": "text_extraction",
                "text_length": len(extracted_text),
                "extraction_method": "pdfminer.six"
            })
            
        except Exception as e:
            print(f"   ❌ テキスト抽出エラー: {e}")
            validation_report["errors"].append(f"テキスト抽出エラー: {e}")
            return False, None, validation_report
        
        # 3. 文書分類
        print("\n3. 文書分類...")
        config = ConfigLoader()
        doc_type, vendor_name, doc_confidence = classify_document(pdf_bytes, config)
        vendor_confidence = doc_confidence  # 同じ信頼度を使用
        
        print(f"   文書種別: {doc_type} (信頼度: {doc_confidence:.2f})")
        print(f"   ベンダー: {vendor_name} (信頼度: {vendor_confidence:.2f})")
        
        validation_report["info"].append({
            "step": "classification",
            "doc_type": doc_type,
            "doc_confidence": doc_confidence,
            "vendor": vendor_name,
            "vendor_confidence": vendor_confidence
        })
        
        # 4. フィールド抽出（テキストベース）
        print("\n4. テキストベース フィールド抽出...")
        raw_extraction = extract_fields_from_text(extracted_text)
        
        print(f"   抽出フィールド数: {len(raw_extraction)}")
        for field, value in list(raw_extraction.items())[:5]:
            print(f"   {field}: {value}")
        if len(raw_extraction) > 5:
            print(f"   ... 他 {len(raw_extraction) - 5} フィールド")
        
        # 5. CDMマッピング
        print("\n5. CDMマッピング...")
        
        try:
            cdm_data = map_to_cdm(
                raw_data=raw_extraction,
                doc_type=doc_type,
                vendor_name=vendor_name,
                config=config
            )
            
            print(f"   CDMマッピング成功")
            print(f"   文書情報: {cdm_data.get('doc', {}).get('type', 'N/A')}")
            print(f"   明細行数: {len(cdm_data.get('lines', []))}")
            if 'totals' in cdm_data:
                grand_total = cdm_data['totals'].get('grand_total', 0)
                print(f"   合計金額: ¥{grand_total:,}")
            
        except Exception as e:
            print(f"   ⚠️ CDMマッピングエラー: {e}")
            validation_report["errors"].append(f"CDMマッピングエラー: {e}")
            # 基本CDMデータを作成
            cdm_data = create_minimal_cdm(raw_extraction, doc_type, vendor_name)
        
        # 6. 結果出力
        print("\n6. 処理結果:")
        print(json.dumps(cdm_data, ensure_ascii=False, indent=2))
        
        return True, cdm_data, validation_report
        
    except Exception as e:
        print(f"❌ 処理エラー: {e}")
        import traceback
        traceback.print_exc()
        validation_report["errors"].append(f"処理エラー: {e}")
        return False, None, validation_report

def extract_fields_from_text(text):
    """テキストから基本フィールドを抽出"""
    import re
    
    fields = {}
    
    # 請求書番号
    patterns = [
        r"請求(?:書)?番号[\s:：]*([A-Z0-9\-]+)",
        r"Invoice\s*(?:No|Number)[\s:：]*([A-Z0-9\-]+)",
        r"(?:No|NO)[\s.:：]*([A-Z0-9\-]{5,})"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields["invoice_number"] = match.group(1).strip()
            break
    
    # 発行日
    date_patterns = [
        r"発行日[\s:：]*([^\n\r]+)",
        r"(?:令和|平成)(\d+)年(\d+)月(\d+)日",
        r"(\d{4})年(\d{1,2})月(\d{1,2})日",
        r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})"
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            fields["issue_date_raw"] = match.group(0).strip()
            break
    
    # 合計金額
    amount_patterns = [
        r"合計(?:金額)?[\s:：]*[￥¥]?([0-9,]+)円?",
        r"(?:Total|TOTAL)[\s:：]*[￥¥]?([0-9,]+)",
        r"([0-9,]+)円?\s*(?:税込|込み|total)"
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields["total_amount_raw"] = match.group(1).replace(",", "")
            break
    
    # 会社名（ベンダー）
    company_patterns = [
        r"((?:株式会社|有限会社|合同会社|合名会社|合資会社)[^\n\r]{1,30})",
        r"([^\n\r]{1,30}(?:株式会社|有限会社|㈱|㈲))",
        r"([A-Z][A-Za-z\s&,.-]{5,30}(?:Inc|LLC|Corp|Co\.|Ltd))"
    ]
    
    for pattern in company_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # 最初に見つかった会社名を使用
            fields["vendor_name"] = matches[0].strip()
            break
    
    # 住所
    address_match = re.search(r"(〒?\d{3}-?\d{4}\s*[^\n\r]{5,50})", text)
    if address_match:
        fields["address"] = address_match.group(1).strip()
    
    # 電話番号
    phone_match = re.search(r"(?:TEL|電話)[\s:：]*([0-9\-\(\)]{10,15})", text, re.IGNORECASE)
    if phone_match:
        fields["phone"] = phone_match.group(1).strip()
    
    return fields

def create_minimal_cdm(raw_data, doc_type, vendor_name):
    """最小限のCDMデータを作成"""
    from datetime import datetime
    
    cdm_data = {
        "doc": {
            "type": doc_type or "UNKNOWN",
            "schema_version": "1.0",
            "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
            "vendor": vendor_name or "不明"
        },
        "lines": [],
        "totals": {},
        "metadata": {
            "confidence_scores": {},
            "unmapped_fields": list(raw_data.keys())
        }
    }
    
    # 基本フィールドのマッピング
    if "invoice_number" in raw_data:
        cdm_data["doc"]["document_no"] = raw_data["invoice_number"]
    
    if "issue_date_raw" in raw_data:
        cdm_data["doc"]["issue_date_raw"] = raw_data["issue_date_raw"]
        # 簡易日付変換
        try:
            if "令和" in raw_data["issue_date_raw"]:
                cdm_data["doc"]["issue_date"] = transforms.parse_japanese_date(raw_data["issue_date_raw"])
        except:
            pass
    
    if "total_amount_raw" in raw_data:
        try:
            amount = int(raw_data["total_amount_raw"].replace(",", ""))
            cdm_data["totals"]["grand_total"] = amount
            cdm_data["doc"]["currency"] = "JPY"
        except:
            pass
    
    return cdm_data

def test_sample_pdf_creation():
    """サンプルPDFファイルの作成支援"""
    print("\n=== サンプルPDF作成支援 ===\n")
    
    sample_content = """
請求書サンプル作成のヒント:

1. 簡単なテキストファイルから始める:
   - テキストエディタで invoice_sample.txt を作成
   - 以下の内容を含める:
     • 請求書
     • 請求番号: INV-2024-001
     • 発行日: 令和6年1月15日
     • 株式会社サンプル
     • 合計: 50,000円

2. オンライン変換ツールでPDF化:
   - https://www.ilovepdf.com/txt_to_pdf
   - https://smallpdf.com/txt-to-pdf
   - Googleドキュメント経由でPDF書き出し

3. 既存の請求書PDFを使用:
   - 個人情報を除去した請求書
   - ダミー請求書を作成

作成したPDFを同じディレクトリに配置してテスト実行してください。
"""
    print(sample_content)

if __name__ == "__main__":
    print("Document Normalizer - 実PDF処理テスト\n")
    
    # PDFファイルパスの確認
    sample_paths = [
        "sample_invoice.pdf",
        "test_invoice.pdf", 
        "invoice.pdf",
        "請求書.pdf"
    ]
    
    found_pdf = None
    for pdf_path in sample_paths:
        if Path(pdf_path).exists():
            found_pdf = pdf_path
            break
    
    if found_pdf:
        print(f"PDFファイルが見つかりました: {found_pdf}")
        success, cdm_data, report = test_real_pdf_processing(found_pdf)
        
        print(f"\n=== テスト結果 ===")
        print(f"処理成功: {'✅' if success else '❌'}")
        print(f"エラー数: {len(report.get('errors', []))}")
        print(f"警告数: {len(report.get('warnings', []))}")
        
        if report.get("errors"):
            print(f"\nエラー詳細:")
            for error in report["errors"]:
                print(f"  • {error}")
    
    else:
        print("テスト用PDFファイルが見つかりません。")
        test_sample_pdf_creation()
        print(f"\n手動テスト方法:")
        print(f"python test_with_real_pdf.py")
        print(f"または、PDFファイルパスを指定:")
        print(f"python -c \"from test_with_real_pdf import test_real_pdf_processing; test_real_pdf_processing('your_file.pdf')\"")