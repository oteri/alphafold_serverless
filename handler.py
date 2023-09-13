import json
import os
import random
import sys
import tempfile
from typing import Any, Dict

import jax.numpy as jnp
import numpy as np
import runpod
from absl import logging
from alphafold.data import pipeline, pipeline_multimer
from alphafold.model import config, data, model
from alphafold.predict_structure import ModelsToRelax, predict_structure
from alphafold.relax import relax

WORKDIR  = os.environ.get("WORKDIR", "/data/")
PARAM_DIR = os.environ.get("PARAM_DIR", "/data/")
logging.set_verbosity(logging.INFO)


RELAX_MAX_ITERATIONS = 0
RELAX_ENERGY_TOLERANCE = 2.39
RELAX_STIFFNESS = 10.0
RELAX_EXCLUDE_RESIDUES = []
RELAX_MAX_OUTER_ITERATIONS = 3


def _jnp_to_np(output: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively changes jax arrays to numpy arrays."""
    for k, v in output.items():
        if isinstance(v, dict):
            output[k] = _jnp_to_np(v)
        elif isinstance(v, jnp.ndarray):
            output[k] = np.array(v)
    return output


def run_prediction(
    precomputed_msa: str,
    data_dir: str,
    output_dir: str,
    num_multimer_predictions_per_model: int = 5,
    models_to_relax: int = ModelsToRelax.BEST,
    model_preset: str = "monomer",
    benchmark: bool = False,
    use_gpu_relax: bool = True,
    random_seed: int = None,
):
    run_multimer_system = "multimer" in model_preset

    if model_preset == "monomer_casp14":
        num_ensemble = 8
    else:
        num_ensemble = 1

    monomer_data_pipeline = pipeline.DataPipeline()

    if run_multimer_system:
        num_predictions_per_model = num_multimer_predictions_per_model
        data_pipeline = pipeline_multimer.DataPipeline()
    else:
        num_predictions_per_model = 1
        data_pipeline = monomer_data_pipeline

    model_runners = {}
    model_names = config.MODEL_PRESETS[model_preset]
    for model_name in model_names:
        model_config = config.model_config(model_name)
        if run_multimer_system:
            model_config.model.num_ensemble_eval = num_ensemble
        else:
            model_config.data.eval.num_ensemble = num_ensemble
        model_params = data.get_model_haiku_params(
            model_name=model_name, data_dir=data_dir
        )
        model_runner = model.RunModel(model_config, model_params)
        for i in range(num_predictions_per_model):
            model_runners[f"{model_name}_pred_{i}"] = model_runner

    logging.info("Have %d models: %s", len(model_runners), list(model_runners.keys()))

    amber_relaxer = relax.AmberRelaxation(
        max_iterations=RELAX_MAX_ITERATIONS,
        tolerance=RELAX_ENERGY_TOLERANCE,
        stiffness=RELAX_STIFFNESS,
        exclude_residues=RELAX_EXCLUDE_RESIDUES,
        max_outer_iterations=RELAX_MAX_OUTER_ITERATIONS,
        use_gpu=use_gpu_relax,
    )

    if random_seed is None:
        random_seed = random.randrange(sys.maxsize // len(model_runners))
    logging.info("Using random seed %d for the data pipeline", random_seed)

    basename = os.path.basename(precomputed_msa)  # Get the filename with extension
    fasta_name = os.path.splitext(basename)[0]  # Remove the extension

    # Predict structure for each of the sequences.
    predict_structure(
        precomputed_msa=precomputed_msa,
        fasta_name=fasta_name,
        output_dir_base=output_dir,
        data_pipeline=data_pipeline,
        model_runners=model_runners,
        amber_relaxer=amber_relaxer,
        benchmark=benchmark,
        random_seed=random_seed,
        models_to_relax=models_to_relax,
    )


def handler(event):
    # Save event.msa to WORKDIR/msa.fasta
    job_dir = tempfile.mkdtemp(dir=WORKDIR)

    msa_file_path = os.path.join(job_dir, "msa.fasta")
    with open(msa_file_path, "w") as file:
        file.write(event["input"]["msa"])

    run_prediction(precomputed_msa=msa_file_path, output_dir=job_dir, data_dir=PARAM_DIR)
    # Read the output file.
    # runpod doesn't allow to manage more than 2MB so only the best result is returned.
    # If you want to store more, use a bucket and the object id instead.
    output_file_path = os.path.join(job_dir, "msa/ranked_0.pdb")
    with open(output_file_path, "r") as file:
        output_content = file.read()
        return json.dumps({"structure": output_content})


runpod.serverless.start({"handler": handler})
