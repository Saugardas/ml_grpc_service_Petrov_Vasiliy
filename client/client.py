import grpc
import sys
import os

from protos import model_pb2, model_pb2_grpc

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = model_pb2_grpc.PredictionServiceStub(channel)

        # Health check
        try:
            health_response = stub.Health(model_pb2.HealthRequest(), timeout=2)
            print("Health:", health_response)
        except grpc.RpcError as e:
            print(f"Health check failed: {e}")
            return

        # Predict
        try:
            predict_request = model_pb2.PredictRequest(
                sepal_length=3.7,
                sepal_width=2.4
            )
            predict_response = stub.Predict(predict_request, timeout=5)
            print("Predict:", predict_response)
        except grpc.RpcError as e:
            print(f"Prediction failed: {e}")
            return

if __name__ == "__main__":
    run()
