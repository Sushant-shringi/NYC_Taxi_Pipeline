import json
import boto3
import pandas as pd

def lambda_handler(event, context=None):
    try:
        input_data = event.get('data', [])
        file_processed = event.get('file_processed', 'unknown')
        
        df = pd.DataFrame(input_data)
        
        df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
        df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])
        
        df['trip_minutes'] = (df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime']).dt.total_seconds() / 60.0
        
        df = df[(df['total_amount'] > 0) & (df['trip_distance'] > 0) & (df['trip_minutes'] > 0)]
        
        df['pickup_month'] = df['tpep_pickup_datetime'].dt.strftime('%B')
        df['pickup_date'] = df['tpep_pickup_datetime'].dt.date.astype(str)
        df['pickup_hour'] = df['tpep_pickup_datetime'].dt.hour
        
        zones_url = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
        zones = pd.read_csv(zones_url)
        
        pickup_zones = zones.rename(columns={"LocationID": "PULocationID", "Borough": "pickup_borough", "Zone": "pickup_zone"})
        df = pd.merge(df, pickup_zones[["PULocationID", "pickup_borough", "pickup_zone"]], on="PULocationID", how="left")
        
        dropoff_zones = zones.rename(columns={"LocationID": "DOLocationID", "Borough": "dropoff_borough", "Zone": "dropoff_zone"})
        df = pd.merge(df, dropoff_zones[["DOLocationID", "dropoff_borough", "dropoff_zone"]], on="DOLocationID", how="left")
        
        zone_summary = df.groupby(["pickup_borough", "pickup_zone"]).agg(
            trip_count=("total_amount", "count"),
            total_revenue=("total_amount", "sum"),
            avg_revenue=("total_amount", "mean"),
            avg_distance=("trip_distance", "mean"),
            min_distance=("trip_distance", "min"),
            max_distance=("trip_distance", "max")
        ).reset_index()
        
        payment_summary = df.groupby(["pickup_month", "payment_type"]).agg(
            count=("total_amount", "count"),
            total_revenue=("total_amount", "sum"),
            average_fare=("fare_amount", "mean"),
            min_fare=("fare_amount", "min"),
            max_fare=("fare_amount", "max")
        ).reset_index()
        
        pivot = pd.pivot_table(df, values="total_amount", index="pickup_hour", columns="pickup_borough", aggfunc="sum", fill_value=0)
        
        melted_pivot = pivot.reset_index().melt(id_vars="pickup_hour", var_name="pickup_borough", value_name="revenue")
        
        output_payload = {
            "status": "Transformed",
            "file_processed": file_processed,
            "zone_summary": zone_summary.to_dict(orient='records'),
            "payment_summary": payment_summary.to_dict(orient='records'),
            "melted_pivot": melted_pivot.to_dict(orient='records')
        }
        
        if context and hasattr(context, 'function_name'):
            lambda_client = boto3.client('lambda', region_name='us-east-1')
            lambda_client.invoke(
                FunctionName='taxi-loader-service',
                InvocationType='Event',
                Payload=json.dumps(output_payload)
            )
            
        return output_payload
        
    except Exception as e:
        return {"status": "Error", "file_processed": "unknown", "error": str(e)}