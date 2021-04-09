import Algorithmia
import numpy as np
from joblib import load
import os.path
from pathlib import Path
import hashlib
import json


def load_model_manifest(rel_path="model_manifest.json"):
    """Loads the model manifest file as a dict. 
    A manifest file has the following structure:
    {
      "model_filepath": Uploaded model path on Algorithmia data collection
      "model_md5_hash": MD5 hash of the uploaded model file
      "model_origin_ref": Informative note about the model source
      "model_uploaded_utc": UTC timestamp of the automated model upload
    }
    """
    manifest = []
    manifest_path = "{}/{}".format(Path(__file__).parents[1], rel_path)
    if os.path.exists(manifest_path):
        with open(manifest_path) as json_file:
            manifest = json.load(json_file)
    return manifest


def load_model(manifest, assert_hash=False):
    """Loads the model object from the file at model_filepath key in config dict"""
    model_path = manifest["model_filepath"]
    model = load(client.file(model_path).getFile().name)
    if assert_hash:
        assert_model_md5(model)
    return model, model_path


def assert_model_md5(model_file):
    """
    Calculates the loaded model file's MD5 and compares the actual file hash with the hash on the model manifest
    """
    md5_hash = None
    DIGEST_BLOCK_SIZE = 128 * 64
    with open(model_file, "rb") as f:
        hasher = hashlib.md5()
        buf = f.read(DIGEST_BLOCK_SIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(DIGEST_BLOCK_SIZE)
        md5_hash = hasher.hexdigest()
    assert manifest["model_md5_hash"] == md5_hash
    print("Model file's runtime MD5 hash equals to the upload time hash, great!")


client = Algorithmia.client()
manifest = load_model_manifest()
model, model_path = load_model(manifest, assert_hash=True)


def apply(input):
    params = np.array(
        [
            input.get("gender", 0),
            input.get("owns_home", 1),
            input.get("child_one", 0),
            input.get("child_two_plus", 0),
            input.get("has_work_phone", 0),
            input.get("age_high", 0),
            input.get("age_highest", 1),
            input.get("age_low", 0),
            input.get("age_lowest", 0),
            input.get("employment_duration_high", 0),
            input.get("employment_duration_highest", 0),
            input.get("employment_duration_low", 0),
            input.get("employment_duration_medium", 0),
            input.get("occupation_hightech", 0),
            input.get("occupation_office", 1),
            input.get("family_size_one", 1),
            input.get("family_size_three_plus", 0),
            input.get("housing_coop_apartment", 0),
            input.get("housing_municipal_apartment", 0),
            input.get("housing_office_apartment", 0),
            input.get("housing_rented_apartment", 0),
            input.get("housing_with_parents", 0),
            input.get("education_higher_education", 0),
            input.get("education_incomplete_higher", 0),
            input.get("education_lower_secondary", 0),
            input.get("marital_civil_marriage", 0),
            input.get("marital_separated", 0),
            input.get("marital_single_not_married", 1),
            input.get("marital_widow", 0),
        ]
    ).reshape(1, -1)

    risk_score = model.predict_proba(params)
    risk_score = round(float(risk_score[0][1]), 2)
    approved = int(1 - model.predict(params)[0])

    return {
        "risk_score": risk_score,
        "approved": approved,
        "predicting_model": model_path,
    }

