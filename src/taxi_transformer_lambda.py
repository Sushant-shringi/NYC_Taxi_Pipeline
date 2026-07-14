import json
import boto3
from datetime import datetime

def lambda_handler(event, context=None):
    try:
        print("Transformer Stage Triggered (Zero-Dependency)...")
        bucket_name = event.get('bucket_name')
        zone_key = event.get('zone_key')
        
        s3_client = boto3.client('s3')
        
        # 1. Zone Lookup CSV ko read aur parse karo (Pure Python)
        zone_obj = s3_client.get_object(Bucket=bucket_name, Key=zone_key)
        zone_content = zone_obj['Body'].read().decode('utf-8')
        
        zone_mapping = {}
        lines = zone_content.split('\n')
        # First line header hoti hai: LocationID,Borough,Zone,service_zone
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split(',')
            if len(parts) >= 3:
                loc_id = parts[0].strip()
                zone_name = parts[2].strip().replace('"', '')
                zone_mapping[loc_id] = zone_name

        print(f"Successfully mapped {len(zone_mapping)} zones.")
        
        # 2. Dummy Clean Record for testing the pipeline chain
        # (Kyunki Parquet bina pandas ke binary parse karna heavy hai, hum workflow check karne ke liye live metadata generate kar rahe hain)
        clean_records = [
            {
                "record_id": f"TX_VEND1_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "vendor_id": "VEND1",
                "passenger_count": 2,
                "trip_distance": 4.5,
                "total_cost": "25.50",
                "pickup_zone": zone_mapping.get("1", "UNKNOWN"),
                "processed_at": datetime.utcnow().isoformat()
            }
        ]
        
        output_payload = {
            "status": "Transformed",
            "total_input_records": 1,
            "rejected_records": 0,
            "data": clean_records
        }
        
        # 3. Trigger Loader Lambda
        if context and hasattr(context, 'function_name'):
            lambda_client = boto3.client('lambda', region_name='us-east-1')
            lambda_client.invoke(
                FunctionName='taxi-loader-service',
                InvocationType='Event',
                Payload=json.dumps(output_payload)
            )
            print("Successfully triggered taxi-loader-service.")
            
        return output_payload

    except Exception as e:
        print(f"Transformer Error: {str(e)}")
        return {"status": "Error", "message": str(e)}