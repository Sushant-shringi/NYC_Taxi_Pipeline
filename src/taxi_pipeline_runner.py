import json
from taxi_extractor_lambda import lambda_handler as extractor_handler
from taxi_transformer_lambda import lambda_handler as transformer_handler
from taxi_loader_lambda import lambda_handler as loader_handler

def run_local_pipeline():
    print("=== STARTING LOCAL NYC TAXI PIPELINE INTEGRATION TEST ===")
    
    mock_event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "local-mock-raw-bucket"},
                    "object": {"key": "yellow_tripdata_2024-01.parquet"}
                }
            }
        ]
    }
    
    print("\nExecuting Layer 1: Extractor...")
    extractor_output = extractor_handler(mock_event, context=None)
    print(f"Extractor Status: {extractor_output['status']}")
    
    if extractor_output['status'] == 'Error':
        print("Pipeline failed at Extraction stage.")
        return

    print("\nExecuting Layer 2: Transformer...")
    transformer_output = transformer_handler(extractor_output, context=None)
    print(f"Transformer Status: {transformer_output['status']}")
    
    if transformer_output['status'] == 'Error':
        print(f"Pipeline failed at Transformation stage: {transformer_output.get('error')}")
        return

    print("\nExecuting Layer 3: Loader (Simulated Mode)...")
    try:
        print("Skipping AWS DynamoDB batch write for local execution.")
        print(f"Records Processed successfully for file: {transformer_output['file_processed']}")
        print(f"Zone Summary Records: {len(transformer_output['zone_summary'])}")
        print(f"Payment Summary Records: {len(transformer_output['payment_summary'])}")
        print(f"Melted Pivot Records: {len(transformer_output['melted_pivot'])}")
        print("\n=== LOCAL PIPELINE EXECUTION SUCCESSFUL ===")
    except Exception as e:
        print(f"Pipeline failed at Loading stage: {str(e)}")

if __name__ == "__main__":
    run_local_pipeline()