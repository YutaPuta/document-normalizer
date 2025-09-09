# Document Normalizer for Azure

請求書（INVOICE）と発注書（PURCHASE_ORDER）のPDFを自動で読み取り、共通スキーマ（CDM）に正規化するAzure Functionsアプリケーション。

## 特徴

- PDFファイルの自動分類（請求書/発注書）
- Azure AI Document Intelligenceによる高精度データ抽出
- 宣言的YAMLマッピングによる柔軟な設定
- ベンダー別カスタマイズ対応
- データ検証とエンティティ解決
- Blob StorageとCosmos DBへの自動保存

## アーキテクチャ

```
PDF → Blob Storage → Event Grid → Azure Functions
         ↓
   Document Intelligence
         ↓
   CDM正規化 → Cosmos DB
         ↓
   成果物 → Blob Storage
```

## セットアップ

### 前提条件

- Python 3.9以上
- Azure サブスクリプション
- Azure Functions Core Tools
- Azure Storage Emulator（ローカル開発用）

### インストール

```bash
# 仮想環境作成（推奨：uv使用）
uv venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 依存関係のインストール
pip install -r requirements.txt

# ローカル設定の更新（Azure Functions用）
# local.settings.json を編集して以下を設定:
# - DOCUMENT_INTELLIGENCE_ENDPOINT（Azureデプロイ時のみ）
# - DOCUMENT_INTELLIGENCE_API_KEY（Azureデプロイ時のみ）
# - COSMOS_DB_ENDPOINT（オプション）
# - COSMOS_DB_KEY（オプション）
```

### ローカルテスト実行

```bash
# 🚀 すぐに実行可能なテスト
python test_with_text.py          # テキスト処理テスト
python test_local_fixed.py        # 総合パイプラインテスト
python simple_test.py             # 設定ファイルテスト
python detailed_test.py           # 詳細コンポーネントテスト

# PDFテスト（オプション）
python create_sample_pdf.py       # サンプルPDF作成
python test_with_real_pdf.py      # 実PDFファイルテスト

# Azure Functions ローカル実行（オプション）
func start                        # http://localhost:7071
```

## 処理フロー

1. **アップロード**: PDFを `inbox` コンテナにアップロード
2. **分類**: 文書種別（請求書/発注書）とベンダーを判定
3. **抽出**: Document Intelligenceでデータ抽出
4. **マッピング**: YAML設定に基づいてCDMに変換
5. **検証**: ビジネスルールと数値計算の検証
6. **保存**: Blob StorageとCosmos DBに保存

## 設定ファイル

### CDMスキーマ
- `config/cdm/invoice.schema.json`: 請求書スキーマ
- `config/cdm/purchase_order.schema.json`: 発注書スキーマ

### マッピング設定
- `config/mapping/global.yaml`: 共通マッピング
- `config/mapping/doc_type/`: 文書種別ごとのマッピング
- `config/mapping/vendors/`: ベンダー固有のマッピング

### 検証ルール
- `config/validation/rules.yaml`: データ検証ルール

### ベンダー設定
- `config/classifier/vendors.yaml`: ベンダー判定パターン

## カスタマイズ

### 新しいベンダーの追加

1. `config/classifier/vendors.yaml` にベンダー情報を追加
2. `config/mapping/vendors/[ベンダー名]/` ディレクトリを作成
3. ベンダー固有のマッピングファイルを作成

### マッピングルールの追加

```yaml
# config/mapping/vendors/新ベンダー/INVOICE.yaml
mappings:
  document_no:
    from: ["独自請求番号フィールド"]
    transform: ["trim", "upper"]
```

### 変換関数（日本語対応）

利用可能な変換関数:
- `trim`: 前後の空白を削除
- `upper`/`lower`: 大文字/小文字変換  
- `to_date`: 日付形式に変換
- `strip_currency`: 通貨記号を削除（¥、￥、円対応）
- `to_decimal`: 小数に変換
- `normalize_japanese`: 日本語正規化
- `parse_japanese_date`: 和暦解析（令和→2024年変換）
- `zenkaku_to_hankaku`: 全角半角変換（１２３→123）
- `normalize_phone`: 電話番号正規化
- `extract_postal_code`: 郵便番号抽出

## 出力形式

### CDM JSON
```json
{
  "doc": {
    "type": "INVOICE",
    "document_no": "INV-2024-001",
    "issue_date": "2024-01-15",
    "due_date": "2024-02-15",
    "currency": "JPY",
    "vendor": "株式会社エグザンプル"
  },
  "lines": [...],
  "totals": {
    "subtotal": 100000,
    "tax": 10000,
    "grand_total": 110000
  }
}
```

## 🧪 テスト結果

### ローカルテスト実行例
```bash
$ python test_with_text.py
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

## 🔧 高度な機能

### Serena統合（セマンティック検索）
```bash
# Serena MCP サーバー起動
serena start-mcp-server --project $(pwd)

# Claude Desktop でセマンティック検索とコード編集が利用可能
# - find_symbol: 関数・クラス検索
# - search_for_pattern: パターン検索  
# - replace_symbol_body: コード置換
```

## トラブルシューティング

### ローカルテストエラー
- 仮想環境が有効化されているか確認: `which python`
- 依存関係を再インストール: `pip install -r requirements.txt`
- 設定ファイルの存在確認: `ls config/`

### Document Intelligence エラー（本番環境）
- APIキーとエンドポイントを確認
- リージョンが正しいか確認
- クォータ制限を確認

### マッピングエラー
- YAMLファイルの構文を確認: `python -c "import yaml; yaml.safe_load(open('config/mapping/global.yaml'))"`
- フィールド名の大文字小文字を確認
- 変換関数のパラメータを確認

## デプロイ

```bash
# Azure にデプロイ
func azure functionapp publish <FunctionAppName>

# 環境変数を設定
az functionapp config appsettings set \
  --name <FunctionAppName> \
  --resource-group <ResourceGroup> \
  --settings \
    DOCUMENT_INTELLIGENCE_ENDPOINT=<endpoint> \
    DOCUMENT_INTELLIGENCE_API_KEY=<key>
```

## ライセンス

MIT