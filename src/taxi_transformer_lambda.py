import json
import boto3
from datetime import datetime

def lambda_handler(event, context=None):
    try:
        print("Transformer Stage Triggered...")
        raw_records = event.get('data', [])
        zone_records = event.get('zone_data', [])
        
        clean_records = []
        total_input_records = len(raw_records)
        rejected_records = 0
        
        zone_mapping = {str(z['LocationID']): z['Zone'] for z in zone_records if 'LocationID' in z and 'Zone' in z}
        
        for row in raw_records:
            try:
                p_count = int(row.get('passenger_count', 0))
                distance = float(row.get('trip_distance', 0))
                if p_count <= 0 or distance <= 0:
                    rejected_records += 1
                    continue
                
                vendor_id = str(row.get('VendorID', 'UNKNOWN')).strip().upper()
                
                fare = float(row.get('fare_amount', 0))
                tip = float(row.get('tip_amount', 0))
                total_cost = fare + tip
                
                pu_id = str(row.get('PULocationID', ''))
                pickup_zone = zone_mapping.get(pu_id, 'UNKNOWN')
                
                pickup_time = str(row.get('tpep_pickup_datetime', ''))
                record_id = f"TX_{vendor_id}_{pickup_time}".replace(" ", "_").replace(":", "-")
                
                clean_row = {
                    "record_id": record_id,
                    "vendor_id": vendor_id,
                    "passenger_count": p_count,
                    "trip_distance": distance,
                    "total_cost": str(total_cost),
                    "pickup_zone": pickup_zone,
                    "processed_at": datetime.utcnow().isoformat()
                }
                clean_records.append(clean_row)
                
            except Exception:
                rejected_records += 1
                
        output_payload = {
            "status": "Transformed",
            "total_input_records": total_input_records,
            "rejected_records": rejected_records,
            "data": clean_records
        }
        
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
        return {"status": "Error", "data": []}