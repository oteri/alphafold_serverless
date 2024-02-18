"""Performs the prediction task."""
import os
import random
import sys
from typing import Any
import numpy as np  # type: ignore

import jax.numpy as jnp  # type: ignore
from absl import logging  # type: ignore
from alphafold.data import pipeline, pipeline_multimer  # type: ignore
from alphafold.model import config, data, model  # type: ignore
from alphafold.predict_structure import ModelsToRelax, predict_structure  # type: ignore
from alphafold.relax import relax  # type: ignore


RELAX_MAX_ITERATIONS = 0
RELAX_ENERGY_TOLERANCE = 2.39
RELAX_STIFFNESS = 10.0
RELAX_EXCLUDE_RESIDUES = []  # type: ignore
RELAX_MAX_OUTER_ITERATIONS = 3


def _jnp_to_np(output: dict[str, Any]) -> dict[str, Any]:
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
    random_seed: int = 1,
):
    """Runs the prediction.

    Args:
        precomputed_msa (str): name of the file with the MSA.
        data_dir (str): Directory with the weights.
        output_dir (str): Directory the output will be saved to.
        num_multimer_predictions_per_model (int, optional): How many multimer predictions must be carried on for each model. Defaults to 5.
        models_to_relax (int, optional): What model to relax. Defaults to ModelsToRelax.BEST.
        model_preset (str, optional): Wat model to use. Defaults to "monomer".
        benchmark (bool, optional): Running benchmark. Defaults to False.
        use_gpu_relax (bool, optional): True to use GPU to relax the selected structures. Defaults to True.
        random_seed (int, optional): Seed to perform the task. Defaults to 1.
    """
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


# def run_prediction_test(
#     precomputed_msa: str,
#     data_dir: str,
#     output_dir: str,
#     num_multimer_predictions_per_model: int = 5,
#     models_to_relax: int = 0,
#     model_preset: str = "monomer",
#     benchmark: bool = False,
#     use_gpu_relax: bool = True,
#     random_seed: int = None,
# ):
#     """Testing function. It mokes the creation of a pdb file.

#     Args:
#         Look at run_prediction for a full description
#     """
#     if random_seed is not None:
#         # Set the random seed here if your prediction logic uses random numbers
#         pass

#     o_dir = Path(output_dir) / "msa"
#     o_dir.mkdir(parents=True, exist_ok=True)

#     try:
#         logging.warning(f"Writing: {o_dir / 'ranked_0.pdb'}")
#         with open(o_dir / "ranked_0.pdb", "w") as f_out:
#             f_out.write("ATOM test1")
#     except OSError as e:
#         logging.error(f"Error writing to file: {e}")
