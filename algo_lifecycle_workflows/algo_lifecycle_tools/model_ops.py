from . import repo_ops
import Algorithmia
from retry import retry
import os
import json
import hashlib
import logging
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class ModelPublisher:
    def __init__(
        self,
        api_key,
        username,
        algo_name,
        algo_api_addr="https://api.algorithmia.com",
        model_manifest="model_manifest.json",
        tmp_repo_path="./",
    ):
        self.api_key = api_key
        self.username = username
        self.algo_name = algo_name
        self.algo_api_addr = algo_api_addr

        self.model_manifest = model_manifest
        self.tmp_repo_path = tmp_repo_path

        self.algo_namespace = f"{username}/{algo_name}"
        self.algorithmia_data_path = f"data://{username}/{algo_name}"
        self.algo_client = Algorithmia.client(self.api_key)
        self.algo = self.algo_client.algo(self.algo_namespace)

    def release_algo_with_model(
        self,
        model_path,
        should_upload_model=False,
        test_input=None,
        publish_params=None,
    ):
        self._clone_or_pull_algorithm_repo()
        model_hash = None
        if should_upload_model:
            algorithmia_path = self._upload_model_to_algorithmia(model_path)
            model_hash = self._calculate_model_md5(model_path)
        else:
            algorithmia_path = model_path
        self._update_model_manifest(algorithmia_path, model_hash)
        self._push_algo_to_algorithmia()
        if test_input is not None:
            self._call_latest_algo_version(test_input)

        if publish_params is None:
            publish_params = {
                "version_info": {
                    "sample_input": json.dumps(test_input),
                    "version_type": "minor",
                    "release_notes": "Updated model manifest via Python workflow",
                },
                "details": {"label": self.algo_name},
                "settings": {"algorithm_callability": "private"},
            }

        self.algo.publish(
            settings=publish_params["settings"],
            version_info=publish_params["version_info"],
            details=publish_params["details"],
        )
        latest_version = self.algo.info().version_info.semantic_version
        logger.info(f"Released {latest_version} version of {self.algo_name}. Enjoy!")

    def _clone_or_pull_algorithm_repo(self):
        self.repo, self.repo_path = repo_ops.clone_or_pull_repo(
            self.api_key,
            self.username,
            self.algo_name,
            self.algo_api_addr,
            self.tmp_repo_path,
        )

    def _push_algo_to_algorithmia(self):
        repo_ops.push_repo(self.repo)

    def _calculate_model_md5(self, model_path):
        DIGEST_BLOCK_SIZE = 128 * 64
        md5 = hashlib.md5()
        md5_hash = None
        try:
            with open(model_path, "rb") as f:
                for chunk in iter(lambda: f.read(DIGEST_BLOCK_SIZE), b""):
                    md5.update(chunk)
            md5_hash = md5.hexdigest()
        except Exception as e:
            print(f"An exception occurred while getting MD5 hash of file: {e}")
        return md5_hash

    def _upload_model_to_algorithmia(self, model_path):
        if not self.algo_client.dir(self.algorithmia_data_path).exists():
            self.algo_client.dir(self.algorithmia_data_path).create()
        model_name = os.path.basename(model_path)
        algorithmia_upload_path = "{}/{}".format(self.algorithmia_data_path, model_name)
        self.algo_client.file(algorithmia_upload_path).putFile(model_path)
        return algorithmia_upload_path

    def _update_model_manifest(self, algorithmia_upload_path, model_hash):
        manifest = []
        manifest_path = "{}/{}/{}".format(
            self.tmp_repo_path, self.algo_name, self.model_manifest
        )
        if os.path.exists(manifest_path):
            with open(manifest_path) as json_file:
                manifest = json.load(json_file)
        manifest["model_filepath"] = algorithmia_upload_path
        if model_hash is not None:
            manifest["model_md5_hash"] = model_hash
        with open(manifest_path, "w+") as new_manifest_file:
            json.dump(manifest, new_manifest_file)
        logger.info(
            "Updated model_manifest with new model metadata:{}".format(manifest)
        )

    # Call algorithm until the algo hash endpoint becomes available, up to 10 seconds
    @retry(Algorithmia.errors.AlgorithmException, tries=10, delay=1)
    def _call_latest_algo_version(self, input):
        latest_algo_hash = self.algo.info().version_info.git_hash
        latest_algo = self.algo_client.algo(
            "{}/{}".format(self.algo_namespace, latest_algo_hash)
        )
        latest_algo.set_options(timeout=60, stdout=False)
        algo_pipe_result = latest_algo.pipe(input)
        return algo_pipe_result

    def create_algorithm_on_env(self, env_display_name):
        algo_env_id = self._get_algo_env_id_by_name(env_display_name)
        if algo_env_id is not None:
            details = {
                "label": self.algo_name,
            }
            settings = {
                "algorithm_environment": algo_env_id,
                "source_visibility": "closed",
                "license": "apl",
                "network_access": "full",
                "pipeline_enabled": True,
            }
            self.algo.create(details=details, settings=settings)
            logger.info(f"{self.algo_name} algorithm created")
        else:
            logger.error(
                f"Could not fetch environment id for {env_display_name}, blocking algorithm creation. Please verify the environment display name is correct."
            )
        self._clone_or_pull_algorithm_repo()

    def _get_algo_env_id_by_name(self, env_display_name):
        envs = self._get_algo_environments()
        for env in envs:
            if str.lower(env_display_name) == str.lower(env["display_name"]):
                return env["id"]
        return None

    def _get_algo_environments(self):
        response = requests.get(
            f"{self.algo_api_addr}/webapi/v1/algorithm-environments/languages/python3/environments",
            headers={"Authorization": f"Simple {self.api_key}"},
        )
        return response.json()["environments"]

    def write_algo_environments_json(outfile="envs.json"):
        """Write environment list to JSON."""
        """
        Envs is list of dicts showing envs available on cluster, of format:
        [{
            "id": "87a294f5-441f-41b9-a16e-209618df9612",
            "display_name": "Python 3.7",
            ...
        },]
        """
        envs_long = self._get_algo_environments()
        envs_short = self._subset_environment_props(envs_long)
        with open(outfile, "w") as f:
            json.dump(envs, f)
        logger.info("{} environments available, listed in {}".format(
            len(envs), outfile))
        return None

    @staticmethod
    def _subset_environment_props(envs: list) -> list:
        """Subset environment details of interest for concise output.""" 
        properties = ["id", "display_name", "description", "machine_type"]
        envs_short = []
        for env in envs_long:
            env_props = {}
            for prop in properties:
                env_props[prop] = env[prop]
            envs_short.append(env_props)
        return envs_short


