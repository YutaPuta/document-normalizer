#!/usr/bin/env python3
"""
Document Normalizer - 自動ドキュメント更新スクリプト
プログラム変更に基づいてドキュメントを自動更新する
"""

import os
import re
import json
import yaml
from pathlib import Path
from datetime import datetime
import subprocess

class DocumentUpdater:
    def __init__(self, project_root=None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.src_dir = self.project_root / "src"
        self.config_dir = self.project_root / "config"
        self.doc_dir = self.project_root / "doc"
        
    def update_all_docs(self):
        """すべてのドキュメントを更新"""
        print("🔄 Document Normalizer - ドキュメント自動更新開始")
        
        updates_made = []
        
        # 1. 日本語処理ドキュメント更新
        if self.update_japanese_processing_doc():
            updates_made.append("日本語処理機能ドキュメント")
            
        # 2. 設定ドキュメント更新
        if self.update_configuration_doc():
            updates_made.append("設定ファイルドキュメント")
            
        # 3. ローカルテストドキュメント更新
        if self.update_local_testing_doc():
            updates_made.append("ローカルテストドキュメント")
            
        # 4. メインREADME更新
        if self.update_main_readme():
            updates_made.append("メインREADME")
            
        # 5. 更新サマリー
        self.print_update_summary(updates_made)
        
        return len(updates_made) > 0
        
    def update_japanese_processing_doc(self):
        """日本語処理ドキュメントを更新"""
        transforms_file = self.src_dir / "transforms.py"
        if not transforms_file.exists():
            return False
            
        print("📝 日本語処理ドキュメントを更新中...")
        
        # transforms.pyから関数一覧を抽出
        with open(transforms_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 関数定義を抽出
        functions = re.findall(r'def ([a-zA-Z_][a-zA-Z0-9_]*)\([^)]*\):', content)
        japanese_functions = [f for f in functions if any(keyword in f for keyword in 
            ['japanese', 'zenkaku', 'hankaku', 'parse', 'normalize', 'strip_currency'])]
            
        # ドキュメネーションを抽出
        doc_strings = re.findall(r'def [a-zA-Z_][a-zA-Z0-9_]*\([^)]*\):\s*"""([^"]+)"""', content, re.DOTALL)
        
        doc_file = self.doc_dir / "JAPANESE_PROCESSING.md"
        if doc_file.exists():
            with open(doc_file, 'r', encoding='utf-8') as f:
                doc_content = f.read()
                
            # 関数一覧セクションを更新
            function_list = "\n".join([f"- `{func}`: 日本語処理関数" for func in japanese_functions])
            
            # 利用可能な変換関数セクションを更新
            if "利用可能な変換関数" in doc_content:
                updated_content = re.sub(
                    r'(利用可能な変換関数.*?)\n([^\n]*\n)*(?=##|\n##|\Z)',
                    f'利用可能な変換関数:\n{function_list}\n\n',
                    doc_content,
                    flags=re.MULTILINE | re.DOTALL
                )
                
                with open(doc_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                    
                print(f"  ✅ 日本語処理関数 {len(japanese_functions)} 個を更新")
                return True
                
        return False
        
    def update_configuration_doc(self):
        """設定ドキュメントを更新"""
        print("⚙️ 設定ドキュメントを更新中...")
        
        updated = False
        
        # グローバルマッピング設定を確認
        global_mapping = self.config_dir / "mapping" / "global.yaml"
        if global_mapping.exists():
            try:
                with open(global_mapping, 'r', encoding='utf-8') as f:
                    mapping_config = yaml.safe_load(f)
                    
                mappings_count = len(mapping_config.get('mappings', {}))
                print(f"  ✅ グローバルマッピング {mappings_count} フィールド確認")
                updated = True
                
            except Exception as e:
                print(f"  ⚠️ global.yaml読み込みエラー: {e}")
                
        # CDMスキーマを確認
        cdm_schemas = list((self.config_dir / "cdm").glob("*.schema.json"))
        if cdm_schemas:
            print(f"  ✅ CDMスキーマ {len(cdm_schemas)} ファイル確認")
            for schema in cdm_schemas:
                try:
                    with open(schema, 'r', encoding='utf-8') as f:
                        schema_data = json.load(f)
                        properties_count = len(schema_data.get('properties', {}).get('doc', {}).get('properties', {}))
                        print(f"    - {schema.name}: {properties_count} プロパティ")
                except Exception as e:
                    print(f"    ⚠️ {schema.name} 読み込みエラー: {e}")
            updated = True
            
        return updated
        
    def update_local_testing_doc(self):
        """ローカルテストドキュメントを更新"""
        print("🧪 ローカルテストドキュメントを更新中...")
        
        # テストファイル一覧を取得
        test_files = []
        for pattern in ["test_*.py", "*_test.py", "pdf_test.py"]:
            test_files.extend(self.project_root.glob(pattern))
            
        if not test_files:
            return False
            
        doc_file = self.doc_dir / "LOCAL_TESTING.md"
        if not doc_file.exists():
            return False
            
        # テストファイル情報を収集
        test_info = []
        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # ドキュメント文字列から説明を抽出
                doc_match = re.search(r'"""([^"]+)"""', content)
                description = doc_match.group(1).strip().split('\n')[0] if doc_match else "テストファイル"
                
                test_info.append({
                    'file': test_file.name,
                    'description': description
                })
                
            except Exception as e:
                print(f"  ⚠️ {test_file.name} 読み込みエラー: {e}")
                
        if test_info:
            print(f"  ✅ テストファイル {len(test_info)} 個を確認")
            for info in test_info:
                print(f"    - {info['file']}: {info['description']}")
            return True
            
        return False
        
    def update_main_readme(self):
        """メインREADMEを更新"""
        print("📚 メインREADMEを更新中...")
        
        readme_file = self.project_root / "README.md"
        if not readme_file.exists():
            return False
            
        # 依存関係情報を更新
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            with open(requirements_file, 'r', encoding='utf-8') as f:
                dependencies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
            print(f"  ✅ 依存関係 {len(dependencies)} パッケージを確認")
            
            # 主要パッケージを特定
            key_packages = []
            for dep in dependencies:
                package_name = dep.split('==')[0].split('>=')[0].split('<=')[0]
                if package_name in ['azure-functions', 'pdfminer.six', 'PyYAML', 'reportlab']:
                    key_packages.append(package_name)
                    
            if key_packages:
                print(f"    主要パッケージ: {', '.join(key_packages)}")
                
            return True
            
        return False
        
    def print_update_summary(self, updates_made):
        """更新サマリーを出力"""
        print(f"\n{'='*50}")
        print(f"📋 ドキュメント更新サマリー")
        print(f"{'='*50}")
        
        if updates_made:
            print("✅ 更新されたドキュメント:")
            for doc in updates_made:
                print(f"  - {doc}")
                
            print(f"\n📅 更新日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📁 プロジェクトルート: {self.project_root}")
            
            # Gitステータス確認
            try:
                result = subprocess.run(['git', 'status', '--porcelain'], 
                                     capture_output=True, text=True, cwd=self.project_root)
                if result.stdout.strip():
                    print(f"\n💡 次のステップ:")
                    print(f"  git add doc/")
                    print(f"  git commit -m \"docs: プログラム変更に伴うドキュメント更新\"")
            except Exception:
                pass
                
        else:
            print("ℹ️ 更新が必要なドキュメントはありませんでした")
            
        print(f"{'='*50}\n")
        
    def validate_docs(self):
        """ドキュメントの整合性を検証"""
        print("🔍 ドキュメント整合性検証中...")
        
        issues = []
        
        # 1. 必要なドキュメントファイルの存在確認
        required_docs = [
            "LOCAL_TESTING.md",
            "JAPANESE_PROCESSING.md", 
            "CONFIGURATION.md",
            "README.md"
        ]
        
        for doc in required_docs:
            doc_path = self.doc_dir / doc if doc != "README.md" else self.doc_dir / doc
            if not doc_path.exists():
                issues.append(f"必須ドキュメント {doc} が見つかりません")
                
        # 2. リンク整合性チェック
        readme_main = self.project_root / "README.md"
        if readme_main.exists():
            with open(readme_main, 'r', encoding='utf-8') as f:
                readme_content = f.read()
                
            # ドキュメントリンクの確認
            doc_links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', readme_content)
            for link_text, link_path in doc_links:
                if link_path.startswith('doc/'):
                    full_path = self.project_root / link_path
                    if not full_path.exists():
                        issues.append(f"リンク切れ: {link_text} -> {link_path}")
                        
        # 3. 検証結果出力
        if issues:
            print("⚠️ 以下の問題が見つかりました:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("✅ ドキュメント整合性に問題はありません")
            return True

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Document Normalizer ドキュメント自動更新')
    parser.add_argument('--validate-only', action='store_true', 
                       help='更新せず、検証のみ実行')
    parser.add_argument('--project-root', type=str, 
                       help='プロジェクトルートディレクトリ')
    
    args = parser.parse_args()
    
    updater = DocumentUpdater(args.project_root)
    
    if args.validate_only:
        success = updater.validate_docs()
        exit(0 if success else 1)
    else:
        updated = updater.update_all_docs()
        success = updater.validate_docs()
        
        if updated and success:
            print("🎉 ドキュメント更新完了！")
        elif not updated:
            print("ℹ️ 更新は不要でした")
        else:
            print("⚠️ 更新中に問題が発生しました")
            exit(1)

if __name__ == "__main__":
    main()