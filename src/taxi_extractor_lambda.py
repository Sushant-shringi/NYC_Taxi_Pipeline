import json
import urllib.parse
import urllib.request
import boto3

def lambda_handler(event, context=None):
    try:
        s3_client = boto3.client('s3')
        
        # 📋 Aapka S3 Bucket Name
        bucket_name = "nyc-taxi-raw-data-sushant"
        
        jan_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
        zone_url = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
        
        # 🛡️ Browser Header (User-Agent) taaki 403 Forbidden Error na aaye
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        print("Downloading Yellow Taxi Parquet file...")
        req_jan = urllib.request.Request(jan_url, headers=headers)
        with urllib.request.urlopen(req_jan) as response:
            parquet_data = response.read()
            s3_client.put_object(Bucket=bucket_name, Key="raw/yellow_tripdata_2024-01.parquet", Body=parquet_data)
            
        print("Downloading Taxi Zone CSV file...")
        req_zone = urllib.request.Request(zone_url, headers=headers)
        with urllib.request.urlopen(req_zone) as response:
            zone_data = response.read()
            s3_client.put_object(Bucket=bucket_name, Key="raw/taxi_zone_lookup.csv", Body=zone_data)
            
        print("Successfully saved raw files to S3 using built-in streams with Headers.")
        
        output_payload = {
            "status": "Extracted",
            "bucket_name": bucket_name,
            "data_key": "raw/yellow_tripdata_2024-01.parquet",
            "zone_key": "raw/taxi_zone_lookup.csv"
        }
        
        if context and hasattr(context, 'function_name'):
            lambda_client = boto3.client('lambda', region_name='us-east-1')
            lambda_client.invoke(
                FunctionName='taxi-transformer-service',
                InvocationType='Event',
                Payload=json.dumps(output_payload)
            )
            print("Successfully triggered taxi-transformer-service.")
            
        return {"status": "Success", "payload": output_payload}
        
    except Exception as e:
        print(f"Extractor Error: {str(e)}")
        return {"status": "Error", "message": str(e)}