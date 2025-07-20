import os
import pandas as pd
from arize.pandas.logger import Client
from arize.utils.types import Schema, ModelTypes, Environments
from dotenv import load_dotenv

load_dotenv()
ARIZE_SPACE_ID = os.getenv("ARIZE_SPACE_ID")
ARIZE_API_KEY = os.getenv("ARIZE_API_KEY")

# Simulate drift: all predictions and actuals are 'virginica'
classes = ["setosa", "versicolor", "virginica"]

def make_virginica_probs():
    return {c: 1.0 if c == "virginica" else 0.0 for c in classes}

def dict_to_list_of_dicts(d):
    return [{"class_name": k, "score": float(v)} for k, v in d.items()]

# Create a small drifted DataFrame
drifted_data = pd.DataFrame({
    "sepal_length": [7.1, 7.2, 7.3, 7.4, 7.5],
    "sepal_width": [3.0, 3.1, 3.2, 3.3, 3.4],
    "petal_length": [5.9, 6.0, 6.1, 6.2, 6.3],
    "petal_width": [2.1, 2.2, 2.3, 2.4, 2.5],
})

drifted_data["prediction_scores"] = [dict_to_list_of_dicts(make_virginica_probs()) for _ in range(len(drifted_data))]
drifted_data["actual_scores"] = [dict_to_list_of_dicts(make_virginica_probs()) for _ in range(len(drifted_data))]

client = Client(space_id=ARIZE_SPACE_ID, api_key=ARIZE_API_KEY)

schema = Schema(
    prediction_score_column_name="prediction_scores",
    actual_score_column_name="actual_scores"
)

response = client.log(
    dataframe=drifted_data,
    model_id="iris-model",
    model_version="v1",
    model_type=ModelTypes.MULTI_CLASS,
    environment=Environments.PRODUCTION,
    schema=schema
)

print("Arize log response:", response)