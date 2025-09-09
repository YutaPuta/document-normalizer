# 設定ファイルガイド

Document Normalizerの設定システムの詳細仕様と構成方法です。

## 📋 設定アーキテクチャ

### 3層マッピングシステム

```
Global Mapping        # 全文書共通のマッピング
    ↓ Override
Document Type Mapping # 文書種別固有のマッピング（請求書/発注書）
    ↓ Override  
Vendor Mapping        # ベンダー固有のマッピング
```

**優先順位**: ベンダー固有 > 文書種別固有 > グローバル

## 🗂️ ディレクトリ構造

```
config/
├── cdm/                    # CDMスキーマ定義
│   ├── invoice.schema.json
│   └── purchase_order.schema.json
├── mapping/                # フィールドマッピング設定
│   ├── global.yaml        # グローバルマッピング
│   ├── doc_type/          # 文書種別マッピング
│   │   ├── INVOICE.yaml
│   │   └── PURCHASE_ORDER.yaml
│   └── vendors/           # ベンダー固有マッピング
│       ├── 株式会社サンプル/
│       │   ├── INVOICE.yaml
│       │   └── PURCHASE_ORDER.yaml
│       └── Sample_Corp/
│           ├── INVOICE.yaml
│           └── PURCHASE_ORDER.yaml
├── classifier/             # 分類器設定
│   └── vendors.yaml       # ベンダー判定パターン
└── validation/            # 検証ルール
    └── rules.yaml
```

## ⚙️ 設定ファイル詳細

### 1. グローバルマッピング (`config/mapping/global.yaml`)

**役割**: 全文書種別・全ベンダー共通の基本フィールドマッピング

```yaml
# config/mapping/global.yaml
mappings:
  # 文書番号（請求書番号、発注書番号など）
  document_no:
    from: ["請求書番号", "請求番号", "Invoice Number", "発注番号", "PO Number"]
    transform: ["trim", "upper"]
    required: true
    
  # 発行日
  issue_date:
    from: ["発行日", "日付", "Date", "Issue Date"]
    transform: ["trim", "parse_japanese_date"]
    required: true
    
  # 支払期限・納期
  due_date:
    from: ["支払期限", "納期", "Due Date", "Delivery Date"]
    transform: ["trim", "parse_japanese_date"]
    required: false
    
  # 合計金額
  grand_total:
    from: ["合計", "総額", "Grand Total", "Total Amount"]
    transform: ["strip_currency", "to_decimal:0"]
    required: true
    
  # 小計
  subtotal:
    from: ["小計", "Subtotal", "Net Amount"]
    transform: ["strip_currency", "to_decimal:0"]
    required: false
    
  # 消費税額
  tax_amount:
    from: ["消費税", "税額", "Tax", "VAT"]
    transform: ["strip_currency", "to_decimal:0"]
    required: false
    
  # 通貨コード
  currency:
    from: ["通貨", "Currency"]
    transform: ["trim", "upper"]
    default: "JPY"
    
  # ベンダー名
  vendor:
    from: ["発行者", "会社名", "Vendor", "Company"]
    transform: ["trim", "normalize_japanese"]
    required: true
    
  # 住所
  address:
    from: ["住所", "所在地", "Address"]
    transform: ["trim", "normalize_japanese"]
    required: false
```

**設定要素の説明:**
- `from`: 抽出元フィールド名（複数指定可、優先順）
- `transform`: 適用する変換関数のリスト
- `required`: 必須フィールドかどうか
- `default`: デフォルト値

### 2. 文書種別マッピング

#### 請求書マッピング (`config/mapping/doc_type/INVOICE.yaml`)

```yaml
# 請求書固有のフィールド
mappings:
  payment_terms:
    from: ["支払条件", "Payment Terms"]
    transform: ["trim"]
    
  bank_account:
    from: ["振込先", "口座番号", "Bank Account"]
    transform: ["trim", "normalize_japanese"]
    
  invoice_type:
    from: ["請求書種別", "Type"]
    default: "STANDARD"
    
  # 請求書明細行の設定
  line_items:
    from: ["明細", "Items", "Line Items"]
    type: "array"
    fields:
      description:
        from: ["品目", "項目", "Description"]
        transform: ["trim"]
      quantity:
        from: ["数量", "Quantity", "Qty"]  
        transform: ["to_decimal:2"]
      unit_price:
        from: ["単価", "Unit Price"]
        transform: ["strip_currency", "to_decimal:0"]
      amount:
        from: ["金額", "Amount"]
        transform: ["strip_currency", "to_decimal:0"]
```

#### 発注書マッピング (`config/mapping/doc_type/PURCHASE_ORDER.yaml`)

```yaml
# 発注書固有のフィールド
mappings:
  delivery_date:
    from: ["納期", "Delivery Date", "Expected Date"]
    transform: ["trim", "parse_japanese_date"]
    
  delivery_address:
    from: ["納品先", "配送先", "Delivery Address"]
    transform: ["trim", "normalize_japanese"]
    
  order_type:
    from: ["発注種別", "Order Type"]
    default: "PURCHASE"
    
  supplier:
    from: ["発注先", "供給元", "Supplier"]
    transform: ["trim", "normalize_japanese"]
    
  # 発注明細行の設定
  line_items:
    from: ["明細", "Items"]
    type: "array"
    fields:
      product_code:
        from: ["品番", "商品コード", "Product Code"]
        transform: ["trim", "upper"]
      specification:
        from: ["仕様", "Specification", "Spec"]
        transform: ["trim"]
```

### 3. ベンダー固有マッピング

#### サンプル企業の請求書 (`config/mapping/vendors/株式会社サンプル/INVOICE.yaml`)

```yaml
# ベンダー固有のカスタムマッピング
mappings:
  document_no:
    # このベンダーは独特の請求番号形式を使用
    from: ["請求Ｎｏ．", "Invoice-No"]
    transform: ["zenkaku_to_hankaku", "trim", "upper"]
    
  issue_date:
    # このベンダーは特殊な日付形式を使用
    from: ["請求日付", "発行年月日"]
    transform: ["custom_date_parse", "parse_japanese_date"]
    
  # ベンダー特有のフィールド
  project_code:
    from: ["プロジェクト番号", "案件番号"]
    transform: ["trim", "upper"]
    
  contact_person:
    from: ["担当者", "連絡先担当"]
    transform: ["trim", "normalize_japanese"]
    
  # カスタム明細行処理
  line_items:
    from: ["作業明細", "項目一覧"]
    type: "array"
    fields:
      work_date:
        from: ["作業日", "実施日"]
        transform: ["parse_japanese_date"]
      hours:
        from: ["時間数", "工数"]
        transform: ["to_decimal:1"]
      hourly_rate:
        from: ["時間単価", "単価/h"]
        transform: ["strip_currency", "to_decimal:0"]
```

### 4. CDMスキーマ定義

#### 請求書スキーマ (`config/cdm/invoice.schema.json`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "請求書CDMスキーマ",
  "properties": {
    "doc": {
      "type": "object",
      "properties": {
        "type": {
          "type": "string",
          "enum": ["INVOICE"],
          "description": "文書種別"
        },
        "schema_version": {
          "type": "string",
          "pattern": "^[0-9]+\\.[0-9]+$",
          "description": "CDMスキーマバージョン"
        },
        "document_no": {
          "type": "string",
          "minLength": 1,
          "description": "請求書番号"
        },
        "issue_date": {
          "type": "string", 
          "format": "date",
          "description": "発行日（YYYY-MM-DD形式）"
        },
        "due_date": {
          "type": "string",
          "format": "date", 
          "description": "支払期限（YYYY-MM-DD形式）"
        },
        "currency": {
          "type": "string",
          "pattern": "^[A-Z]{3}$",
          "default": "JPY",
          "description": "通貨コード（ISO 4217）"
        },
        "vendor": {
          "type": "string",
          "minLength": 1,
          "description": "発行元ベンダー名"
        }
      },
      "required": ["type", "schema_version", "document_no", "issue_date", "vendor"]
    },
    "lines": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "line_no": {
            "type": "integer",
            "minimum": 1,
            "description": "明細行番号"
          },
          "description": {
            "type": "string",
            "description": "品目・サービス内容"
          },
          "qty": {
            "type": "number",
            "minimum": 0,
            "description": "数量"
          },
          "unit_price": {
            "type": "number", 
            "minimum": 0,
            "description": "単価"
          },
          "amount": {
            "type": "number",
            "minimum": 0,
            "description": "金額"
          },
          "tax_rate": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "税率（0.1 = 10%）"
          }
        },
        "required": ["description", "amount"]
      }
    },
    "totals": {
      "type": "object",
      "properties": {
        "subtotal": {
          "type": "number",
          "minimum": 0,
          "description": "小計"
        },
        "tax": {
          "type": "number", 
          "minimum": 0,
          "description": "消費税額"
        },
        "grand_total": {
          "type": "number",
          "minimum": 0,
          "description": "合計金額"
        }
      },
      "required": ["grand_total"]
    },
    "metadata": {
      "type": "object",
      "properties": {
        "confidence_scores": {
          "type": "object",
          "description": "各フィールドの信頼度スコア"
        },
        "unmapped_fields": {
          "type": "array",
          "items": {"type": "string"},
          "description": "マッピングできなかったフィールド"
        }
      }
    }
  },
  "required": ["doc", "lines", "totals", "metadata"]
}
```

### 5. ベンダー分類パターン (`config/classifier/vendors.yaml`)

```yaml
# ベンダー判定パターン設定
vendors:
  株式会社サンプル:
    patterns:
      - "株式会社サンプル"
      - "Sample Company"  
      - "サンプル会社"
    phone_patterns:
      - "03-1234-5678"
      - "03-1234-****"
    email_patterns:
      - "@sample.co.jp"
    address_patterns:
      - "東京都千代田区"
      - "Sample Building"
    confidence_weight: 0.9
    
  Sample_Corp:
    patterns:
      - "Sample Corp"
      - "Sample Corporation"
      - "サンプル Corp"
    phone_patterns:
      - "03-5678-1234"
    website_patterns:
      - "sample-corp.com"
    confidence_weight: 0.8
    
  デフォルトベンダー:
    patterns:
      - ".*株式会社.*"
      - ".*有限会社.*"
      - ".*Co\\..*Ltd.*"
    confidence_weight: 0.3
    fallback: true
```

### 6. 検証ルール (`config/validation/rules.yaml`)

```yaml
# データ検証ルール設定
validation_rules:
  # 必須フィールド検証
  required_fields:
    INVOICE: ["document_no", "issue_date", "grand_total", "vendor"]
    PURCHASE_ORDER: ["document_no", "issue_date", "grand_total", "supplier"]
    
  # 数値範囲検証
  numeric_ranges:
    grand_total:
      min: 1
      max: 100000000  # 1億円まで
    tax_rate:
      min: 0
      max: 1
      
  # 日付検証
  date_validation:
    issue_date:
      min_date: "2000-01-01"
      max_date: "+1year"  # 1年後まで
    due_date:
      min_date: "issue_date"  # 発行日以降
      max_date: "+2years"
      
  # 文字列長検証
  string_lengths:
    document_no:
      min: 3
      max: 50
    vendor:
      min: 2
      max: 100
      
  # 金額整合性チェック
  amount_consistency:
    subtotal_plus_tax_equals_total: true
    line_total_equals_subtotal: true
    tax_calculation_tolerance: 10  # 税額計算誤差許容値
    
  # 業務ルール
  business_rules:
    # 消費税率チェック
    valid_tax_rates: [0.0, 0.08, 0.10]  # 0%, 8%, 10%
    
    # 支払期限チェック  
    payment_terms_days: [0, 30, 60, 90]  # 即日、30日、60日、90日
    
    # 文書番号形式チェック
    document_no_patterns:
      INVOICE: "^(INV|請求)-[0-9]{4,}-[0-9]{3,}$"
      PURCHASE_ORDER: "^(PO|発注)-[0-9]{4,}-[0-9]{3,}$"
```

## 🔧 設定の動的ロード

### ConfigLoaderクラスの使用

```python
from config_loader import ConfigLoader

# 設定ローダー初期化
config = ConfigLoader()

# 特定ベンダー・文書種別のマッピング取得
mapping = config.get_mapping_config("INVOICE", "株式会社サンプル")

# CDMスキーマ取得
schema = config.get_cdm_schema("INVOICE")

# 検証ルール取得
rules = config.get_validation_rules()

# 設定の妥当性検証
validation_report = config.validate_config()
```

### 設定の優先順位解決

```python
# 設定解決例
def resolve_field_mapping(field_name, doc_type, vendor_name):
    # 1. ベンダー固有設定を確認
    vendor_config = load_vendor_config(vendor_name, doc_type)
    if field_name in vendor_config.get('mappings', {}):
        return vendor_config['mappings'][field_name]
    
    # 2. 文書種別設定を確認  
    doc_type_config = load_doc_type_config(doc_type)
    if field_name in doc_type_config.get('mappings', {}):
        return doc_type_config['mappings'][field_name]
        
    # 3. グローバル設定を確認
    global_config = load_global_config()
    if field_name in global_config.get('mappings', {}):
        return global_config['mappings'][field_name]
        
    # 4. デフォルト設定
    return None
```

## 🧪 設定テスト

### 設定ファイル検証

```bash
# YAML構文チェック
python -c "import yaml; yaml.safe_load(open('config/mapping/global.yaml'))"

# JSON Schema検証
python -c "import json; json.load(open('config/cdm/invoice.schema.json'))"

# 設定統合テスト
python simple_test.py
```

### カスタム設定の作成

```bash
# 新ベンダー設定作成
mkdir -p config/mapping/vendors/新会社名
cp config/mapping/vendors/株式会社サンプル/INVOICE.yaml \
   config/mapping/vendors/新会社名/INVOICE.yaml

# ベンダーパターン追加
# config/classifier/vendors.yamlを編集

# 設定テスト実行
python detailed_test.py
```

## 🔍 デバッグとトラブルシューティング

### 設定ロードエラーの診断

```python
# デバッグ用設定チェック
def debug_config_loading():
    try:
        config = ConfigLoader()
        
        # 各設定ファイルの読み込み状況確認
        print("Global mapping:", bool(config.global_mapping))
        print("Document schemas:", list(config.cdm_schemas.keys()))
        print("Vendor patterns:", list(config.vendor_patterns.keys()))
        
        # 設定内容のサマリー
        print(f"Total mappings: {len(config.global_mapping.get('mappings', {}))}")
        
    except Exception as e:
        print(f"Config loading error: {e}")
        import traceback
        traceback.print_exc()
```

### マッピング動作確認

```python
# フィールドマッピングのデバッグ  
def debug_field_mapping(field_name, doc_type, vendor_name):
    config = ConfigLoader()
    
    # マッピング解決過程を表示
    print(f"Resolving mapping for: {field_name}")
    print(f"Document type: {doc_type}")
    print(f"Vendor: {vendor_name}")
    
    mapping = config.get_mapping_config(doc_type, vendor_name)
    if field_name in mapping.get('mappings', {}):
        field_config = mapping['mappings'][field_name]
        print(f"Found mapping: {field_config}")
        print(f"Source fields: {field_config.get('from', [])}")
        print(f"Transforms: {field_config.get('transform', [])}")
    else:
        print("No mapping found")
```

## 📚 関連ドキュメント

- [ローカル実行ガイド](LOCAL_TESTING.md) - 設定テスト方法
- [日本語処理機能](JAPANESE_PROCESSING.md) - 変換関数詳細
- [CDMスキーマ仕様](CDM_SCHEMA.md) - 出力形式仕様
- [Azure デプロイメント](AZURE_DEPLOYMENT.md) - 本番環境設定