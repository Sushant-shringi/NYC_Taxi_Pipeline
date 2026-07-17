import boto3
import json

def trigger_pipeline():
    print("🚀 Triggering NYC Taxi Extractor Lambda from local system...")
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    
    mock_event = {
        "Records": [
            {
                "s3": {
                    "bucket": {
                        "name": "your-raw-s3-bucket-name"
                    },
                    "object": {
                        "key": "raw/yellow_tripdata_2024-01.parquet"
                    }
                }
            }
        ]
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='taxi-extractor-service',
            InvocationType='RequestResponse',
            Payload=json.dumps(mock_event)
        )
        
        response_payload = json.loads(response['Payload'].read().decode('utf-8'))
        print("✅ Extractor Triggered Successfully!")
        print("Response:", response_payload)
        print("📢 Check AWS CloudWatch Logs for Transformer and Loader auto-trigger updates.")
        
    except Exception as e:
        print("❌ Error triggering Lambda:", str(e))

if __name__ == "__main__":
    trigger_pipeline()
