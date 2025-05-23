import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from urllib.parse import urlparse
import mlflow
import mlflow.sklearn
from pathlib import Path

from mlProject.utils.common import save_json
from mlProject.entity.config_entity import ModelEvaluationConfig
 
class ModelEvaluation:
    def __init__(self, config: ModelEvaluationConfig):
        self.config = config
    
    def eval_metrics(self, actual, predicted):
        rmse = np.sqrt(mean_squared_error(actual, predicted))
        r2 = r2_score(actual, predicted)
        mae = mean_absolute_error(actual, predicted)
        return rmse, r2, mae
    
    def log_into_mlflow(self):
        test_data = pd.read_csv(self.config.test_data_path)
        model = joblib.load(self.config.model_path)
        
        X_test = test_data.drop(self.config.target_col, axis=1)
        y_test = test_data[self.config.target_col]
         
        mlflow.set_registry_uri(self.config.mlflow_uri)
        tracking_url_type_store = urlparse(mlflow.get_tracking_uri()).scheme
        
        with mlflow.start_run():
            predicted_qualities = model.predict(X_test)
            (rmse, r2, mae) = self.eval_metrics(y_test, predicted_qualities)
            
            # Save metrics locally
            scores = {"rmse": rmse, "r2": r2, "mae": mae} 
            save_json(path=Path(self.config.metric_file_name), data=scores)  
            
            mlflow.log_params(self.config.all_params)
            mlflow.log_metric("rmse", rmse)
            mlflow.log_metric("r2", r2)
            mlflow.log_metric("mae", mae)
            
            # Register model only if not using file store
            if tracking_url_type_store != "file":
                
                # Register the model in the MLflow Model Registry
                # Please refer to the doc for more details:
                # https://mlflow.org/docs/latest/model-registry.html#api-workflow
                
                mlflow.sklearn.log_model(model, "model", registered_model_name="ElasticNetModel")
            else:
                mlflow.sklearn.log_model(model, "model")
