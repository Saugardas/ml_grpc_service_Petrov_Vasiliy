import os
import pickle
import numpy as np
import grpc
from concurrent import futures

from protos import model_pb2, model_pb2_grpc


# Глобальные переменные
_model = None
_scaler = None
_class_names = None
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0.0")

def load_artifacts():
    global _model, _scaler, _class_names
    model_path = os.getenv("MODEL_PATH", "/app/models/model.pkl")
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")
    
    model_dir = os.path.dirname(model_path)
    scaler_path = os.path.join(model_dir, "scaler.pkl")
    class_names_path = os.path.join(model_dir, "class_names.pkl")

    print("Загрузка моделей")
    with open(model_path, "rb") as f:
        _model = pickle.load(f)
    with open(scaler_path, "rb") as f:
        _scaler = pickle.load(f)
    with open(class_names_path, "rb") as f:
        _class_names = pickle.load(f)
    print("Модели загружены")

class PredictionService(model_pb2_grpc.PredictionServiceServicer):
    def Health(self, request, context):
        return model_pb2.HealthResponse(
            status="ok",
            model_version=MODEL_VERSION
        )

    def Predict(self, request, context):
        if _model is None or _scaler is None or _class_names is None:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Model artifacts not loaded")
            return model_pb2.PredictResponse()

        try:
            features = np.array([[request.sepal_length, request.sepal_width]])
            features_scaled = _scaler.transform(features)
            proba = _model.predict_proba(features_scaled)[0]
            confidence = float(proba.max())
            pred_index = int(proba.argmax())
            prediction = _class_names[pred_index]

            return model_pb2.PredictResponse(
                prediction=prediction,
                confidence=confidence,
                model_version=MODEL_VERSION
            )
        except Exception as e:
            print(f"Ошибка Predct: {e}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return model_pb2.PredictResponse()

def serve():
    load_artifacts()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    model_pb2_grpc.add_PredictionServiceServicer_to_server(PredictionService(), server)
    server.add_insecure_port("[::]:50051")
    print("Порт 50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
