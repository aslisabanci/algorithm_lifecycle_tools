import logging
import sys
import os
import example_template_utils

sys.path.append(os.path.abspath("./algo_lifecycle_workflows"))
from algo_lifecycle_tools import model_ops

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.realpath(__file__))
    local_model_path = os.path.join(
        current_dir, "models/albert_model_and_tokenizer.zip"
    )

    algo_name = "yiptf"
    model_publisher = model_ops.ModelPublisher(
        api_key=os.environ.get("ALGORITHMIA_API_KEY", None),
        username="asli",
        algo_name=algo_name,
    )

    model_publisher.create_algorithm_on_env("Python 3.8 + TensorFlow GPU 2.3")
    example_template_utils.copy_example_algo_templates(
        algo_name, model_publisher.repo_path, "tf_transformers_with_manifest"
    )
    model_publisher.release_algo_with_model(
        local_model_path,
        should_upload_model=True,
        test_input={"text": "How is it going?"},
    )
