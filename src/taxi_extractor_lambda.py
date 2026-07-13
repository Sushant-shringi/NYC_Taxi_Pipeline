import json
import urllib.parse
import boto3
import pandas as pd
import io

def lambda_handler(event, context=None):
    try:
        bucket = event.get('Records', [{}])[0].get('s3', {}).get('bucket', {}).get('name', None)
        key = event.get('Records', [{}])[0].get('s3', {}).get('object', {}).get('key', 'yellow_tripdata_2024-01.parquet')
        
        trip_cols = [
            "tpep_pickup_datetime", "tpep_dropoff_datetime", "PULocationID",
            "DOLocationID", "passenger_count", "trip_distance",
            "fare_amount", "total_amount", "payment_type"
        ]
        
        if context is None or not hasattr(context, 'function_name'):
            jan_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
            df = pd.read_parquet(jan_url, columns=trip_cols)
            df = df.head(10000)
        else:
            s3_client = boto3.client('s3')
            response = s3_client.get_object(Bucket=bucket, Key=key)
            parquet_data = response['Body'].read()
            df = pd.read_parquet(io.BytesIO(parquet_data), columns=trip_cols)
            
        raw_records = df.to_dict(orient='records')
        output_payload = {
            "status": "Extracted",
            "file_processed": key,
            "data": raw_records
        }
        
        if context and hasattr(context, 'function_name'):
            lambda_client = boto3.client('lambda', region_name='us-east-1')
            lambda_client.invoke(
                FunctionName='taxi-transformer-service',
                InvocationType='Event',
                Payload=json.dumps(output_payload)
            )
            
        return output_payload
        
    except Exception as e:
        return {"status": "Error", "file_processed": "unknown", "data": []}