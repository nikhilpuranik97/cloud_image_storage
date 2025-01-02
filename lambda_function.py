import os
import boto3
import hashlib
import logging
from Crypto.Cipher import Blowfish
from Crypto.Util.Padding import pad

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

def lambda_handler(event, context):
    try:
        # Log event details
        logger.info("Lambda triggered with event: %s", event)

        # Parse the event for S3 bucket and object details
        source_bucket = event['Records'][0]['s3']['bucket']['name']
        source_key = event['Records'][0]['s3']['object']['key']
        target_bucket = "processed-images-bucket-folder"  # Processed bucket name
        
        logger.info("Source Bucket: %s, Source Key: %s", source_bucket, source_key)

        # Get object metadata to retrieve the encryption password
        metadata = s3.head_object(Bucket=source_bucket, Key=source_key)['Metadata']
        password = metadata.get('encryption-password')
        if not password:
            logger.error("Encryption password not found in object metadata.")
            raise Exception("Encryption password not found in object metadata.")
        
        logger.info("Encryption password retrieved successfully.")

        # Download the file from source S3 bucket
        download_path = f"/tmp/{os.path.basename(source_key)}"
        s3.download_file(source_bucket, source_key, download_path)
        logger.info("File downloaded from S3 to %s", download_path)

        # Encrypt the file
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt', 100000, dklen=32)
        cipher = Blowfish.new(key, Blowfish.MODE_CBC)
        iv = cipher.iv
        with open(download_path, 'rb') as file:
            file_data = file.read()
        padded_data = pad(file_data, Blowfish.block_size)
        encrypted_data = iv + cipher.encrypt(padded_data)
        
        logger.info("File encrypted successfully.")

        # Save the encrypted file locally
        encrypted_path = f"/tmp/{os.path.splitext(os.path.basename(source_key))[0]}.enc"
        with open(encrypted_path, 'wb') as enc_file:
            enc_file.write(encrypted_data)
        
        logger.info("Encrypted file saved locally at %s", encrypted_path)

        # Upload the encrypted file to the processed S3 bucket
        encrypted_key = f"encrypted/{os.path.basename(encrypted_path)}"
        s3.upload_file(encrypted_path, target_bucket, encrypted_key)
        
        logger.info("Encrypted file uploaded to S3 bucket %s with key %s", target_bucket, encrypted_key)

        return {
            "statusCode": 200,
            "body": f"Encrypted file uploaded to s3://{target_bucket}/{encrypted_key}"
        }
    except Exception as e:
        logger.error("Error during encryption: %s", str(e))
        return {
            "statusCode": 500,
            "body": f"Error: {str(e)}"
        }
