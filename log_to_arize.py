import os
import pandas as pd
from arize.pandas.logger import Client
from arize.utils.types import Schema, ModelTypes, Environments
from dotenv import load_dotenv

load_dotenv()
ARIZE_SPACE_ID = os.getenv("ARIZE_SPACE_ID")
ARIZE_API_KEY = os.getenv("ARIZE_API_KEY")

df = pd.read_csv("iris.csv")
classes = df["species"].unique().tolist()

def make_dummy_probs(row):
    return {c: 1.0 if row["species"] == c else 0.0 for c in classes}

def make_actual_onehot(row):
    return {c: 1.0 if row["species"] == c else 0.0 for c in classes}

df["prediction_scores"] = df.apply(make_dummy_probs, axis=1)
df["actual_scores"] = df.apply(make_actual_onehot, axis=1)

def dict_to_list_of_dicts(d):
    return [{"class_name": k, "score": float(v)} for k, v in d.items()]

df["prediction_scores"] = df["prediction_scores"].apply(dict_to_list_of_dicts)
df["actual_scores"] = df["actual_scores"].apply(dict_to_list_of_dicts)

client = Client(space_id=ARIZE_SPACE_ID, api_key=ARIZE_API_KEY)

schema = Schema(
    prediction_score_column_name="prediction_scores",
    actual_score_column_name="actual_scores"
)

response = client.log(
    dataframe=df,
    model_id="iris-model",
    model_version="v1",
    model_type=ModelTypes.MULTI_CLASS,
    environment=Environments.PRODUCTION,
    schema=schema
)

print("Arize log response:", response)