import boto3
import zipfile
import os
import shutil
import uuid

ZIP_FILE_NAME = 'audio.zip'
OUTPUT_BUCKET_NAME = os.environ['OUTPUT_BUCKET_NAME']

s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')

# Note this code only handles the case where one s3 record is recieved 
# the code should handle an array of records and loop over the zip files. 
# Also note, that the maximum number of files in zip that could be processed this way 
# is 10000 due to the limit of 10000 queued transcribe jobs. 
def lambda_handler(event, context):
    print(f"Received event: {event}")
    s3.download_file(event['Records'][0]['s3']['bucket']['name'], 
                     event['Records'][0]['s3']['object']['key'], 
                     f"/tmp/{ZIP_FILE_NAME}")

    # Unzip
    with zipfile.ZipFile(f"/tmp/{ZIP_FILE_NAME}", 'r') as zip_ref:
        zip_ref.extractall("/tmp/audio")

    job_run = uuid.uuid4()
    
    # list all files in the /tmp/audio directory
    for file in os.listdir("/tmp/audio"):
        print(f"Uploading {file} to S3")
        s3.upload_file(f"/tmp/audio/{file}", OUTPUT_BUCKET_NAME, "input/" + file)
        print(f"Starting Call Analytics Job for {file}")
        res = transcribe.start_call_analytics_job(
            CallAnalyticsJobName=f"Redact-{job_run}-{file}",
            Media={
                "MediaFileUri": f"s3://{OUTPUT_BUCKET_NAME}/input/{file}",
                "RedactedMediaFileUri": f"s3://{OUTPUT_BUCKET_NAME}/input/{file}"
            },
            OutputLocation=f"s3://{OUTPUT_BUCKET_NAME}/output/",
            Settings={
                'ContentRedaction': {
                    'RedactionType': 'PII',
                    'RedactionOutput': 'redacted',
                    'PiiEntityTypes': [
                        'ALL',
                    ]
            },
            'LanguageOptions': [
                'en-US'
            ]
            },
            ChannelDefinitions=[
            {
                'ChannelId': 0,
                'ParticipantRole': 'AGENT'
            },
            {
                'ChannelId': 1,
                'ParticipantRole': 'CUSTOMER'
            }
            ]
        )
        print(res)

    # clean up tmp files
    os.remove(f"/tmp/{ZIP_FILE_NAME}")
    shutil.rmtree("/tmp/audio")

    # Start Waiter Step Function
    # TODO