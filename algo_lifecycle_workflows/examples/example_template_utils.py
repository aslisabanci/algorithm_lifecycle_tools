import os
import shutil


def copy_example_algo_templates(algo_name, repo_path, template_dir_name):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    manifest_path = os.path.join(
        current_dir, "algo_with_manifest_templates/model_manifest.json"
    )
    shutil.copy(manifest_path, repo_path)
    algo_src_path = os.path.join(
        current_dir, f"algo_with_manifest_templates/{template_dir_name}/algo_src.py"
    )
    shutil.copy(algo_src_path, os.path.join(repo_path, f"src/{algo_name}.py"))
    algo_req_path = os.path.join(
        current_dir,
        f"algo_with_manifest_templates/{template_dir_name}/requirements.txt",
    )
    shutil.copy(algo_req_path, repo_path)
