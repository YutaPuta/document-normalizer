import logging
import os
import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigLoader:
    """設定ファイルのローダー"""
    
    def __init__(self, config_dir: str = None):
        """
        Args:
            config_dir: 設定ディレクトリのパス
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path(__file__).parent.parent / "config"
        
        self._cache = {}
        logger.info(f"ConfigLoader initialized with config_dir: {self.config_dir}")
    
    def get_cdm_schema(self, doc_type: str) -> Optional[Dict]:
        """CDMスキーマを取得"""
        cache_key = f"schema_{doc_type}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        schema_file = self.config_dir / "cdm" / f"{doc_type.lower()}.schema.json"
        
        if not schema_file.exists():
            logger.warning(f"Schema file not found: {schema_file}")
            return None
        
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                schema = json.load(f)
            
            self._cache[cache_key] = schema
            return schema
            
        except Exception as e:
            logger.error(f"Failed to load schema: {str(e)}")
            return None
    
    def get_mapping_config(self, doc_type: str, vendor_name: Optional[str] = None) -> Dict:
        """マッピング設定を取得"""
        mapping_config = {}
        
        global_config = self._load_yaml("mapping/global.yaml")
        if global_config:
            mapping_config.update(global_config)
        
        doc_type_config = self._load_yaml(f"mapping/doc_type/{doc_type}.yaml")
        if doc_type_config:
            mapping_config = self._merge_configs(mapping_config, doc_type_config)
        
        if vendor_name:
            vendor_config = self._load_yaml(f"mapping/vendors/{vendor_name}/{doc_type}.yaml")
            if vendor_config:
                mapping_config = self._merge_configs(mapping_config, vendor_config)
        
        return mapping_config
    
    def get_validation_rules(self) -> Dict:
        """検証ルールを取得"""
        cache_key = "validation_rules"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        rules = self._load_yaml("validation/rules.yaml") or {}
        
        self._cache[cache_key] = rules
        return rules
    
    def get_vendor_config(self) -> Dict:
        """ベンダー分類設定を取得"""
        cache_key = "vendor_config"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        config = self._load_yaml("classifier/vendors.yaml") or {}
        
        self._cache[cache_key] = config
        return config
    
    def get_entity_dictionary(self) -> Dict:
        """エンティティ辞書を取得"""
        cache_key = "entity_dictionary"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        dictionary = self._load_yaml("entity/dictionary.yaml") or {}
        
        self._cache[cache_key] = dictionary
        return dictionary
    
    def _load_yaml(self, relative_path: str) -> Optional[Dict]:
        """YAMLファイルを読み込む"""
        file_path = self.config_dir / relative_path
        
        if not file_path.exists():
            logger.debug(f"YAML file not found: {file_path}")
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            logger.debug(f"Loaded YAML: {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to load YAML {file_path}: {str(e)}")
            return None
    
    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """設定をマージ（深いマージ）"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._merge_configs(result[key], value)
                elif isinstance(result[key], list) and isinstance(value, list):
                    result[key] = result[key] + value
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    def reload(self):
        """設定キャッシュをクリアして再読み込み"""
        self._cache.clear()
        logger.info("Configuration cache cleared")
    
    def list_vendor_mappings(self) -> list:
        """利用可能なベンダーマッピングをリスト"""
        vendors_dir = self.config_dir / "mapping" / "vendors"
        
        if not vendors_dir.exists():
            return []
        
        vendors = []
        for vendor_dir in vendors_dir.iterdir():
            if vendor_dir.is_dir():
                vendor_name = vendor_dir.name
                mappings = []
                
                for mapping_file in vendor_dir.glob("*.yaml"):
                    doc_type = mapping_file.stem
                    mappings.append(doc_type)
                
                if mappings:
                    vendors.append({
                        "vendor": vendor_name,
                        "mappings": mappings
                    })
        
        return vendors
    
    def validate_config(self) -> Dict[str, list]:
        """設定の整合性を検証"""
        issues = {
            "errors": [],
            "warnings": []
        }
        
        schema_dir = self.config_dir / "cdm"
        if not schema_dir.exists():
            issues["errors"].append("CDM schema directory not found")
        
        global_mapping = self.config_dir / "mapping" / "global.yaml"
        if not global_mapping.exists():
            issues["warnings"].append("Global mapping configuration not found")
        
        validation_rules = self.config_dir / "validation" / "rules.yaml"
        if not validation_rules.exists():
            issues["warnings"].append("Validation rules not found")
        
        for doc_type in ["INVOICE", "PURCHASE_ORDER"]:
            schema_file = self.config_dir / "cdm" / f"{doc_type.lower()}.schema.json"
            if not schema_file.exists():
                issues["errors"].append(f"Schema for {doc_type} not found")
            
            mapping_file = self.config_dir / "mapping" / "doc_type" / f"{doc_type}.yaml"
            if not mapping_file.exists():
                issues["warnings"].append(f"Default mapping for {doc_type} not found")
        
        return issues