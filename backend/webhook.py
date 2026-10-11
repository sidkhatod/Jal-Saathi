import os
import json
import hmac
import hashlib
import base64
import urllib.parse
from datetime import datetime, timezone
import uuid
import boto3
from typing import Dict, Any, Optional
from twilio.request_validator import RequestValidator
from messages import MESSAGES
import requests
import math

# Init AWS clients
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get("AWS_REGION", "ap-south-1"))
secretsmanager = boto3.client('secretsmanager', region_name=os.environ.get("AWS_REGION", "ap-south-1"))
location_client = boto3.client('location', region_name=os.environ.get("AWS_REGION", "ap-south-1"))
s3 = boto3.client('s3', region_name=os.environ.get("AWS_REGION", "ap-south-1"))

ENV = os.environ.get("ENV", "dev")
TWILIO_SECRET_ARN = os.environ.get("TWILIO_SECRET_ARN")
PLACE_INDEX_NAME = os.environ.get("PLACE_INDEX_NAME")
FARMS_TABLE = os.environ.get("FARMS_TABLE")
PLOTS_TABLE = os.environ.get("PLOTS_TABLE")
OBSERVATIONS_TABLE = os.environ.get("OBSERVATIONS_TABLE")
PHOTOS_BUCKET = os.environ.get("PHOTOS_BUCKET")

# Caching secrets
_secrets = None

def get_secrets():
    global _secrets
    if not _secrets:
        try:
            resp = secretsmanager.get_secret_value(SecretId=TWILIO_SECRET_ARN)
            _secrets = json.loads(resp['SecretString'])
        except Exception as e:
            print("Failed to get secret:", e)
            _secrets = {}
    return _secrets

class ChannelAdapter:
    def parse_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
    def validate_signature(self, event: Dict[str, Any]) -> bool:
        raise NotImplementedError
    def send_message(self, to: str, body: str):
        raise NotImplementedError

class TwilioAdapter(ChannelAdapter):
    def parse_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        body = event.get('body', '')
        if event.get('isBase64Encoded'):
            body = base64.b64decode(body).decode('utf-8')
        
        parsed = dict(urllib.parse.parse_qsl(body))
        return parsed

    def validate_signature(self, event: Dict[str, Any]) -> bool:
        secrets = get_secrets()
        auth_token = secrets.get('TWILIO_AUTH_TOKEN', '')
        validator = RequestValidator(auth_token)
        
        # Get signature
        headers = event.get('headers', {})
        # lowercase headers are typical in API GW v2 / HTTP API
        signature = headers.get('x-twilio-signature') or headers.get('X-Twilio-Signature', '')
        
        # Reconstruct URL (assuming Function URL or API GW)
        # Function URL has host header
        host = headers.get('host') or headers.get('Host', '')
        
        # API GW v2 uses rawPath, v1 uses path
        path = event.get('rawPath') or event.get('path', '/')
        # Note: AWS Lambda Function URL includes the protocol
        # Twilio sends the signature using https://
        protocol = headers.get('x-forwarded-proto') or headers.get('X-Forwarded-Proto', 'https')
        
        url = f"{protocol}://{host}{path}"
        query_string = event.get('rawQueryString') or event.get('queryStringParameters')
        if event.get('rawQueryString'):
            url += f"?{event.get('rawQueryString')}"
        elif query_string:
            # Need to reconstruct query string if dict
            pass
            
        params = self.parse_request(event)
        
        return validator.validate(url, params, signature)
    
    def send_message(self, to: str, body: str):
        secrets = get_secrets()
        account_sid = secrets.get('TWILIO_ACCOUNT_SID')
        auth_token = secrets.get('TWILIO_AUTH_TOKEN')
        from_number = secrets.get('TWILIO_PHONE_NUMBER', 'whatsapp:+14155238886') # Sandbox number
        
        if not account_sid or not auth_token:
            print("Missing Twilio credentials")
            return
            
        # Twilio API call
        auth = (account_sid, auth_token)
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        data = {
            "To": to,
            "From": from_number,
            "Body": body
        }
        resp = requests.post(url, data=data, auth=auth)
        if resp.status_code >= 400:
            print("Twilio API Error:", resp.text)

adapter = TwilioAdapter()

def handler(event, context):
    try:
        return process_event(event)
    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 500, "body": "Internal Server Error"}

def get_farmer_id(phone: str) -> str:
    secrets = get_secrets()
    secret_key = secrets.get('TWILIO_SECRET_KEY', 'default_secret').encode('utf-8')
    return hmac.new(secret_key, phone.encode('utf-8'), hashlib.sha256).hexdigest()

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

PILOT_DISTRICTS = [
    {"name": "Rohtak", "lat": 28.8955, "lon": 76.5892},
    {"name": "Karnal", "lat": 29.6857, "lon": 76.9905},
]

def find_nearest_district(lat: float, lon: float) -> str:
    nearest = min(PILOT_DISTRICTS, key=lambda d: haversine(lat, lon, d['lat'], d['lon']))
    return nearest['name']

def process_event(event: Dict[str, Any]):
    # Allow testing without signature validation using a special header or for unit tests
    if not event.get('_testing'):
        if not adapter.validate_signature(event):
            print("Signature validation failed")
            return {"statusCode": 401, "body": "Unauthorized"}
        
    params = adapter.parse_request(event)
    from_number = params.get('From', '')
    body_text = params.get('Body', '').strip().lower()
    
    farmer_id = get_farmer_id(from_number)
    
    farms_table = dynamodb.Table(FARMS_TABLE)
    
    # Fetch farm / onboarding state
    resp = farms_table.get_item(Key={"farmer_id": farmer_id})
    farm = resp.get('Item', {})
    
    if not farm or body_text == 'reset':
        farm = {
            "farmer_id": farmer_id,
            "contact_e164": from_number,
            "onboarding_state": "START",
            "lang": "en"
        }
        farms_table.put_item(Item=farm)
    
    state = farm.get("onboarding_state", "START")
    lang = farm.get("lang", "en")
    msg_dict = MESSAGES.get(lang, MESSAGES["en"])
    
    # Process Photos if onboarding is complete
    if state == "DONE":
        num_media = int(params.get('NumMedia', '0'))
        if num_media > 0:
            media_url = params.get('MediaUrl0')
            media_type = params.get('MediaContentType0')
            
            if media_type in ['image/jpeg', 'image/png', 'image/jpg']:
                # Basic Auth for Twilio Media
                secrets = get_secrets()
                auth = (secrets.get('TWILIO_ACCOUNT_SID'), secrets.get('TWILIO_AUTH_TOKEN'))
                
                # Mock requests for testing
                if event.get('_testing'):
                    r = type('MockResponse', (object,), {'status_code': 200, 'raw': b''})()
                else:
                    r = requests.get(media_url, auth=auth, stream=True)
                
                if r.status_code == 200:
                    now = datetime.now(timezone.utc)
                    iso_year, iso_week, _ = now.isocalendar()
                    week_str = f"{iso_year}-W{iso_week:02d}"
                    plot_id = f"plot-{farmer_id}-1" # Default plot
                    img_uuid = str(uuid.uuid4())
                    
                    s3_key = f"photos/{farmer_id}/{plot_id}/{week_str}/{img_uuid}.jpg"
                    
                    if not event.get('_testing'):
                        s3.upload_fileobj(r.raw, PHOTOS_BUCKET, s3_key, ExtraArgs={'ContentType': media_type})
                    
                    obs_table = dynamodb.Table(OBSERVATIONS_TABLE)
                    obs_table.put_item(Item={
                        "plot_id": plot_id,
                        "observation_timestamp": now.isoformat(),
                        "farmer_id": farmer_id,
                        "photo_s3_key": s3_key,
                        "week": week_str
                    })
                    
                    obs_res = obs_table.query(
                        KeyConditionExpression="plot_id = :p",
                        ExpressionAttributeValues={":p": plot_id}
                    )
                    count = sum(1 for item in obs_res.get('Items', []) if item.get('week') == week_str)
                    
                    adapter.send_message(from_number, msg_dict["photo_received"].format(count=count))
                    return {"statusCode": 200, "body": "OK"}
        
        # If not media or no matching logic
        adapter.send_message(from_number, msg_dict["done"])
        return {"statusCode": 200, "body": "OK"}
        
    # Onboarding State Machine
    next_state = state
    reply_msg = ""
    
    if state == "START":
        reply_msg = MESSAGES["en"]["welcome"]
        next_state = "AWAITING_LANG"
        
    elif state == "AWAITING_LANG":
        if body_text in ['1', 'english']:
            farm['lang'] = 'en'
            reply_msg = MESSAGES['en']['location']
            next_state = "AWAITING_LOCATION"
        elif body_text in ['2', 'hindi', 'hi']:
            farm['lang'] = 'hi'
            reply_msg = MESSAGES['hi']['location']
            next_state = "AWAITING_LOCATION"
        else:
            reply_msg = msg_dict['invalid']
            
    elif state == "AWAITING_LOCATION":
        lat = params.get('Latitude')
        lon = params.get('Longitude')
        if lat and lon:
            lat_f, lon_f = float(lat), float(lon)
            from decimal import Decimal
            farm['location'] = {'lat': Decimal(str(lat_f)), 'lon': Decimal(str(lon_f))}
            
            # Reverse geocode
            try:
                if event.get('_testing'):
                    district = event.get('_mock_district', 'Unknown')
                else:
                    geo_resp = location_client.search_place_index_for_position(
                        IndexName=PLACE_INDEX_NAME,
                        Position=[lon_f, lat_f] # Longitude first for Location Service
                    )
                    district = "Unknown"
                    if geo_resp.get('Results'):
                        place = geo_resp['Results'][0].get('Place', {})
                        district = place.get('SubRegion') or place.get('Region') or "Unknown"
                
                if district == "Unknown":
                    # Fallback
                    nearest = find_nearest_district(lat_f, lon_f)
                    farm['district'] = nearest
                    reply_msg = msg_dict['location_fallback'].format(district=nearest) + "\n\n" + msg_dict['crop']
                else:
                    farm['district'] = district
                    reply_msg = msg_dict['location_found'].format(district=district) + "\n\n" + msg_dict['crop']
                
                next_state = "AWAITING_CROP"
            except Exception as e:
                print("Geocode error:", e)
                # Fallback to nearest
                nearest = find_nearest_district(lat_f, lon_f)
                farm['district'] = nearest
                reply_msg = msg_dict['location_fallback'].format(district=nearest) + "\n\n" + msg_dict['crop']
                next_state = "AWAITING_CROP"
        else:
            reply_msg = msg_dict['invalid']
            
    elif state == "AWAITING_CROP":
        if body_text in ['1', 'paddy', 'धान']:
            farm['crop'] = 'paddy'
            reply_msg = msg_dict['area']
            next_state = "AWAITING_AREA"
        elif body_text in ['2', 'wheat', 'गेहूं']:
            farm['crop'] = 'wheat'
            reply_msg = msg_dict['area']
            next_state = "AWAITING_AREA"
        else:
            reply_msg = msg_dict['invalid']
            
    elif state == "AWAITING_AREA":
        farm['area'] = body_text
        reply_msg = msg_dict['sowing_date']
        next_state = "AWAITING_SOWING_DATE"
        
    elif state == "AWAITING_SOWING_DATE":
        farm['sowing_date'] = body_text
        reply_msg = msg_dict['irrigation']
        next_state = "AWAITING_IRRIGATION"
        
    elif state == "AWAITING_IRRIGATION":
        farm['irrigation'] = body_text
        reply_msg = msg_dict['consent']
        next_state = "AWAITING_CONSENT"
        
    elif state == "AWAITING_CONSENT":
        if 'yes' in body_text or 'हाँ' in body_text:
            farm['consent'] = True
            reply_msg = msg_dict['done']
            next_state = "DONE"
        else:
            reply_msg = msg_dict['invalid']
            
    farm['onboarding_state'] = next_state
    farms_table.put_item(Item=farm)
    
    if reply_msg:
        adapter.send_message(from_number, reply_msg)
        
    return {"statusCode": 200, "body": "OK"}
