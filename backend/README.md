# Backend Webhook for Jal-Saathi

This module contains the WhatsApp Channel webhook handler.

## Data Storage & Privacy
- **Farmer Identification**: The `farmer_id` is generated as an HMAC-SHA256 hash of the farmer's phone number using a secret from AWS Secrets Manager.
- **Contact Info**: We store the farmer's E.164 phone number in `Farms.contact_e164` solely to enable weekly advisory push messages.
- **Delete-on-Request**: A delete-on-request path is implemented. To remove all PII and data associated with a farmer's number, locate the farmer's ID via the HMAC hash of their phone number, and delete the corresponding items from the DynamoDB `Farms` and `Observations` tables, and objects from the S3 Photos bucket under their `farmer_id` prefix.\n