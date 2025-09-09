# Gitフック ガイド

Document Normalizerのプログラム更新時に自動でドキュメントを同期するGitフックシステムの説明です。

## 📋 概要

プログラムコードを変更した際に、関連するドキュメントが自動で更新・チェックされるシステムを導入しています。

### 🔧 導入済みフック

1. **Pre-commit Hook** - コミット前にドキュメント更新が必要かチェック
2. **Post-commit Hook** - コミット後にドキュメント同期状況を確認
3. **自動更新スクリプト** - ドキュメントの自動更新機能

## 🚀 フックの動作

### Pre-commit Hook (コミット前)

**トリガー**: `git commit` 実行時

**動作内容**:
- 変更されたファイルを分析
- 以下のファイル変更時にドキュメント更新を警告:
  - `src/transforms.py` → `doc/JAPANESE_PROCESSING.md`
  - `src/config_loader.py` → `doc/CONFIGURATION.md`  
  - `src/pipeline.py` → `doc/LOCAL_TESTING.md`
  - `config/` 配下 → `doc/CONFIGURATION.md`
  - テストファイル → `doc/LOCAL_TESTING.md`
  - `requirements.txt` → `README.md`, `doc/LOCAL_TESTING.md`

**実行例**:
```bash
$ git commit -m "Add new transform function"

🔍 Document Normalizer - Pre-commit Hook実行中...
📝 以下のファイルが変更されました:
  - src/transforms.py

🔧 src/配下の変更を検出 - 機能ドキュメントをチェック中...
  📋 transforms.py変更 - 日本語処理ドキュメント更新が必要
    ✅ 日本語処理関数が検出されました
    ⚠️  doc/JAPANESE_PROCESSING.md の更新を確認してください

📚 メインREADME.mdの更新チェック...
⚠️  プログラム変更に伴いREADME.mdの更新も検討してください

💡 ヒント: ドキュメント更新を自動化したい場合は以下を実行:
   python scripts/update_docs.py

🎉 Pre-commit Hook完了 - コミットを継続します
```

### Post-commit Hook (コミット後)

**トリガー**: `git commit` 完了後

**動作内容**:
- コミットされた変更を分析
- ドキュメント同期状況を検証
- 更新推奨事項を表示

**実行例**:
```bash
📋 Document Normalizer - Post-commit Hook実行中...
📝 コミットされた変更:
  - src/transforms.py

🔍 ドキュメント同期状況を確認中...
⚠️  ドキュメントの更新が推奨されます
💡 以下のコマンドでドキュメントを更新できます:
   python scripts/update_docs.py

🎉 Post-commit Hook完了
```

## 🤖 自動更新スクリプト

### scripts/update_docs.py

**機能**: プログラム変更に基づいてドキュメントを自動更新

**使用方法**:
```bash
# 全ドキュメントを自動更新
python scripts/update_docs.py

# 検証のみ実行（更新なし）
python scripts/update_docs.py --validate-only

# プロジェクトルート指定
python scripts/update_docs.py --project-root /path/to/project
```

**更新対象**:
1. **日本語処理ドキュメント** (`doc/JAPANESE_PROCESSING.md`)
   - `src/transforms.py` から関数一覧を抽出
   - 新しい変換関数を自動検出
   - 関数説明の同期

2. **設定ドキュメント** (`doc/CONFIGURATION.md`)
   - `config/mapping/global.yaml` からマッピング数を取得
   - CDMスキーマファイルの構造確認
   - 設定例の更新

3. **ローカルテストドキュメント** (`doc/LOCAL_TESTING.md`)
   - テストファイル一覧の自動更新
   - テストファイルの説明同期

4. **メインREADME** (`README.md`)
   - `requirements.txt` から依存関係情報を取得
   - 主要パッケージの同期

### 実行例

```bash
$ python scripts/update_docs.py

🔄 Document Normalizer - ドキュメント自動更新開始
📝 日本語処理ドキュメントを更新中...
  ✅ 日本語処理関数 8 個を更新
⚙️ 設定ドキュメントを更新中...
  ✅ グローバルマッピング 9 フィールド確認
  ✅ CDMスキーマ 2 ファイル確認
    - invoice.schema.json: 12 プロパティ
    - purchase_order.schema.json: 10 プロパティ
🧪 ローカルテストドキュメントを更新中...
  ✅ テストファイル 6 個を確認
    - test_with_text.py: テキスト処理機能テスト
    - pdf_test.py: PDFファイルを使った簡易テスト
📚 メインREADMEを更新中...
  ✅ 依存関係 15 パッケージを確認
    主要パッケージ: azure-functions, pdfminer.six, PyYAML, reportlab

==================================================
📋 ドキュメント更新サマリー
==================================================
✅ 更新されたドキュメント:
  - 日本語処理機能ドキュメント
  - 設定ファイルドキュメント
  - ローカルテストドキュメント
  - メインREADME

📅 更新日時: 2024-01-15 14:30:22
📁 プロジェクトルート: /Users/.../doc-normalizer

💡 次のステップ:
  git add doc/
  git commit -m "docs: プログラム変更に伴うドキュメント更新"
==================================================

🔍 ドキュメント整合性検証中...
✅ ドキュメント整合性に問題はありません
🎉 ドキュメント更新完了！
```

## 🔧 カスタマイズ

### フック設定のカスタマイズ

#### 新しい監視ファイルパターンの追加

`.git/hooks/pre-commit` を編集:

```bash
# 新しいファイルパターンを追加
NEW_PATTERN_CHANGED=$(echo "$CHANGED_FILES" | grep -E '^custom_module/' || true)

if [[ -n "$NEW_PATTERN_CHANGED" ]]; then
    echo -e "${BLUE}  📋 custom_module変更 - カスタムドキュメント更新が必要${NC}"
    DOCS_UPDATED=true
    echo -e "    ${YELLOW}⚠️  doc/CUSTOM_MODULE.md の更新を確認してください${NC}"
fi
```

#### ドキュメント検証ルールの追加

`scripts/update_docs.py` の `validate_docs` メソッドを拡張:

```python
def validate_docs(self):
    # 既存の検証に加えて
    
    # カスタム検証ルール追加
    custom_files = list(self.project_root.glob("custom_*.py"))
    if custom_files:
        custom_doc = self.doc_dir / "CUSTOM_FEATURES.md"
        if not custom_doc.exists():
            issues.append("カスタム機能のドキュメントが見つかりません")
```

### 自動更新ルールの追加

新しいドキュメント更新ロジックを追加:

```python
def update_custom_doc(self):
    """カスタムドキュメントを更新"""
    print("🔧 カスタムドキュメントを更新中...")
    
    # カスタム実装を追加
    custom_files = list(self.src_dir.glob("custom_*.py"))
    
    if custom_files:
        print(f"  ✅ カスタムファイル {len(custom_files)} 個を確認")
        return True
        
    return False
```

## 🛠️ トラブルシューティング

### よくある問題と解決法

#### 1. フックが実行されない

```bash
# フックファイルの実行権限を確認
ls -la .git/hooks/pre-commit
ls -la .git/hooks/post-commit

# 実行権限がない場合は付与
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/post-commit
```

#### 2. Python スクリプトエラー

```bash
# Python環境の確認
which python
python --version

# 必要なモジュールの確認
python -c "import yaml, json, pathlib"

# 仮想環境の確認
source .venv/bin/activate  # 仮想環境有効化
```

#### 3. ドキュメント更新スクリプトエラー

```bash
# スクリプトの実行権限確認
chmod +x scripts/update_docs.py

# 依存関係の確認
pip install PyYAML

# デバッグモードで実行
python scripts/update_docs.py --validate-only
```

#### 4. Gitフック無効化（一時的）

```bash
# 一時的にフックをスキップしてコミット
git commit --no-verify -m "Commit message"

# フックを完全に無効化（非推奨）
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled
```

### パフォーマンス最適化

#### フック実行時間の短縮

- 変更されたファイルのみを対象とする（既に実装済み）
- 大きなファイルのスキップ
- 並列処理の導入

#### ドキュメント更新の最適化

- 差分更新のみ実行
- キャッシュ機能の追加
- 増分更新の実装

## 📚 関連コマンド

### 手動でのフック実行

```bash
# Pre-commit フックのテスト実行
.git/hooks/pre-commit

# Post-commit フックのテスト実行  
.git/hooks/post-commit

# ドキュメント更新の手動実行
python scripts/update_docs.py
```

### フック管理コマンド

```bash
# 現在のフック一覧
ls -la .git/hooks/

# フックのバックアップ
cp -r .git/hooks/ .git/hooks.backup/

# フックの復元
cp -r .git/hooks.backup/* .git/hooks/
```

## 🎯 ベストプラクティス

### 1. 開発ワークフロー

1. コード変更を実装
2. ローカルテスト実行
3. `git add` で変更をステージング
4. `git commit` でコミット（フック自動実行）
5. フックの警告に基づいてドキュメント更新
6. ドキュメントもコミット

### 2. ドキュメント同期の確認

```bash
# 定期的にドキュメント同期状況をチェック
python scripts/update_docs.py --validate-only

# プルリクエスト前の最終確認
python scripts/update_docs.py
```

### 3. チーム開発での注意点

- フックはローカル設定のため、チームメンバー全員での設定が必要
- 新規メンバーのオンボーディング時にフック設定を含める
- CI/CDパイプラインでドキュメント同期確認を実装

## 📋 チェックリスト

### 初回設定時
- [ ] `.git/hooks/pre-commit` 実行権限確認
- [ ] `.git/hooks/post-commit` 実行権限確認  
- [ ] `scripts/update_docs.py` 実行権限確認
- [ ] Python仮想環境の確認
- [ ] 必要なPythonモジュールのインストール
- [ ] テスト実行でフック動作確認

### 運用時
- [ ] コミット前のローカルテスト実行
- [ ] フック警告への対応
- [ ] 定期的なドキュメント同期確認
- [ ] 新機能追加時のドキュメント更新ルール追加

フックシステムにより、プログラム変更とドキュメント更新の同期が自動化され、常に最新のドキュメントが維持されます。