import json
import boto3
from datetime import datetime

def lambda_handler(event, context=None):
    try:
        print("Loader Stage Triggered with accurate schemas and data types...")
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # 📋 Sahi tables ke naam (Spelling Corrected)
        zone_table = dynamodb.Table('nyc_taxi_zone_summary')
        payment_table = dynamodb.Table('nyc_taxi_payment_summary')
        borough_table = dynamodb.Table('nyc_taxi_borough_hour_long')
        
        records = event.get('data', [])
        print(f"Received {len(records)} clean records to load into DynamoDB.")
        
        for row in records:
            current_time = datetime.utcnow()
            
            # 1️⃣ Table: nyc_taxi_zone_summary
            # Keys: pickup_borough (String), pickup_zone (String)
            zone_table.put_item(
                Item={
                    'pickup_borough': str(row.get('pickup_borough', 'EWR')),
                    'pickup_zone': str(row.get('pickup_zone', 'Newark Airport')),
                    'record_id': str(row.get('record_id', 'TX_DUMMY')),
                    'trip_distance': str(row.get('trip_distance', '4.5')),
                    'processed_at': str(row.get('processed_at', current_time.isoformat()))
                }
            )
            
            # 2️⃣ Table: nyc_taxi_payment_summary
            # Keys: pickup_month (String), payment_type (Number)
            payment_table.put_item(
                Item={
                    'pickup_month': str(current_time.strftime('%B')), # Jaise 'July' (String)
                    'payment_type': int(row.get('payment_type', 1)),   # Strict Number/Integer
                    'record_id': str(row.get('record_id', 'TX_DUMMY')),
                    'total_cost': str(row.get('total_cost', '25.50')),
                    'vendor_id': str(row.get('vendor_id', 'VEND1')),
                    'processed_at': str(row.get('processed_at', current_time.isoformat()))
                }
            )
            
            # 3️⃣ Table: nyc_taxi_borough_hour_long
            # Keys: pickup_hour (Number), pickup_borough (String)
            borough_table.put_item(
                Item={
                    'pickup_hour': int(current_time.hour),             # Strict Number/Integer (e.g., 18)
                    'pickup_borough': str(row.get('pickup_borough', 'EWR')), # Sort Key (String)
                    'record_id': str(row.get('record_id', 'TX_DUMMY')),
                    'passenger_count': int(row.get('passenger_count', 2)),
                    'processed_at': str(row.get('processed_at', current_time.isoformat()))
                }
            )
            
        print("Successfully loaded data into all three reporting tables with strict data types!")
        return {"status": "Success", "loaded_records": len(records)}
        
    except Exception as e:
        print(f"Loader Error: {str(e)}")
        return {"status": "Error", "message": str(e)}