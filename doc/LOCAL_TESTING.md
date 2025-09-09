# ローカル実行ガイド

Document Normalizerをローカル環境で実行・テストする完全ガイドです。

## 📋 目次

- [環境セットアップ](#環境セットアップ)
- [基本テスト](#基本テスト)
- [PDFテスト](#pdfテスト)
- [Azure Functions テスト](#azure-functions-テスト)
- [トラブルシューティング](#トラブルシューティング)

## 🚀 環境セットアップ

### 前提条件
- Python 3.9以上
- Git

### 1. プロジェクトのクローン
```bash
git clone <repository-url>
cd doc-normalizer
```

### 2. 仮想環境の作成（推奨：uv使用）
```bash
# uvがない場合はインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# 仮想環境作成と有効化
uv venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 依存関係インストール
pip install -r requirements.txt
```

### 3. 設定確認
```bash
# 設定ファイルの存在確認
ls config/
# 出力例:
# cdm/  classifier/  mapping/  validation/

# Python環境確認
which python
# 仮想環境のPythonパスが表示されることを確認
```

## 🧪 基本テスト

### 1. 設定ファイルテスト
```bash
python simple_test.py
```
**実行内容:**
- YAML設定ファイルの読み込み確認
- JSON Schema の妥当性チェック
- 設定構造の整合性検証

**期待する出力:**
```
=== Document Normalizer 基本動作テスト ===
✅設定ファイル読み込みテスト成功
✅テキスト処理パイプラインテスト成功
✅CDMデータ生成テスト成功
```

### 2. 詳細コンポーネントテスト
```bash
python detailed_test.py
```
**実行内容:**
- 各モジュール個別テスト
- 日本語処理機能テスト
- CDMマッピング機能テスト
- データ検証機能テスト

### 3. テキスト処理パイプラインテスト
```bash
python test_with_text.py
```
**実行内容:**
- サンプルテキストでの完全パイプライン実行
- 和暦変換テスト（令和6年→2024年）
- 金額処理テスト（¥55,000→55000）
- CDM出力形式確認

**実行例:**
```
=== テキスト処理機能テスト ===

1. サンプルテキスト読み込み:
   文字数: 248
   
2. 文書種別判定:
   判定結果: INVOICE

3. ベンダー判定:
   判定結果: 株式会社サンプル

4. フィールド抽出:
   抽出フィールド数: 8
   document_no: INV-2024-TEST-001
   issue_date_raw: 令和6年1月15日
   
5. 日本語変換処理:
   issue_date: 2024-01-15 ✅
   grand_total: 55000 ✅

✅ テキスト処理パイプラインが正常に動作しました！
```

### 4. 総合パイプラインテスト
```bash
python test_local_fixed.py
```
**実行内容:**
- パイプライン全体の統合テスト
- モックデータでの処理フロー確認
- エラーハンドリング確認

## 📄 PDFテスト

### PDFライブラリのインストール
```bash
# PDFライブラリ追加（オプション）
pip install reportlab fpdf2
```

### 方法1: サンプルPDF作成テスト
```bash
# 1. サンプルPDF作成
python create_sample_pdf.py

# 2. PDFテスト実行
python pdf_test.py
```

**期待する出力:**
```
Document Normalizer - PDFテスト

📄 PDFファイル発見: sample_invoice.pdf
=== PDFファイル処理テスト: sample_invoice.pdf ===

1. PDFファイル読み込み...
   ファイルサイズ: 3,554 bytes

2. PDFテキスト抽出...
   抽出文字数: 259
   テキスト例: 請求書\n\n請求番号: INV-2024-TEST-001...

3. 文書分類...
   文書種別: INVOICE (信頼度: 0.90)

4. ベンダー判定...
   ベンダー: 株式会社サンプル (信頼度: 0.80)

5. フィールド抽出...
   抽出フィールド数: 6
   document_no: INV-2024-TEST-001
   issue_date: 2024-01-15
   grand_total: 55000

✅ PDFテスト成功！Document Normalizerは正常に動作しています
```

### 方法2: 既存PDFファイルテスト
```bash
# 1. PDFファイルを以下の名前で配置
# - sample_invoice.pdf
# - test_invoice.pdf
# - invoice.pdf
# - 請求書.pdf

# 2. テスト実行
python pdf_test.py
```

### 方法3: 任意のPDFファイルテスト
```bash
# 特定ファイルのテスト
python -c "from pdf_test import test_pdf_processing; test_pdf_processing('your_file.pdf')"
```

## ⚡ Azure Functions テスト

### 1. Azure Functions Core Tools のインストール
```bash
# macOS
brew tap azure/functions
brew install azure-functions-core-tools@4

# Windows (chocolatey)
choco install azure-functions-core-tools

# Ubuntu
wget -q https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4
```

### 2. ローカル設定ファイル作成
```bash
# local.settings.json作成（Azure設定用）
cat > local.settings.json << EOF
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "DOCUMENT_INTELLIGENCE_ENDPOINT": "",
    "DOCUMENT_INTELLIGENCE_API_KEY": "",
    "COSMOS_DB_ENDPOINT": "",
    "COSMOS_DB_KEY": ""
  }
}
EOF
```

### 3. Azure Functions起動
```bash
# Azure Functions起動
func start

# 別ターミナルでテスト
curl http://localhost:7071/api/test_http
```

### 4. Functionsテスト
```bash
python simple_func_test.py
```

**実行内容:**
- HTTP Functions のモックテスト
- Blob Trigger Functions のモックテスト  
- 設定ファイル統合テスト

## 🔧 高度な機能

### Serena統合（セマンティック検索）

Serenaが導入済みの場合、以下の機能が利用可能：

```bash
# MCP サーバー起動
serena start-mcp-server --project $(pwd)

# Claude Desktop で以下が利用可能:
# - find_symbol: 関数・クラス検索
# - search_for_pattern: パターン検索
# - replace_symbol_body: コード置換
# - プロジェクト記憶システム
```

### 設定カスタマイズ

#### 新しいベンダー追加
```bash
# 1. ベンダーディレクトリ作成
mkdir -p config/mapping/vendors/新ベンダー

# 2. マッピングファイル作成
cat > config/mapping/vendors/新ベンダー/INVOICE.yaml << EOF
mappings:
  document_no:
    from: ["独自請求番号フィールド"]
    transform: ["trim", "upper"]
  issue_date:
    from: ["発行日付フィールド"]
    transform: ["parse_japanese_date"]
EOF

# 3. ベンダーパターン追加
# config/classifier/vendors.yaml を編集
```

#### 変換関数追加
```bash
# src/transforms.py に新しい変換関数を追加
# 例: def custom_transform(value): return processed_value
```

## 🐛 トラブルシューティング

### よくある問題と解決方法

#### 1. 仮想環境関連エラー
```bash
# 問題: ImportError: No module named 'xxx'
# 解決:
which python  # 仮想環境確認
source .venv/bin/activate  # 仮想環境有効化
pip install -r requirements.txt  # 依存関係再インストール
```

#### 2. PDFテキスト抽出エラー
```bash
# 問題: PDF text extraction failed
# 解決:
pip install pdfminer.six  # ライブラリ確認
python -c "import pdfminer; print('OK')"  # インストール確認
```

#### 3. YAML設定エラー
```bash
# 問題: YAMLファイルの構文エラー
# 解決:
python -c "import yaml; yaml.safe_load(open('config/mapping/global.yaml'))"
# エラー箇所が表示されるので修正
```

#### 4. 日本語処理エラー
```bash
# 問題: 和暦変換が失敗する
# 解決:
python -c "
import sys
sys.path.insert(0, 'src')
from transforms import parse_japanese_date
print(parse_japanese_date('令和6年1月15日'))
"
```

#### 5. Azure Functions起動エラー
```bash
# 問題: func start が失敗する
# 解決:
func --version  # バージョン確認
pip install azure-functions  # 依存関係確認
ls function.json  # 設定ファイル確認
```

### ログ確認方法

```bash
# Python実行時の詳細ログ
python -v test_with_text.py

# Azure Functions ログ
func start --verbose

# モジュール読み込み確認
python -c "
import sys
sys.path.insert(0, 'src')
print('Available modules:')
import os
for f in os.listdir('src'):
    if f.endswith('.py'):
        print(f'  {f[:-3]}')
"
```

### パフォーマンス確認

```bash
# 処理時間測定
time python test_with_text.py

# メモリ使用量確認
python -m memory_profiler test_with_text.py
```

## 📊 テスト成功の確認項目

### ✅ 基本機能チェックリスト
- [ ] 設定ファイル読み込み成功
- [ ] テキスト処理パイプライン動作
- [ ] 文書種別分類（INVOICE/PURCHASE_ORDER）
- [ ] ベンダー判定機能
- [ ] フィールド抽出機能
- [ ] 日本語処理（和暦変換、全角半角変換）
- [ ] CDMデータ生成
- [ ] JSON出力形式確認

### ✅ PDFテスト チェックリスト  
- [ ] PDFテキスト抽出成功
- [ ] PDF分類精度 > 80%
- [ ] フィールド抽出精度確認
- [ ] 金額計算正確性
- [ ] 最終CDM出力妥当性

### ✅ Azure Functions チェックリスト
- [ ] HTTP エンドポイント応答
- [ ] Blob トリガー動作確認
- [ ] 設定ファイル統合テスト成功
- [ ] エラーハンドリング確認

## 🎯 次のステップ

ローカルテストが完了したら、以下に進むことができます：

1. **Azure環境のセットアップ**: [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)を参照
2. **本番データでのテスト**: 実際の請求書PDFでの検証
3. **カスタマイズ**: 組織固有のベンダーやフィールドマッピング追加
4. **継続的インテグレーション**: CI/CDパイプライン構築

## 📚 関連ドキュメント

- [設定ファイル詳細](CONFIGURATION.md)
- [日本語処理機能](JAPANESE_PROCESSING.md)  
- [CDMスキーマ仕様](CDM_SCHEMA.md)
- [Azure デプロイメント](AZURE_DEPLOYMENT.md)