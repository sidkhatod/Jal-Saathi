import os
import pytest
import boto3
from moto import mock_aws
import urllib.parse
import hmac
import hashlib
from twilio.request_validator import RequestValidator

# Set env vars before importing webhook
os.environ['ENV'] = 'test'
os.environ['AWS_REGION'] = 'ap-south-1'
os.environ['TWILIO_SECRET_ARN'] = 'arn:aws:secretsmanager:ap-south-1:123456789012:secret:test-secret'
os.environ['PLACE_INDEX_NAME'] = 'test-index'
os.environ['FARMS_TABLE'] = 'jal-saathi-farms-test'
os.environ['PLOTS_TABLE'] = 'jal-saathi-plots-test'
os.environ['OBSERVATIONS_TABLE'] = 'jal-saathi-observations-test'
os.environ['PHOTOS_BUCKET'] = 'jal-saathi-photos-test'

from webhook import handler, adapter, get_farmer_id

@pytest.fixture
def aws_setup():
    with mock_aws():
        # DynamoDB
        dynamodb = boto3.client('dynamodb', region_name='ap-south-1')
        dynamodb.create_table(
            TableName=os.environ['FARMS_TABLE'],
            KeySchema=[{'AttributeName': 'farmer_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'farmer_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        dynamodb.create_table(
            TableName=os.environ['OBSERVATIONS_TABLE'],
            KeySchema=[
                {'AttributeName': 'plot_id', 'KeyType': 'HASH'},
                {'AttributeName': 'observation_timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'plot_id', 'AttributeType': 'S'},
                {'AttributeName': 'observation_timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # SecretsManager
        secretsmanager = boto3.client('secretsmanager', region_name='ap-south-1')
        secretsmanager.create_secret(
            Name=os.environ['TWILIO_SECRET_ARN'],
            SecretString='{"TWILIO_ACCOUNT_SID": "ACtest", "TWILIO_AUTH_TOKEN": "token", "TWILIO_SECRET_KEY": "secret"}'
        )
        
        yield

def make_event(body_dict, path="/", validate=False):
    body = urllib.parse.urlencode(body_dict)
    
    headers = {
        "host": "test.lambda-url.ap-south-1.on.aws",
        "x-forwarded-proto": "https"
    }
    
    if validate:
        # Generate valid signature
        validator = RequestValidator("token")
        url = f"https://{headers['host']}{path}"
        signature = validator.compute_signature(url, body_dict)
        headers["x-twilio-signature"] = signature
    
    return {
        "rawPath": path,
        "headers": headers,
        "body": body,
        "isBase64Encoded": False,
        "_testing": not validate
    }

def test_signature_validation(aws_setup):
    event = make_event({"From": "whatsapp:+1234567890", "Body": "hi"}, validate=True)
    # Remove _testing flag to test signature
    event['_testing'] = False
    
    res = handler(event, None)
    assert res['statusCode'] == 200
    
    # Test invalid signature
    event['headers']['x-twilio-signature'] = 'invalid'
    res = handler(event, None)
    assert res['statusCode'] == 401

def test_onboarding_walkthrough(aws_setup, mocker):
    mock_send = mocker.patch('webhook.TwilioAdapter.send_message')
    phone = "whatsapp:+1234567890"
    
    # 1. Start
    res = handler(make_event({"From": phone, "Body": "hi"}), None)
    assert res['statusCode'] == 200
    assert mock_send.call_args[0][0] == phone
    assert "English" in mock_send.call_args[0][1]
    
    # 2. Language
    res = handler(make_event({"From": phone, "Body": "1"}), None)
    assert "location pin" in mock_send.call_args[0][1]
    
    # 3. Location (Mocking fallback)
    res = handler(make_event({"From": phone, "Latitude": "29.0", "Longitude": "76.0"}), None)
    assert "Rohtak" in mock_send.call_args[0][1] # Fallback to nearest
    assert "Paddy" in mock_send.call_args[0][1]
    
    # 4. Crop
    res = handler(make_event({"From": phone, "Body": "1"}), None)
    assert "area" in mock_send.call_args[0][1]
    
    # 5. Area
    res = handler(make_event({"From": phone, "Body": "2 acres"}), None)
    assert "sow" in mock_send.call_args[0][1]
    
    # 6. Sowing Date
    res = handler(make_event({"From": phone, "Body": "last week"}), None)
    assert "irrigation" in mock_send.call_args[0][1]
    
    # 7. Irrigation
    res = handler(make_event({"From": phone, "Body": "tube well"}), None)
    assert "consent" in mock_send.call_args[0][1]
    
    # 8. Consent
    res = handler(make_event({"From": phone, "Body": "yes"}), None)
    assert "complete" in mock_send.call_args[0][1]
    
    # 9. Verify DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    table = dynamodb.Table(os.environ['FARMS_TABLE'])
    farmer_id = get_farmer_id(phone)
    farm = table.get_item(Key={'farmer_id': farmer_id})['Item']
    
    assert farm['crop'] == 'paddy'
    assert farm['area'] == '2 acres'
    assert farm['consent'] == True
    assert farm['onboarding_state'] == 'DONE'

def test_photo_upload(aws_setup, mocker):
    mock_send = mocker.patch('webhook.TwilioAdapter.send_message')
    phone = "whatsapp:+1234567890"
    
    # First finish onboarding
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    table = dynamodb.Table(os.environ['FARMS_TABLE'])
    farmer_id = get_farmer_id(phone)
    table.put_item(Item={
        "farmer_id": farmer_id,
        "contact_e164": phone,
        "onboarding_state": "DONE",
        "lang": "en"
    })
    
    # Send photo
    event = make_event({
        "From": phone, 
        "NumMedia": "1", 
        "MediaUrl0": "http://example.com/photo.jpg",
        "MediaContentType0": "image/jpeg"
    })
    
    res = handler(event, None)
    assert res['statusCode'] == 200
    
    # Verify observation created
    obs_table = dynamodb.Table(os.environ['OBSERVATIONS_TABLE'])
    obs_res = obs_table.query(
        KeyConditionExpression="plot_id = :p",
        ExpressionAttributeValues={":p": f"plot-{farmer_id}-1"}
    )
    assert len(obs_res['Items']) == 1
    assert "photo_received" not in mock_send.call_args[0][1] # It sends a formatted string, check the structure
    assert "photo received" in mock_send.call_args[0][1].lower()
