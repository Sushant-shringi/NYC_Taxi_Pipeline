import json
import boto3
import csv
from datetime import datetime

def lambda_handler(event, context=None):
    try:
        print("Transformer Stage Triggered on Python 3.14 (No Layer Mode)...")
        s3_client = boto3.client('s3')
        
        bucket_name = event.get('bucket_name', 'nyc-taxi-raw-data-sushant')
        zone_key = event.get('zone_key', 'raw/taxi_zone_lookup.csv')
        
        # 1. Download & Parse CSV Zone Lookup from S3 (Built-in CSV parser)
        print(f"Reading {zone_key} from S3...")
        zone_obj = s3_client.get_object(Bucket=bucket_name, Key=zone_key)
        zone_content = zone_obj['Body'].read().decode('utf-8').splitlines()
        
        # Map LocationID -> (Borough, Zone)
        zone_map = {}
        csv_reader = csv.reader(zone_content)
        next(csv_reader)  # Skip header
        for row in csv_reader:
            if len(row) >= 3:
                loc_id = row[0]
                borough = row[1]
                zone_name = row[2]
                zone_map[loc_id] = {"borough": borough, "zone": zone_name}

        print(f"Loaded {len(zone_map)} zones successfully.")
        
       
        current_time = datetime.utcnow()
        records_to_send = []
        
        sample_location_ids = ['1', '132', '138', '142', '230'] # Newark, JFK, LaGuardia, Manhattan zones
        
        for idx, loc_id in enumerate(sample_location_ids):
            zone_info = zone_map.get(loc_id, {"borough": "Unknown", "zone": "Unknown"})
            
            records_to_send.append({
                'record_id': f"TX_VEND1_{idx}_{int(current_time.timestamp())}",
                'pickup_borough': str(zone_info["borough"]),
                'pickup_zone': str(zone_info["zone"]),
                'trip_distance': str(3.5 + idx), # Mock processed calculation
                'payment_type': int(1 if idx % 2 == 0 else 2),
                'total_cost': str(15.50 + (idx * 5)),
                'vendor_id': "VEND1",
                'passenger_count': int(1 + (idx % 3)),
                'processed_at': current_time.isoformat()
            })
            
        print(f"Successfully processed {len(records_to_send)} records with real S3 Zone mapping!")
        
        # 3. Trigger Loader Lambda
        payload = {"data": records_to_send}
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        print("Triggering loader stage...")
        response = lambda_client.invoke(
            FunctionName='taxi-loader-service',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        loader_response = json.loads(response['Payload'].read().decode('utf-8'))
        return {"status": "Success", "loader_response": loader_response}
        
    except Exception as e:
        print(f"Transformer Error: {str(e)}")
        return {"status": "Error", "message": str(e)}
