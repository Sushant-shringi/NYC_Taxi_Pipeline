import json
import boto3

def lambda_handler(event, context=None):
    try:
        status = event.get('status', 'unknown')
        file_processed = event.get('file_processed', 'unknown')
        
        if status != 'Transformed':
            return {"status": "Skipped", "file_processed": file_processed}
            
        zone_summary = event.get('zone_summary', [])
        payment_summary = event.get('payment_summary', [])
        melted_pivot = event.get('melted_pivot', [])
        
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        zone_table = dynamodb.Table('nyc_taxi_zone_summary')
        with zone_table.batch_writer() as batch:
            for record in zone_summary:
                batch.put_item(Item={
                    'pickup_borough': str(record['pickup_borough']),
                    'pickup_zone': str(record['pickup_zone']),
                    'trip_count': int(record['trip_count']),
                    'total_revenue': float(record['total_revenue']),
                    'avg_revenue': float(record['avg_revenue']),
                    'avg_distance': float(record['avg_distance']),
                    'min_distance': float(record['min_distance']),
                    'max_distance': float(record['max_distance'])
                })
                
        payment_table = dynamodb.Table('nyc_taxi_payment_summary')
        with payment_table.batch_writer() as batch:
            for record in payment_summary:
                batch.put_item(Item={
                    'pickup_month': str(record['pickup_month']),
                    'payment_type': int(record['payment_type']),
                    'count': int(record['count']),
                    'total_revenue': float(record['total_revenue']),
                    'average_fare': float(record['average_fare']),
                    'min_fare': float(record['min_fare']),
                    'max_fare': float(record['max_fare'])
                })
                
        pivot_table = dynamodb.Table('nyc_taxi_borough_hour_long')
        with pivot_table.batch_writer() as batch:
            for record in melted_pivot:
                batch.put_item(Item={
                    'pickup_hour': int(record['pickup_hour']),
                    'pickup_borough': str(record['pickup_borough']),
                    'revenue': float(record['revenue'])
                })
                
        return {
            "status": "Loaded Successfully",
            "file_processed": file_processed,
            "metrics": {
                "zone_records": len(zone_summary),
                "payment_records": len(payment_summary),
                "pivot_records": len(melted_pivot)
            }
        }
        
    except Exception as e:
        return {"status": "Error", "file_processed": "unknown", "error": str(e)}