import argparse
import os
import boto3

def upload_processed(bucket_name, env, dry_run=True):
    s3 = boto3.client('s3')
    base_dir = 'processed'
    full_bucket = f"{bucket_name}-{env}"
    
    print(f"Uploading {base_dir} to s3://{full_bucket} (Dry Run: {dry_run})")
    
    if not os.path.exists(base_dir):
        print(f"Directory {base_dir} does not exist.")
        return
        
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            local_path = os.path.join(root, file)
            # Remove 'processed/' from the key
            s3_key = os.path.relpath(local_path, base_dir).replace(os.sep, '/')
            
            if s3_key.startswith("soil_"):
                s3_key = f"soil/{s3_key}"
            
            if dry_run:
                print(f"[DRY-RUN] Would upload {local_path} to s3://{full_bucket}/{s3_key}")
            else:
                print(f"Uploading {local_path} to s3://{full_bucket}/{s3_key}")
                s3.upload_file(local_path, full_bucket, s3_key)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", default="jal-saathi-datasets")
    parser.add_argument("--env", default="dev")
    parser.add_argument("--execute", action="store_true", help="Actually perform the upload")
    args = parser.parse_args()
    
    upload_processed(args.bucket, args.env, dry_run=not args.execute)
