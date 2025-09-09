# Document Normalizer ドキュメント

Document Normalizerの詳細ドキュメント集です。

## 📚 ドキュメント一覧

### 🚀 はじめに
- **[メインREADME](../README.md)** - プロジェクト概要と基本使用方法

### 💻 開発・テスト
- **[ローカル実行ガイド](LOCAL_TESTING.md)** - ローカル環境での実行・テスト方法
- **[日本語処理機能](JAPANESE_PROCESSING.md)** - 和暦変換、全角半角変換など日本語特有処理
- **[設定ファイルガイド](CONFIGURATION.md)** - YAML設定、CDMスキーマ、マッピングルール

### ☁️ 本番環境
- **[Azureデプロイメント](AZURE_DEPLOYMENT.md)** - Azure環境への本番デプロイ
- **[CDMスキーマ仕様](CDM_SCHEMA.md)** - 出力データ形式とスキーマ詳細

## 🎯 用途別ドキュメント

### 初回セットアップ
1. [メインREADME](../README.md) - 概要理解
2. [ローカル実行ガイド](LOCAL_TESTING.md) - 環境構築とテスト

### 機能カスタマイズ
1. [設定ファイルガイド](CONFIGURATION.md) - マッピング設定
2. [日本語処理機能](JAPANESE_PROCESSING.md) - 変換関数追加

### 本番運用
1. [Azureデプロイメント](AZURE_DEPLOYMENT.md) - 本番環境構築
2. [CDMスキーマ仕様](CDM_SCHEMA.md) - データ仕様確認

## 🔍 よくある質問

### Q: まず何から始めれば良いですか？
A: [ローカル実行ガイド](LOCAL_TESTING.md)の環境セットアップから始めてください。

### Q: 新しいベンダーに対応したいのですが？
A: [設定ファイルガイド](CONFIGURATION.md)のベンダー固有マッピング設定を参照してください。

### Q: 日本語の和暦変換がうまくいきません
A: [日本語処理機能](JAPANESE_PROCESSING.md)のトラブルシューティング部分を確認してください。

### Q: Azure環境にデプロイしたいのですが？
A: [Azureデプロイメント](AZURE_DEPLOYMENT.md)の手順に従ってください。

### Q: 出力されるJSONの形式を知りたいのですが？
A: [CDMスキーマ仕様](CDM_SCHEMA.md)で詳細なスキーマ定義を確認できます。

## 🛠️ 開発支援

### ドキュメント更新
このドキュメントは実装と同期して更新されます。不整合を見つけた場合はIssueを報告してください。

### 貢献方法
1. ドキュメントの改善提案
2. サンプルコードの追加
3. FAQ項目の追加
4. 多言語対応の翻訳

### フィードバック
- GitHub Issues: バグ報告・機能要求
- Pull Requests: 改善コードの提案
- Discussions: 使用方法の質問

## 📄 ライセンス

MIT License - 詳細は [../LICENSE](../LICENSE) を参照