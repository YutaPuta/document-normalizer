# Azure環境構築 超詳細ステップバイステップガイド

初心者でも迷わずDocument NormalizerをAzureにデプロイできる完全ガイドです。

## 📋 目次

- [始める前の準備](#始める前の準備)
- [必要なツールのインストール](#step-1-必要なツールのインストール)
- [Azureにログイン](#step-2-azureにログイン)
- [リソースグループ作成](#step-3-リソースグループ作成)
- [Storage Account作成](#step-4-storage-account作成)
- [Document Intelligence作成](#step-5-document-intelligence作成)
- [Azure Functions作成](#step-6-azure-functions作成)
- [アプリケーションデプロイ](#step-7-アプリケーションデプロイ)
- [動作確認](#step-8-動作確認)
- [設定情報の保存](#step-9-設定情報の保存)
- [困ったときは](#困ったときは)

## 🎯 始める前の準備

### Step 0-1: Azureアカウント作成
1. **ブラウザで** https://azure.microsoft.com/ja-jp/free/ にアクセス
2. **「無料で始める」** ボタンをクリック
3. **Microsoftアカウント**でサインイン（なければ作成）
4. **クレジットカード情報**を入力（無料枠内なら課金されません）
5. **電話番号認証**を完了
6. **「サインアップ」** をクリック

### Step 0-2: Azure Portal確認
```
1. https://portal.azure.com にアクセス
2. ログイン
3. 「サブスクリプション」をクリック
4. サブスクリプションIDをメモ（後で使います）
   例: 12345678-1234-1234-1234-123456789abc
```

### 必要な時間とコスト
- **セットアップ時間**: 約30-45分
- **月額コスト目安**:
  - Document Intelligence S0: 約2,000円
  - Storage Account: 約100円
  - Azure Functions: 無料枠内で収まる可能性大
  - Cosmos DB: 約500円（オプション）

## 🔧 Step 1: 必要なツールのインストール

### Step 1-1: Azure CLIインストール

#### **macOSの場合**
```bash
# Homebrewがない場合は先にインストール
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Azure CLIインストール
brew update
brew install azure-cli

# 確認
az --version
# 出力例: azure-cli 2.50.0
```

#### **Windowsの場合**
1. https://aka.ms/installazurecliwindows にアクセス
2. ダウンロードされた`AzureCLI.msi`をダブルクリック
3. インストーラーの指示に従う
4. **コマンドプロンプト**を**新しく開く**
5. 確認コマンド実行：
```cmd
az --version
```

#### **Ubuntu/Debianの場合**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# 確認
az --version
```

### Step 1-2: Azure Functions Core Toolsインストール

#### **macOSの場合**
```bash
brew tap azure/functions
brew install azure-functions-core-tools@4

# 確認
func --version
# 出力例: 4.0.5455
```

#### **Windowsの場合**
1. https://go.microsoft.com/fwlink/?linkid=2174087 にアクセス
2. ダウンロードされたインストーラーを実行
3. インストール完了後、新しいコマンドプロンプトで確認：
```cmd
func --version
```

#### **Ubuntu/Debianの場合**
```bash
# Microsoft GPGキーを信頼リストに追加
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg

# APTソースリストにMicrosoftのリポジトリを追加
sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-ubuntu-$(lsb_release -cs)-prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/dotnetdev.list'

# パッケージリスト更新とインストール
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4

# 確認
func --version
```

### Step 1-3: Pythonの確認
```bash
python3 --version
# Python 3.9以上であることを確認
# 出力例: Python 3.9.17

# Pythonがない場合のインストール
# macOS: brew install python@3.9
# Windows: https://www.python.org/downloads/ からインストーラーをダウンロード
# Ubuntu: sudo apt-get install python3.9 python3.9-venv
```

## 🚀 Step 2: Azureにログイン

### Step 2-1: ターミナル/コマンドプロンプトを開く
```bash
# プロジェクトディレクトリに移動
cd doc-normalizer
```

### Step 2-2: Azureログイン実行
```bash
az login
```
**動作:**
1. ブラウザが自動で開く
2. Microsoftアカウントでログイン
3. 「認証が完了しました」と表示される
4. ターミナルに戻る

### Step 2-3: ログイン確認
```bash
az account show
```
**出力例:**
```json
{
  "environmentName": "AzureCloud",
  "id": "12345678-1234-1234-1234-123456789abc",
  "name": "無料試用版",
  "state": "Enabled",
  "user": {
    "name": "your-email@example.com"
  }
}
```

### Step 2-4: 複数のサブスクリプションがある場合
```bash
# サブスクリプション一覧表示
az account list --output table

# 使用するサブスクリプションを選択
az account set --subscription "サブスクリプション名またはID"
```

## 🏗️ Step 3: リソースグループ作成

### Step 3-1: 名前を決める
```bash
# これらの値を設定（コピー＆ペーストして実行）
RESOURCE_GROUP="doc-normalizer-rg"
LOCATION="japaneast"
APP_NAME="docnorm$(date +%s)"

# 確認
echo "リソースグループ名: $RESOURCE_GROUP"
echo "リージョン: $LOCATION"
echo "アプリ名: $APP_NAME"
```

**リージョン選択の指針:**
- `japaneast`: 東日本（推奨）
- `japanwest`: 西日本
- `eastasia`: 東アジア（香港）
- `southeastasia`: 東南アジア（シンガポール）

### Step 3-2: リソースグループ作成
```bash
az group create --name $RESOURCE_GROUP --location $LOCATION
```
**成功時の出力:**
```json
{
  "id": "/subscriptions/.../resourceGroups/doc-normalizer-rg",
  "location": "japaneast",
  "name": "doc-normalizer-rg",
  "properties": {
    "provisioningState": "Succeeded"
  }
}
```

### Step 3-3: Azure Portalで確認
1. https://portal.azure.com にアクセス
2. 上部の検索バーに「リソースグループ」と入力
3. 「doc-normalizer-rg」が表示されることを確認

## 💾 Step 4: Storage Account作成

### Step 4-1: Storage Account名を生成
```bash
# ランダムな名前を生成（グローバルで一意である必要があるため）
STORAGE_ACCOUNT="docnorm$RANDOM$RANDOM"
echo "Storage Account名: $STORAGE_ACCOUNT"
# 出力例: docnorm1234556789
```

**命名規則:**
- 3-24文字
- 小文字と数字のみ
- グローバルで一意

### Step 4-2: Storage Account作成（約1分かかります）
```bash
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2
```
**成功メッセージを待つ:**
```json
{
  "provisioningState": "Succeeded",
  "primaryEndpoints": {
    "blob": "https://docnorm123456.blob.core.windows.net/"
  }
}
```

### Step 4-3: 接続文字列を取得
```bash
STORAGE_CONNECTION=$(az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query 'connectionString' -o tsv)

echo "接続文字列取得完了"
```

### Step 4-4: Blobコンテナ作成
```bash
# Storageキー取得
STORAGE_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT \
  --query '[0].value' -o tsv)

# inboxコンテナ作成（PDFアップロード用）
az storage container create \
  --name inbox \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY

echo "✅ inboxコンテナ作成完了"

# processedコンテナ作成（処理済みファイル保存用）
az storage container create \
  --name processed \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY

echo "✅ processedコンテナ作成完了"

# artifactsコンテナ作成（生成ファイル保存用）
az storage container create \
  --name artifacts \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY

echo "✅ artifactsコンテナ作成完了"

# コンテナ一覧確認
az storage container list \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --output table
```

## 🧠 Step 5: Document Intelligence作成

### Step 5-1: Document Intelligenceリソース名設定
```bash
DOCINT_NAME="${APP_NAME}-docint"
echo "Document Intelligence名: $DOCINT_NAME"
```

### Step 5-2: リソース作成（約2分かかります）
```bash
az cognitiveservices account create \
  --name $DOCINT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --kind FormRecognizer \
  --sku S0 \
  --yes
```
**待機メッセージ:**
```
Creating cognitive services account...
{
  "provisioningState": "Succeeded",
  "endpoint": "https://docnorm123456-docint.cognitiveservices.azure.com/"
}
```

### Step 5-3: エンドポイントとキー取得
```bash
# エンドポイント取得
DOCINT_ENDPOINT=$(az cognitiveservices account show \
  --name $DOCINT_NAME \
  --resource-group $RESOURCE_GROUP \
  --query 'properties.endpoint' -o tsv)

# APIキー取得
DOCINT_KEY=$(az cognitiveservices account keys list \
  --name $DOCINT_NAME \
  --resource-group $RESOURCE_GROUP \
  --query 'key1' -o tsv)

echo "✅ Document Intelligence設定完了"
echo "Endpoint: $DOCINT_ENDPOINT"
echo "Key: ${DOCINT_KEY:0:5}..." # セキュリティのため最初の5文字のみ表示
```

## ⚡ Step 6: Azure Functions作成

### Step 6-1: Function App作成（約3分かかります）
```bash
az functionapp create \
  --resource-group $RESOURCE_GROUP \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.9 \
  --functions-version 4 \
  --name $APP_NAME \
  --storage-account $STORAGE_ACCOUNT \
  --os-type Linux
```
**成功メッセージ:**
```json
{
  "state": "Running",
  "defaultHostName": "docnorm1234567890.azurewebsites.net",
  "kind": "functionapp,linux"
}
```

### Step 6-2: Function URL取得
```bash
FUNCTION_URL=$(az functionapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query 'defaultHostName' -o tsv)

echo "Function App URL: https://$FUNCTION_URL"
```

### Step 6-3: 環境変数設定
```bash
az functionapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    AzureWebJobsStorage="$STORAGE_CONNECTION" \
    DOCUMENT_INTELLIGENCE_ENDPOINT="$DOCINT_ENDPOINT" \
    DOCUMENT_INTELLIGENCE_API_KEY="$DOCINT_KEY" \
    STORAGE_CONNECTION_STRING="$STORAGE_CONNECTION" \
    FUNCTIONS_WORKER_RUNTIME="python"

echo "✅ 環境変数設定完了"
```

## 📦 Step 7: アプリケーションデプロイ

### Step 7-1: ローカル設定ファイル作成
```bash
cat > local.settings.json << EOF
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "$STORAGE_CONNECTION",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "DOCUMENT_INTELLIGENCE_ENDPOINT": "$DOCINT_ENDPOINT",
    "DOCUMENT_INTELLIGENCE_API_KEY": "$DOCINT_KEY",
    "STORAGE_CONNECTION_STRING": "$STORAGE_CONNECTION"
  }
}
EOF

echo "✅ local.settings.json作成完了"
```

### Step 7-2: デプロイ実行（約5分かかります）
```bash
# 仮想環境有効化
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# デプロイ実行
func azure functionapp publish $APP_NAME

# 出力例:
# Getting site publishing info...
# Creating archive for current directory...
# Uploading 10.5 MB [##############################################################################]
# Upload completed successfully.
# Deployment completed successfully.
# Syncing triggers...
# Functions in docnorm1234567890:
#     main_blob_trigger - [blobTrigger]
#     test_http - [httpTrigger]
```

### Step 7-3: デプロイ確認
```bash
# デプロイされた関数一覧
az functionapp function list \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output table
```

## ✅ Step 8: 動作確認

### Step 8-1: HTTPエンドポイントテスト
```bash
# テストURL構築
TEST_URL="https://$FUNCTION_URL/api/test_http"
echo "テストURL: $TEST_URL"

# curlでテスト
curl $TEST_URL
```
**期待される出力:**
```json
{
  "status": "success",
  "message": "Document Normalizer is running!",
  "features": [
    "PDF document classification",
    "Azure Document Intelligence integration",
    "CDM schema mapping",
    "Data validation and entity resolution"
  ],
  "config_status": {
    "schemas": "✅ Loaded",
    "mappings": "✅ Loaded",
    "validation_rules": "✅ Loaded",
    "vendor_patterns": "✅ Loaded"
  }
}
```

### Step 8-2: Azure Portalで確認
1. https://portal.azure.com にアクセス
2. 「Function App」を検索
3. 作成したアプリ名をクリック
4. 左メニューの「関数」をクリック
5. 関数一覧が表示されることを確認:
   - `main_blob_trigger` - PDFアップロード時に自動実行
   - `test_http` - HTTPテスト用エンドポイント

### Step 8-3: PDFアップロードテスト
```bash
# サンプルPDFをアップロード
az storage blob upload \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --container-name inbox \
  --name test-invoice.pdf \
  --file sample_invoice.pdf

echo "✅ PDFアップロード完了"

# 処理ログ確認（リアルタイム）
az functionapp log tail \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP

# 期待されるログ:
# [Information] Processing blob: test-invoice.pdf
# [Information] Document type: INVOICE
# [Information] Vendor: 株式会社サンプル
# [Information] Successfully processed test-invoice.pdf

# Ctrl+C で終了
```

### Step 8-4: 処理結果確認
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

## 💾 Step 9: 設定情報の保存

### Step 9-1: 重要情報を保存
```bash
cat > my-azure-config.txt << EOF
========================================
Document Normalizer - Azure設定情報
作成日: $(date)
========================================

【基本情報】
リソースグループ: $RESOURCE_GROUP
リージョン: $LOCATION
Function App名: $APP_NAME

【アクセスURL】
Function App: https://$FUNCTION_URL
HTTPテスト: https://$FUNCTION_URL/api/test_http
Azure Portal: https://portal.azure.com

【リソース名】
Storage Account: $STORAGE_ACCOUNT
Document Intelligence: $DOCINT_NAME

【コンテナ】
- inbox: PDFアップロード用
- processed: 処理済みファイル
- artifacts: 生成されたCDMファイル

【管理用コマンド】
# ログ確認
az functionapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP

# 再デプロイ
func azure functionapp publish $APP_NAME

# Function App停止
az functionapp stop --name $APP_NAME --resource-group $RESOURCE_GROUP

# Function App開始
az functionapp start --name $APP_NAME --resource-group $RESOURCE_GROUP

# PDFアップロード
az storage blob upload \\
  --account-name $STORAGE_ACCOUNT \\
  --account-key $STORAGE_KEY \\
  --container-name inbox \\
  --name [ファイル名] \\
  --file [ローカルファイルパス]

【費用確認】
Azure Portal > コストの管理と請求

【リソース削除（注意！すべて削除されます）】
# az group delete --name $RESOURCE_GROUP --yes

【注意】
この情報は機密情報です。安全に保管してください。
EOF

echo "✅ 設定情報をmy-azure-config.txtに保存しました"
```

### Step 9-2: Gitに設定ファイルを追加しない
```bash
# .gitignoreに追加
echo "my-azure-config.txt" >> .gitignore
echo "local.settings.json" >> .gitignore
echo "✅ 機密情報をGit管理から除外しました"
```

## 🎉 完了確認

### 最終チェックリスト
```bash
echo "===== デプロイ完了チェック ====="
echo "✅ リソースグループ: $RESOURCE_GROUP"
echo "✅ Storage Account: $STORAGE_ACCOUNT"
echo "✅ Document Intelligence: $DOCINT_NAME"
echo "✅ Function App: $APP_NAME"
echo "✅ URL: https://$FUNCTION_URL"
echo ""
echo "テストURL:"
echo "  https://$FUNCTION_URL/api/test_http"
echo ""
echo "PDFアップロード先:"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  コンテナ: inbox"
echo "================================"
```

## 🆘 困ったときは

### エラー: "Subscription not found"
```bash
# サブスクリプション一覧確認
az account list --output table

# 正しいサブスクリプションを設定
az account set --subscription "表示されたサブスクリプションID"
```

### エラー: "Name already taken"
```bash
# 別の名前で再試行
APP_NAME="docnorm$(date +%s)"
STORAGE_ACCOUNT="docnorm$RANDOM$RANDOM"
```

### エラー: "Deployment failed"
```bash
# Pythonバージョン確認
python --version

# 依存関係の再インストール
pip install -r requirements.txt

# リモートビルドで再試行
func azure functionapp publish $APP_NAME --build remote
```

### エラー: "PDF processing failed"
```bash
# Document Intelligenceの状態確認
az cognitiveservices account show \
  --name $DOCINT_NAME \
  --resource-group $RESOURCE_GROUP

# APIキーの再生成
az cognitiveservices account keys regenerate \
  --name $DOCINT_NAME \
  --resource-group $RESOURCE_GROUP \
  --key-name key1

# 新しいキーで環境変数を更新
DOCINT_KEY=$(az cognitiveservices account keys list \
  --name $DOCINT_NAME \
  --resource-group $RESOURCE_GROUP \
  --query 'key1' -o tsv)

az functionapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings DOCUMENT_INTELLIGENCE_API_KEY="$DOCINT_KEY"
```

### ログの詳細確認
```bash
# リアルタイムログ
az functionapp log tail \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP

# Application Insights（設定済みの場合）
az monitor app-insights query \
  --app "${APP_NAME}-insights" \
  --analytics-query "traces | where timestamp > ago(1h) | order by timestamp desc"
```

## 📊 コスト管理

### 現在の使用量確認
```bash
# リソースグループのコスト確認
az consumption usage list \
  --resource-group $RESOURCE_GROUP \
  --start-date $(date -d '30 days ago' '+%Y-%m-%d') \
  --end-date $(date '+%Y-%m-%d')
```

### 節約のヒント
1. **開発時はFunction Appを停止**
   ```bash
   az functionapp stop --name $APP_NAME --resource-group $RESOURCE_GROUP
   ```

2. **Document Intelligence無料枠の活用**
   - F0プラン: 月500ページまで無料（本番環境には不向き）

3. **Storage Accountのライフサイクル管理**
   - 古いファイルを自動削除する設定

## 🔄 日常的な運用

### PDFの処理方法
1. **Azure Portal経由**
   - Storage Accountを開く
   - inboxコンテナを選択
   - 「アップロード」ボタンでPDFアップロード

2. **コマンドライン経由**
   ```bash
   az storage blob upload \
     --account-name $STORAGE_ACCOUNT \
     --account-key $STORAGE_KEY \
     --container-name inbox \
     --name invoice001.pdf \
     --file /path/to/invoice001.pdf
   ```

3. **Azure Storage Explorer**
   - https://azure.microsoft.com/features/storage-explorer/
   - GUIでファイル管理可能

### 処理結果の確認
```bash
# CDMファイルをダウンロード
az storage blob download \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --container-name artifacts \
  --name "cdm_[ファイル名].json" \
  --file downloaded_cdm.json

# 内容確認
cat downloaded_cdm.json | python -m json.tool
```

## 🎯 次のステップ

1. **監視設定**
   - Application Insightsの設定
   - アラートルールの作成

2. **セキュリティ強化**
   - Key Vaultの導入
   - ネットワーク制限の設定

3. **自動化**
   - CI/CDパイプラインの構築
   - GitHub Actionsとの連携

4. **スケーリング**
   - Premium Planへの移行検討
   - 並列処理の最適化

## 📚 関連ドキュメント

- [ローカル実行ガイド](LOCAL_TESTING.md) - 開発環境での実行方法
- [設定ファイルガイド](CONFIGURATION.md) - カスタマイズ方法
- [日本語処理機能](JAPANESE_PROCESSING.md) - 和暦変換などの詳細
- [Azureデプロイメント](AZURE_DEPLOYMENT.md) - 簡易版デプロイガイド

---

**これで完全にAzure環境が構築されました！PDFをinboxコンテナにアップロードすると自動で処理が開始されます。**