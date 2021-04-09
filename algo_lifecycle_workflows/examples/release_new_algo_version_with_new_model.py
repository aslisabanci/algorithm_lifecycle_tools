import logging
import shutil
import sys
import os

sys.path.append(os.path.abspath("./algo_lifecycle_workflows"))
from algo_lifecycle_tools import model_ops

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.realpath(__file__))
    local_model_path = os.path.join(current_dir, "models/model-a.joblib")
    # s3_model_path = (
    #     "s3+cstest://asli-s3-bucket/model_545b1f53436d2739be8b1d9d03b93bd3e27f3aa8.pkl"
    # )
    # algorithmia_model_path = "data://asli/credit_card_approval/model.joblib"

    model_publisher = model_ops.ModelPublisher(
        api_key=os.environ.get("ALGORITHMIA_API_KEY", None),
        username="asli",
        algo_name="credit_card_approval",
    )
    model_publisher.release_algo_with_model(
        model_path=local_model_path,
        should_upload_model=True,
        test_input={
            "owns_home": 1,
            "child_one": 0,
            "child_two_plus": 0,
            "has_work_phone": 0,
            "age_high": 0,
            "age_highest": 1,
            "age_low": 0,
            "age_lowest": 0,
            "employment_duration_high": 0,
            "employment_duration_highest": 0,
            "employment_duration_low": 0,
            "employment_duration_medium": 0,
            "occupation_hightech": 0,
            "occupation_office": 1,
            "family_size_one": 1,
            "family_size_three_plus": 0,
            "housing_coop_apartment": 0,
            "housing_municipal_apartment": 0,
            "housing_office_apartment": 0,
            "housing_rented_apartment": 0,
            "housing_with_parents": 0,
            "education_higher_education": 0,
            "education_incomplete_higher": 0,
            "education_lower_secondary": 0,
            "marital_civil_marriage": 0,
            "marital_separated": 0,
            "marital_single_not_married": 1,
            "marital_widow": 0,
        },
    )

