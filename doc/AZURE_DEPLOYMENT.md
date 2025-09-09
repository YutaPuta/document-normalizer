# Azure デプロイメントガイド

Document NormalizerをAzure環境に本番デプロイするための完全ガイドです。

## 📋 目次

- [前提条件](#前提条件)
- [Azure リソース作成](#azure-リソース作成)
- [設定とデプロイ](#設定とデプロイ)
- [動作確認](#動作確認)
- [監視と運用](#監視と運用)
- [トラブルシューティング](#トラブルシューティング)

## 🚀 前提条件

### 必要なツール
- Azure CLI 2.0以上
- Azure Functions Core Tools 4.0以上
- Python 3.9以上
- 有効なAzureサブスクリプション

### 権限要件
以下のAzure権限が必要です：
- リソースグループの作成・管理
- Storage Account の作成・管理
- Azure Functions の作成・管理
- Azure AI Document Intelligence の作成・管理
- Cosmos DB の作成・管理（オプション）

## ☁️ Azure リソース作成

### 1. Azure CLI ログイン

```bash
# Azure CLI ログイン
az login

# サブスクリプション確認
az account show

# 使用するサブスクリプション設定
az account set --subscription "<subscription-id>"
```

### 2. リソースグループ作成

```bash
# 変数設定
RESOURCE_GROUP="doc-normalizer-rg"
LOCATION="japaneast"
APP_NAME="doc-normalizer-$(date +%s)"

# リソースグループ作成
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

### 3. Storage Account 作成

```bash
STORAGE_ACCOUNT="${APP_NAME}storage"

# Storage Account 作成
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2

# Blob コンテナ作成
STORAGE_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT \
  --query '[0].value' -o tsv)

az storage container create \
  --name inbox \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY

az storage container create \
  --name processed \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY

az storage container create \
  --name artifacts \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY
```

### 4. Azure AI Document Intelligence 作成

```bash
DOCINT_NAME="${APP_NAME}-docint"

# Document Intelligence リソース作成
az cognitiveservices account create \
  --name $DOCINT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --kind FormRecognizer \
  --sku S0 \
  --custom-domain $DOCINT_NAME

# エンドポイントとキー取得
DOCINT_ENDPOINT=$(az cognitiveservices account show \
  --name $DOCINT_NAME \
  --resource-group $RESOURCE_GROUP \
  --query 'properties.endpoint' -o tsv)

DOCINT_KEY=$(az cognitiveservices account keys list \
  --name $DOCINT_NAME \
  --resource-group $RESOURCE_GROUP \
  --query 'key1' -o tsv)

echo "Document Intelligence Endpoint: $DOCINT_ENDPOINT"
echo "Document Intelligence Key: $DOCINT_KEY"
```

### 5. Azure Functions App 作成

```bash
# Function App 作成
az functionapp create \
  --resource-group $RESOURCE_GROUP \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.9 \
  --functions-version 4 \
  --name $APP_NAME \
  --storage-account $STORAGE_ACCOUNT \
  --os-type Linux

# Function App URL確認
FUNCTION_URL=$(az functionapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query 'defaultHostName' -o tsv)

echo "Function App URL: https://$FUNCTION_URL"
```

### 6. Cosmos DB 作成（オプション）

```bash
COSMOS_NAME="${APP_NAME}-cosmos"

# Cosmos DB アカウント作成
az cosmosdb create \
  --name $COSMOS_NAME \
  --resource-group $RESOURCE_GROUP \
  --locations regionName=$LOCATION \
  --default-consistency-level Eventual

# データベース作成
az cosmosdb sql database create \
  --account-name $COSMOS_NAME \
  --resource-group $RESOURCE_GROUP \
  --name DocumentNormalizer

# コンテナ作成
az cosmosdb sql container create \
  --account-name $COSMOS_NAME \
  --resource-group $RESOURCE_GROUP \
  --database-name DocumentNormalizer \
  --name ProcessedDocuments \
  --partition-key-path "/doc/document_no" \
  --throughput 400

# 接続文字列取得
COSMOS_CONNECTION=$(az cosmosdb keys list \
  --name $COSMOS_NAME \
  --resource-group $RESOURCE_GROUP \
  --type connection-strings \
  --query 'connectionStrings[0].connectionString' -o tsv)

echo "Cosmos DB Connection: $COSMOS_CONNECTION"
```

## ⚙️ 設定とデプロイ

### 1. アプリケーション設定

```bash
# Storage接続文字列取得
STORAGE_CONNECTION=$(az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query 'connectionString' -o tsv)

# Function App設定更新
az functionapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    AzureWebJobsStorage="$STORAGE_CONNECTION" \
    DOCUMENT_INTELLIGENCE_ENDPOINT="$DOCINT_ENDPOINT" \
    DOCUMENT_INTELLIGENCE_API_KEY="$DOCINT_KEY" \
    COSMOS_DB_CONNECTION_STRING="$COSMOS_CONNECTION" \
    STORAGE_CONNECTION_STRING="$STORAGE_CONNECTION"
```

### 2. local.settings.json 更新

```bash
# ローカル開発用設定ファイル更新
cat > local.settings.json << EOF
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "$STORAGE_CONNECTION",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "DOCUMENT_INTELLIGENCE_ENDPOINT": "$DOCINT_ENDPOINT",
    "DOCUMENT_INTELLIGENCE_API_KEY": "$DOCINT_KEY",
    "COSMOS_DB_CONNECTION_STRING": "$COSMOS_CONNECTION",
    "STORAGE_CONNECTION_STRING": "$STORAGE_CONNECTION"
  }
}
EOF
```

### 3. アプリケーションデプロイ

```bash
# 仮想環境有効化
source .venv/bin/activate

# デプロイ実行
func azure functionapp publish $APP_NAME

# デプロイ状況確認
az functionapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query 'state'
```

### 4. 関数URL取得

```bash
# HTTP トリガー関数のURL取得
az functionapp function show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --function-name test_http \
  --query 'invokeUrlTemplate' -o tsv

# Blob トリガー関数確認
az functionapp function list \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query '[].{Name:name, Trigger:trigger.type}'
```

## 🧪 動作確認

### 1. HTTP エンドポイントテスト

```bash
# ヘルスチェック
curl "https://$FUNCTION_URL/api/test_http"

# 期待されるレスポンス例
{
  "status": "success",
  "message": "Document Normalizer is running!",
  "features": [
    "PDF document classification",
    "Azure Document Intelligence integration", 
    "CDM schema mapping",
    "Data validation and entity resolution"
  ]
}
```

### 2. Blob トリガーテスト

```bash
# テスト用PDFファイルをアップロード
az storage blob upload \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --container-name inbox \
  --name test-invoice.pdf \
  --file sample_invoice.pdf

# 処理ログ確認
az functionapp log tail \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP
```

### 3. 結果確認

```bash
# 処理済みファイル確認
az storage blob list \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --container-name processed \
  --output table

# アーティファクト確認
az storage blob list \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --container-name artifacts \
  --output table
```

## 📊 監視と運用

### 1. Application Insights 設定

```bash
# Application Insights 作成
APPINSIGHTS_NAME="${APP_NAME}-insights"

az extension add --name application-insights

az monitor app-insights component create \
  --app $APPINSIGHTS_NAME \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP

# Instrumentation Key 取得
APPINSIGHTS_KEY=$(az monitor app-insights component show \
  --app $APPINSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query 'instrumentationKey' -o tsv)

# Function Appに設定追加
az functionapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    APPINSIGHTS_INSTRUMENTATIONKEY="$APPINSIGHTS_KEY"
```

### 2. ログ監視

```bash
# リアルタイムログ
az functionapp log tail \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP

# Application Insights クエリ例
az monitor app-insights query \
  --app $APPINSIGHTS_NAME \
  --analytics-query "
    requests 
    | where timestamp > ago(1h)
    | summarize count() by resultCode
    | render piechart
  "
```

### 3. メトリクス監視

```bash
# Function 実行数
az monitor metrics list \
  --resource "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$APP_NAME" \
  --metric "FunctionExecutionCount" \
  --interval 1h

# エラー率
az monitor metrics list \
  --resource "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$APP_NAME" \
  --metric "Http5xx" \
  --interval 1h
```

### 4. アラート設定

```bash
# エラー率アラート
az monitor metrics alert create \
  --name "HighErrorRate" \
  --resource-group $RESOURCE_GROUP \
  --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$APP_NAME" \
  --condition "avg Http5xx > 5" \
  --description "High error rate detected" \
  --evaluation-frequency 1m \
  --window-size 5m
```

## 🔧 運用管理

### 1. デプロイメントスロット

```bash
# ステージングスロット作成
az functionapp deployment slot create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --slot staging

# ステージングにデプロイ
func azure functionapp publish $APP_NAME --slot staging

# 本番にスワップ
az functionapp deployment slot swap \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --slot staging \
  --target-slot production
```

### 2. 設定管理

```bash
# 設定のバックアップ
az functionapp config appsettings list \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP > appsettings-backup.json

# 設定の復元  
az functionapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings @appsettings-backup.json
```

### 3. スケーリング設定

```bash
# 消費量プランの制限設定
az functionapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --dailyMemoryTimeQuota 400000

# 同時実行数制限
az functionapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --max-concurrent-requests 100
```

## 🐛 トラブルシューティング

### よくある問題と解決方法

#### 1. デプロイエラー

```bash
# 問題: "Requirements.txt not found" 
# 解決: requirements.txtが存在することを確認
ls -la requirements.txt
func azure functionapp publish $APP_NAME --build remote

# 問題: Python バージョンエラー
# 解決: ローカルとAzureのPythonバージョン一致確認
python --version
az functionapp config show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query 'pythonVersion'
```

#### 2. Document Intelligence エラー

```bash
# API キー確認
az cognitiveservices account keys list \
  --name $DOCINT_NAME \
  --resource-group $RESOURCE_GROUP

# クォータ使用量確認
az cognitiveservices account usage show \
  --name $DOCINT_NAME \
  --resource-group $RESOURCE_GROUP
```

#### 3. Storage 接続エラー

```bash
# 接続文字列テスト
az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP

# コンテナアクセス権限確認
az storage container show-permission \
  --name inbox \
  --account-name $STORAGE_ACCOUNT
```

#### 4. 関数実行エラー

```bash
# 詳細ログ確認
az functionapp log tail \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP

# 関数統計確認
az monitor app-insights query \
  --app $APPINSIGHTS_NAME \
  --analytics-query "
    requests 
    | where timestamp > ago(24h)
    | where success == false
    | project timestamp, name, resultCode, customDimensions
    | order by timestamp desc
  "
```

### パフォーマンス最適化

#### 1. 並列処理設定

```bash
# host.json でバッチサイズ調整
cat > host.json << EOF
{
  "version": "2.0",
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[2.*, 3.0.0)"
  },
  "extensions": {
    "blobs": {
      "maxDegreeOfParallelism": 4
    }
  }
}
EOF
```

#### 2. タイムアウト設定

```bash
# Function タイムアウト延長
az functionapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --timeout 300  # 5分
```

#### 3. メモリ最適化

```python
# Python メモリ使用量監視
import psutil
import os

def log_memory_usage():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    logging.info(f"Memory usage: {memory_info.rss / 1024 / 1024:.1f} MB")
```

## 🛡️ セキュリティ

### 1. Key Vault 統合

```bash
# Key Vault 作成
KEYVAULT_NAME="${APP_NAME}-kv"

az keyvault create \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# シークレット保存
az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name "DocumentIntelligenceKey" \
  --value "$DOCINT_KEY"

# Function App に Key Vault 参照設定
az functionapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    DOCUMENT_INTELLIGENCE_API_KEY="@Microsoft.KeyVault(SecretUri=https://$KEYVAULT_NAME.vault.azure.net/secrets/DocumentIntelligenceKey/)"
```

### 2. ネットワーク制限

```bash
# Function App の IP制限
az functionapp config access-restriction add \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --rule-name "AllowOfficeIP" \
  --action Allow \
  --ip-address "203.0.113.0/24"
```

### 3. 認証設定

```bash
# Azure AD 認証有効化
az functionapp auth update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --enabled true \
  --action LoginWithAzureActiveDirectory
```

## 📋 チェックリスト

### デプロイ前チェック
- [ ] Azure CLI ログイン完了
- [ ] 必要なリソース作成権限確認
- [ ] ローカルテスト完了
- [ ] requirements.txt 更新
- [ ] 設定ファイル準備

### デプロイ後チェック
- [ ] HTTP エンドポイント応答確認
- [ ] Blob トリガー動作確認
- [ ] Document Intelligence 接続確認
- [ ] Storage アクセス確認
- [ ] ログ出力確認
- [ ] メトリクス監視設定
- [ ] アラート設定

### 運用開始チェック
- [ ] 監視ダッシュボード設定
- [ ] バックアップ戦略確立
- [ ] インシデント対応手順作成
- [ ] 定期メンテナンス計画
- [ ] セキュリティ監査実施

## 📚 関連ドキュメント

- [ローカル実行ガイド](LOCAL_TESTING.md) - 開発環境構築
- [設定ファイルガイド](CONFIGURATION.md) - カスタマイズ設定
- [CDMスキーマ仕様](CDM_SCHEMA.md) - データ形式仕様