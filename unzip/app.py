import boto3
import zipfile
import os
import shutil

ZIP_FILE_NAME = 'audio.zip'
OUTPUT_BUCKET_NAME = os.environ['OUTPUT_BUCKET_NAME']

s3 = boto3.client('s3')

# Note this code only handles the case where one s3 record is recieved 
# the code should handle an array of records and loop over the zip files. 
def lambda_handler(event, context):
    print(f"Received event: {event}")
    s3.download_file(event['Records'][0]['s3']['bucket']['name'], 
                     event['Records'][0]['s3']['object']['key'], 
                     f"/tmp/{ZIP_FILE_NAME}")

    # Unzip
    with zipfile.ZipFile(f"/tmp/{ZIP_FILE_NAME}", 'r') as zip_ref:
        zip_ref.extractall("/tmp/audio")
    
    # list all files in the /tmp/audio directory
    for file in os.listdir("/tmp/audio"):
        print(f"Uploading {file} to S3")
        s3.upload_file(f"/tmp/audio/{file}", OUTPUT_BUCKET_NAME, file)

    # clean up tmp files
    os.remove(f"/tmp/{ZIP_FILE_NAME}")
    shutil.rmtree("/tmp/audio")

    # Execute Step Function
    # TODO