import json
import urllib.request
import boto3

def lambda_handler(event, context=None):
    try:
        s3_client = boto3.client('s3')
        
        
        bucket_name = "nyc-taxi-raw-data-sushant"
        
        jan_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
        zone_url = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
        
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        print("Downloading real Taxi Zone CSV file...")
        req_zone = urllib.request.Request(zone_url, headers=headers)
        with urllib.request.urlopen(req_zone) as response:
            zone_data = response.read()
            s3_client.put_object(Bucket=bucket_name, Key="raw/taxi_zone_lookup.csv", Body=zone_data)
        print("✅ Saved taxi_zone_lookup.csv to S3.")
            
        # 2. Download & Stream January Yellow Taxi Parquet to S3
        print("Downloading real Yellow Taxi Parquet file (January 2024)...")
        req_jan = urllib.request.Request(jan_url, headers=headers)
        with urllib.request.urlopen(req_jan) as response:
            parquet_data = response.read()
            s3_client.put_object(Bucket=bucket_name, Key="raw/yellow_tripdata_2024-01.parquet", Body=parquet_data)
        print("✅ Saved yellow_tripdata_2024-01.parquet to S3.")
        
        output_payload = {
            "status": "Extracted",
            "bucket_name": bucket_name,
            "data_key": "raw/yellow_tripdata_2024-01.parquet",
            "zone_key": "raw/taxi_zone_lookup.csv"
        }
        
        # 3. Trigger Transformer (Asynchronously - Safe Mode to avoid Rate Limits)
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        print("Triggering transformer stage asynchronously...")
        lambda_client.invoke(
            FunctionName='taxi-transformer-service',
            InvocationType='Event',
            Payload=json.dumps(output_payload)
        )
        
        return {"status": "Success", "message": "Pipeline triggered successfully, check S3 and CloudWatch."}
        
    except Exception as e:
        print(f"Extractor Error: {str(e)}")
        return {"status": "Error", "message": str(e)}
