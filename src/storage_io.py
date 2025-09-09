import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.cosmos import CosmosClient, PartitionKey

logger = logging.getLogger(__name__)

def save_artifacts(
    blob_name: str,
    raw_data: Dict,
    cdm_data: Optional[Dict],
    validation_report: Dict,
    container: str = "artifacts"
) -> None:
    """
    処理結果をBlob Storageに保存
    
    Args:
        blob_name: 元のBLOB名
        raw_data: 生抽出データ
        cdm_data: CDM形式データ
        validation_report: 検証レポート
        container: 保存先コンテナ名
    """
    try:
        blob_service_client = get_blob_service_client()
        
        base_name = os.path.splitext(blob_name)[0]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        save_json_to_blob(
            blob_service_client,
            container,
            f"{base_name}/raw_{timestamp}.json",
            raw_data
        )
        logger.info(f"Saved raw data for {blob_name}")
        
        if cdm_data:
            save_json_to_blob(
                blob_service_client,
                container,
                f"{base_name}/cdm_{timestamp}.json",
                cdm_data
            )
            logger.info(f"Saved CDM data for {blob_name}")
        
        save_json_to_blob(
            blob_service_client,
            container,
            f"{base_name}/validation_{timestamp}.json",
            validation_report
        )
        logger.info(f"Saved validation report for {blob_name}")
        
        audit_log = {
            "blob_name": blob_name,
            "processed_at": datetime.utcnow().isoformat(),
            "success": cdm_data is not None,
            "error_count": len(validation_report.get("errors", [])),
            "warning_count": len(validation_report.get("warnings", []))
        }
        save_json_to_blob(
            blob_service_client,
            container,
            f"{base_name}/audit_{timestamp}.json",
            audit_log
        )
        
    except Exception as e:
        logger.error(f"Failed to save artifacts: {str(e)}", exc_info=True)

def save_json_to_blob(
    blob_service_client: BlobServiceClient,
    container: str,
    blob_path: str,
    data: Dict
) -> None:
    """JSONデータをBlobに保存"""
    try:
        container_client = blob_service_client.get_container_client(container)
        
        try:
            container_client.get_container_properties()
        except Exception:
            container_client.create_container()
            logger.info(f"Created container: {container}")
        
        blob_client = container_client.get_blob_client(blob_path)
        
        json_content = json.dumps(data, ensure_ascii=False, indent=2)
        
        blob_client.upload_blob(
            json_content,
            overwrite=True,
            content_settings=ContentSettings(content_type="application/json")
        )
        
        logger.debug(f"Uploaded JSON to {container}/{blob_path}")
        
    except Exception as e:
        logger.error(f"Failed to save JSON to blob: {str(e)}", exc_info=True)
        raise

def save_to_cosmos(cdm_data: Dict) -> None:
    """
    CDMデータをCosmos DBに保存
    
    Args:
        cdm_data: 保存するCDM形式のデータ
    """
    try:
        cosmos_client = get_cosmos_client()
        if not cosmos_client:
            logger.warning("Cosmos DB not configured, skipping save")
            return
        
        database_name = os.environ.get("COSMOS_DB_DATABASE", "DocumentProcessing")
        container_name = os.environ.get("COSMOS_DB_CONTAINER", "Documents")
        
        database = cosmos_client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        document = prepare_cosmos_document(cdm_data)
        
        container.upsert_item(document)
        
        logger.info(f"Saved document to Cosmos DB: {document['id']}")
        
    except Exception as e:
        logger.error(f"Failed to save to Cosmos DB: {str(e)}", exc_info=True)

def prepare_cosmos_document(cdm_data: Dict) -> Dict:
    """Cosmos DB用にドキュメントを準備"""
    doc = cdm_data.get("doc", {})
    
    document = {
        "id": generate_document_id(cdm_data),
        "partitionKey": doc.get("vendor", "unknown"),
        "docType": doc.get("type"),
        "documentNo": doc.get("document_no"),
        "issueDate": doc.get("issue_date"),
        "dueDate": doc.get("due_date"),
        "vendor": doc.get("vendor"),
        "vendorId": doc.get("vendor_id"),
        "customerId": doc.get("customer_id"),
        "currency": doc.get("currency"),
        "totals": cdm_data.get("totals", {}),
        "lineItemCount": len(cdm_data.get("lines", [])),
        "extractionTimestamp": doc.get("extraction_timestamp"),
        "createdAt": datetime.utcnow().isoformat(),
        "metadata": cdm_data.get("metadata", {}),
        "fullDocument": cdm_data
    }
    
    return document

def generate_document_id(cdm_data: Dict) -> str:
    """ドキュメントIDを生成"""
    doc = cdm_data.get("doc", {})
    doc_type = doc.get("type", "UNKNOWN")
    doc_no = doc.get("document_no", "")
    vendor = doc.get("vendor", "unknown")
    
    if doc_no and vendor:
        return f"{doc_type}_{vendor}_{doc_no}".replace(" ", "_")
    else:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"{doc_type}_{timestamp}"

def get_blob_service_client() -> BlobServiceClient:
    """Blob Service Clientを取得"""
    connection_string = os.environ.get("AzureWebJobsStorage")
    
    if not connection_string or connection_string == "UseDevelopmentStorage=true":
        logger.warning("Using development storage emulator")
        connection_string = (
            "DefaultEndpointsProtocol=http;"
            "AccountName=devstoreaccount1;"
            "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
            "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
        )
    
    return BlobServiceClient.from_connection_string(connection_string)

def get_cosmos_client() -> Optional[CosmosClient]:
    """Cosmos Clientを取得"""
    endpoint = os.environ.get("COSMOS_DB_ENDPOINT")
    key = os.environ.get("COSMOS_DB_KEY")
    
    if not endpoint or not key:
        return None
    
    return CosmosClient(endpoint, key)

def read_blob(container: str, blob_path: str) -> bytes:
    """Blobからデータを読み込む"""
    try:
        blob_service_client = get_blob_service_client()
        blob_client = blob_service_client.get_blob_client(
            container=container,
            blob=blob_path
        )
        
        return blob_client.download_blob().readall()
        
    except Exception as e:
        logger.error(f"Failed to read blob {container}/{blob_path}: {str(e)}")
        raise

def list_blobs(container: str, prefix: str = "") -> list:
    """Blob一覧を取得"""
    try:
        blob_service_client = get_blob_service_client()
        container_client = blob_service_client.get_container_client(container)
        
        blobs = []
        for blob in container_client.list_blobs(name_starts_with=prefix):
            blobs.append({
                "name": blob.name,
                "size": blob.size,
                "last_modified": blob.last_modified.isoformat() if blob.last_modified else None
            })
        
        return blobs
        
    except Exception as e:
        logger.error(f"Failed to list blobs: {str(e)}")
        return []

def move_blob(source_container: str, source_path: str, dest_container: str, dest_path: str) -> bool:
    """Blobを移動"""
    try:
        blob_service_client = get_blob_service_client()
        
        source_blob = blob_service_client.get_blob_client(
            container=source_container,
            blob=source_path
        )
        dest_blob = blob_service_client.get_blob_client(
            container=dest_container,
            blob=dest_path
        )
        
        dest_blob.start_copy_from_url(source_blob.url)
        
        source_blob.delete_blob()
        
        logger.info(f"Moved blob from {source_container}/{source_path} to {dest_container}/{dest_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to move blob: {str(e)}")
        return False