import json
import urllib.parse
import boto3
import csv
import io
import pandas as pd

def parse_csv_file(content):
    f = io.StringIO(content)
    reader = csv.DictReader(f)
    return list(reader)

def lambda_handler(event, context=None):
    try:
        if event and 'Records' in event:
            bucket = event['Records'][0]['s3']['bucket']['name']
            key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
            print(f"Triggered for S3 Key: {key}")
        
        print("Extracting data from CloudFront URLs...")
        
        jan_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
        zone_url = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
        
        df_parquet = pd.read_parquet(jan_url)
        df_sample = df_parquet.head(100)
        raw_records = df_sample.to_dict(orient='records')
        
        df_zone = pd.read_csv(zone_url)
        zone_records = df_zone.to_dict(orient='records')
        
        output_payload = {
            "status": "Extracted",
            "file_processed": "yellow_tripdata_2024-01.parquet",
            "data": raw_records,
            "zone_data": zone_records
        }
        
        if context and hasattr(context, 'function_name'):
            lambda_client = boto3.client('lambda', region_name='us-east-1')
            lambda_client.invoke(
                FunctionName='taxi-transformer-service',
                InvocationType='Event',
                Payload=json.dumps(output_payload, default=str)
            )
            print("Successfully triggered taxi-transformer-service.")
            
        return {"status": "Success", "records_count": len(raw_records)}
        
    except Exception as e:
        print(f"Extractor Error: {str(e)}")
        return {"status": "Error", "data": []}