import json
import boto3
from datetime import datetime

def lambda_handler(event, context=None):
    try:
        print("Loader Stage Triggered...")
        clean_records = event.get('data', [])
        total_input_records = event.get('total_input_records', 0)
        rejected_records = event.get('rejected_records', 0)
        
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('clean_records')
        
        inserted_records = 0
        
        for record in clean_records:
            try:
                table.put_item(Item=record)
                inserted_records += 1
            except Exception as e:
                print(f"DynamoDB Insert Failed: {str(e)}")
                rejected_records += 1
                
        audit_summary = {
            "total_input_records": total_input_records,
            "inserted_records": inserted_records,
            "rejected_records": rejected_records,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        print("=========================================")
        print("ETL AUDIT SUMMARY LOG:")
        print(json.dumps(audit_summary, indent=4))
        print("=========================================")
        
        return {"status": "Completed", "audit": audit_summary}
        
    except Exception as e:
        print(f"Loader Error: {str(e)}")
        return {"status": "Error"}