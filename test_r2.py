import boto3, os, uuid
from dotenv import load_dotenv
load_dotenv()

endpoint_url = os.environ.get("R2_ENDPOINT_URL")
access_key = os.environ.get("R2_ACCESS_KEY_ID")
secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
bucket_name = os.environ.get("R2_BUCKET_NAME")

print("Keys:", access_key, endpoint_url)

s3 = boto3.client(
    "s3",
    endpoint_url=endpoint_url,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
)

with open("test_r2.py", "rb") as f:
    s3.upload_fileobj(f, bucket_name, "test_upload.py")
print("Uploaded successfully")
