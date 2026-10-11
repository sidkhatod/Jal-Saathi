import json
import pytest
from unittest.mock import patch, MagicMock
from upload_handler import handler

def test_upload_options_preflight():
    event = {
        "httpMethod": "OPTIONS"
    }
    resp = handler(event)
    assert resp["statusCode"] == 200
    assert "Access-Control-Allow-Origin" in resp["headers"]

def test_upload_missing_bucket():
    event = {
        "body": json.dumps({"field_id": "test-field"})
    }
    with patch.dict("os.environ", {}, clear=True):
        resp = handler(event)
        assert resp["statusCode"] == 500
        body = json.loads(resp["body"])
        assert "PHOTOS_BUCKET" in body["error"]

@patch("boto3.client")
@patch("boto3.resource")
def test_upload_success_generation(mock_boto_resource, mock_boto_client):
    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url.return_value = "https://s3.amazonaws.com/test-bucket/checkins/test?signature=abc"
    mock_boto_client.return_value = mock_s3

    mock_dynamo = MagicMock()
    mock_table = MagicMock()
    mock_dynamo.Table.return_value = mock_table
    mock_boto_resource.return_value = mock_dynamo

    event = {
        "body": json.dumps({
            "field_id": "field-demo-karnal-01",
            "file_name": "leaf_photo.jpg",
            "content_type": "image/jpeg"
        })
    }

    env = {
        "PHOTOS_BUCKET": "jal-saathi-photos-test",
        "OBSERVATIONS_TABLE": "jal-saathi-observations-test",
        "AWS_REGION": "ap-south-1"
    }

    with patch.dict("os.environ", env):
        resp = handler(event)
        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert "upload_url" in body
        assert "checkins/field-demo-karnal-01/" in body["s3_key"]
        assert body["expires_in"] == 900
        mock_s3.generate_presigned_url.assert_called_once()
        mock_table.put_item.assert_called_once()
