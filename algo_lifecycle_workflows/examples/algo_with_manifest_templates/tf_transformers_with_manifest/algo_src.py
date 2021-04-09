import Algorithmia
import tensorflow as tf
from transformers import (
    AlbertConfig,
    TFAlbertForSequenceClassification,
    AlbertTokenizer,
)
import zipfile
from pathlib import Path
import hashlib
import json
from os import path, listdir
import re


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
    if path.exists(manifest_path):
        with open(manifest_path) as json_file:
            manifest = json.load(json_file)
    return manifest


def download_zipped_model(manifest, assert_hash=False):
    """Loads the model object from the file at model_filepath key in config dict"""
    zipped_model_path = manifest["model_filepath"]
    zipped_model = client.file(zipped_model_path).getFile().name
    if assert_hash:
        assert_model_md5(zipped_model)
    return zipped_model_path


def load_model_and_tokenizer(manifest):
    zipped_model_path = download_zipped_model(manifest, assert_hash=True)
    unzipped_model_dir = get_unzipped_dir_path(zipped_model_path)
    config = AlbertConfig.from_pretrained(unzipped_model_dir)
    model = TFAlbertForSequenceClassification.from_pretrained(
        unzipped_model_dir, config=config
    )
    tokenizer = AlbertTokenizer.from_pretrained(unzipped_model_dir)
    return model, tokenizer


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


def get_unzipped_dir_path(zip_path_in_collection):
    zip_in_collection = client.file(zip_path_in_collection).getFile().name
    output_dir = "/tmp/model"
    try:
        zipped_file = zipfile.ZipFile(zip_in_collection, "r")
        zipped_file.extractall(output_dir)
        zipped_file.close()
    except Exception as e:
        print("Exception occurred while creating dir: {}".format(e))
    unzipped_folders = [f for f in listdir(output_dir) if re.match(r"^__", f) is None]
    assert len(unzipped_folders) == 1
    return path.join(output_dir, unzipped_folders[0])


client = Algorithmia.client()
manifest = load_model_manifest()
model, tokenizer = load_model_and_tokenizer(manifest)


# API calls will begin at the apply() method, with the request body passed as 'input'
# For more details, see algorithmia.com/developers/algorithm-development/languages
def apply(input):
    text = input["text"]
    input_ids = tf.constant(tokenizer.encode(text))[None, :]  # Batch size 1
    outputs = model(input_ids)
    response_dict = {
        "input_ids": input_ids.numpy().tolist(),
        "outputs": outputs[0].numpy().tolist(),
    }
    return response_dict
