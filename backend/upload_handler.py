import os
import json
import uuid
import datetime
import boto3
from botocore.config import Config

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
}

def handler(event, context=None):
    """
    Lambda handler generating an S3 presigned PUT URL for farmer check-in photos.
    Records observation metadata into DynamoDB.
    """
    http_method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod")
    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": ""
        }

    try:
        body_raw = event.get("body")
        if isinstance(body_raw, str):
            payload = json.loads(body_raw)
        elif isinstance(body_raw, dict):
            payload = body_raw
        elif isinstance(event, dict) and "field_id" in event:
            payload = event
        else:
            payload = {}

        field_id = payload.get("field_id", "default-field")
        file_name = payload.get("file_name", "photo.jpg")
        content_type = payload.get("content_type", "image/jpeg")

        bucket_name = os.environ.get("PHOTOS_BUCKET")
        observations_table_name = os.environ.get("OBSERVATIONS_TABLE")
        region = os.environ.get("AWS_REGION", "ap-south-1")

        if not bucket_name:
            return {
                "statusCode": 500,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "PHOTOS_BUCKET environment variable is required"})
            }

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = os.path.basename(file_name)
        s3_key = f"checkins/{field_id}/{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')}_{unique_id}_{safe_filename}"

        # Initialize S3 client with regional signature config
        s3_client = boto3.client("s3", region_name=region, config=Config(signature_version="s3v4"))

        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket_name,
                "Key": s3_key,
                "ContentType": content_type
            },
            ExpiresIn=900 # 15 minutes
        )

        # Record observation metadata in DynamoDB if table is provided
        if observations_table_name:
            try:
                dynamodb = boto3.resource("dynamodb", region_name=region)
                table = dynamodb.Table(observations_table_name)
                table.put_item(
                    Item={
                        "plot_id": field_id,
                        "observation_timestamp": now_iso,
                        "s3_key": s3_key,
                        "status": "AWAITING_UPLOAD",
                        "content_type": content_type,
                        "created_at": now_iso
                    }
                )
            except Exception as db_err:
                # Log but continue to return the presigned url
                print(f"[WARN] Failed to write observation record: {db_err}")

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "upload_url": presigned_url,
                "s3_key": s3_key,
                "expires_in": 900,
                "field_id": field_id
            })
        }

    except Exception as exc:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(exc)})
        }
