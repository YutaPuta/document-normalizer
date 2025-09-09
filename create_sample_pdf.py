#!/usr/bin/env python3
"""
サンプルPDFファイルを作成するスクリプト
reportlabを使って簡単な請求書PDFを生成
"""

def create_sample_pdf():
    """サンプル請求書PDFを作成"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        
        # 日本語フォントを登録
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
        
        filename = "sample_invoice.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # フォントを設定
        c.setFont("HeiseiMin-W3", 16)
        
        # タイトル
        c.drawString(200, height - 80, "請求書")
        
        # 基本情報
        c.setFont("HeiseiMin-W3", 12)
        y_pos = height - 150
        
        invoice_lines = [
            "請求番号: INV-2024-TEST-001",
            "発行日: 令和6年1月15日",
            "支払期限: 令和6年2月15日",
            "",
            "株式会社サンプル",
            "〒100-0001 東京都千代田区千代田1-1-1",
            "TEL: 03-1234-5678",
            "",
            "請求先:",
            "株式会社クライアント",
            "",
            "品目: システム開発費用",
            "数量: 1式",
            "単価: ¥50,000",
            "金額: ¥50,000",
            "",
            "小計: ¥50,000",
            "消費税(10%): ¥5,000",
            "合計: ¥55,000",
            "",
            "お振込先: ××銀行 ××支店",
            "口座番号: 1234567"
        ]
        
        for line in invoice_lines:
            c.drawString(50, y_pos, line)
            y_pos -= 20
        
        c.save()
        print(f"✅ サンプルPDFを作成しました: {filename}")
        return filename
        
    except ImportError:
        print("❌ reportlabライブラリが必要です")
        print("インストール: pip install reportlab")
        return create_simple_text_pdf()

def create_simple_text_pdf():
    """reportlabが使えない場合の簡易PDF作成"""
    try:
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        
        # タイトル
        pdf.cell(0, 10, 'INVOICE / Seikyu-sho', ln=True, align='C')
        pdf.ln(10)
        
        # 請求書内容
        pdf.set_font('Arial', '', 12)
        invoice_content = [
            "Invoice No: INV-2024-TEST-001",
            "Date: Reiwa 6-nen 1-gatsu 15-nichi (2024-01-15)",
            "Due Date: Reiwa 6-nen 2-gatsu 15-nichi (2024-02-15)",
            "",
            "From: Sample Company Ltd.",
            "Address: 1-1-1 Chiyoda, Chiyoda-ku, Tokyo",
            "Phone: 03-1234-5678",
            "",
            "To: Client Company Ltd.",
            "",
            "Description: System Development Fee",
            "Quantity: 1",
            "Unit Price: 50,000 yen",
            "Amount: 50,000 yen",
            "",
            "Subtotal: 50,000 yen",
            "Tax (10%): 5,000 yen",
            "Total: 55,000 yen",
            "",
            "Payment: XX Bank, XX Branch",
            "Account: 1234567"
        ]
        
        for line in invoice_content:
            pdf.cell(0, 7, line, ln=True)
        
        filename = "sample_invoice_simple.pdf"
        pdf.output(filename)
        print(f"✅ 簡易PDFを作成しました: {filename}")
        return filename
        
    except ImportError:
        print("❌ fpdfライブラリも必要です")
        print("インストール: pip install fpdf2")
        return create_text_file()

def create_text_file():
    """PDFライブラリが使えない場合のテキストファイル作成"""
    filename = "sample_invoice.txt"
    content = """請求書

請求番号: INV-2024-TEST-001
発行日: 令和6年1月15日
支払期限: 令和6年2月15日

株式会社サンプル
〒100-0001 東京都千代田区千代田1-1-1
TEL: 03-1234-5678

請求先:
株式会社クライアント

品目: システム開発費用
数量: 1式
単価: ¥50,000
金額: ¥50,000

小計: ¥50,000
消費税(10%): ¥5,000
合計: ¥55,000

お振込先: ××銀行 ××支店
口座番号: 1234567"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ テキストファイルを作成しました: {filename}")
    print("このファイルをオンライン変換ツールでPDF化してください:")
    print("- https://www.ilovepdf.com/txt_to_pdf")
    print("- https://smallpdf.com/txt-to-pdf")
    return filename

if __name__ == "__main__":
    print("サンプルPDF作成ツール\n")
    
    created_file = create_sample_pdf()
    
    if created_file.endswith('.pdf'):
        print(f"\n次のステップ:")
        print(f"python test_with_real_pdf.py")
        print(f"でPDFテストを実行できます")
    else:
        print(f"\nテキストファイル {created_file} をPDF化後、テストを実行してください")