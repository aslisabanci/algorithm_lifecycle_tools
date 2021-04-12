import os
import sys

sys.path.append(os.path.abspath("./algo_lifecycle_workflows"))
from algo_lifecycle_tools import model_ops


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.realpath(__file__))
    local_envs_path = os.path.join(current_dir, "available_envs.json")

    model_publisher = model_ops.ModelPublisher(
        api_key=os.environ.get("ALGORITHMIA_API_KEY", None),
        username="asli",
        algo_name=algo_name,
    )

    model_publisher.write_algo_environments_json(local_envs_path)