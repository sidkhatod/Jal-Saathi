"""
Packaging build script for the Decision Engine Lambda.
Bundles shared code (data/ loaders, rl/ envs) into a standalone Lambda deployment artifact
without duplicating logic in source control.
"""

import os
import shutil
import zipfile
import argparse

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def build_lambda_package(output_dir: str = None, zip_output: bool = True) -> str:
    if output_dir is None:
        output_dir = os.path.join(ROOT_DIR, "backend", ".lambda_decide_dist")

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Building Lambda package into: {output_dir}")

    # 1. Copy backend/decide
    decide_src = os.path.join(ROOT_DIR, "backend", "decide")
    decide_dst = os.path.join(output_dir, "decide")
    shutil.copytree(decide_src, decide_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "build.py"))

    # 2. Copy shared data modules
    data_dst = os.path.join(output_dir, "data")
    os.makedirs(data_dst, exist_ok=True)
    
    # Copy data subpackages
    for sub in ["crops", "advisories", "fertiliser", "processed"]:
        sub_src = os.path.join(ROOT_DIR, "data", sub)
        if os.path.exists(sub_src):
            shutil.copytree(sub_src, os.path.join(data_dst, sub), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    # Copy data python files
    for pyf in ["soil_hydraulics.py", "soil_api.py", "config.py", "weather.py"]:
        pyf_src = os.path.join(ROOT_DIR, "data", pyf)
        if os.path.exists(pyf_src):
            shutil.copy2(pyf_src, os.path.join(data_dst, pyf))

    # 3. Copy shared rl modules
    rl_dst = os.path.join(output_dir, "rl")
    os.makedirs(rl_dst, exist_ok=True)
    envs_src = os.path.join(ROOT_DIR, "rl", "envs")
    if os.path.exists(envs_src):
        shutil.copytree(envs_src, os.path.join(rl_dst, "envs"), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    utils_src = os.path.join(ROOT_DIR, "rl", "utils.py")
    if os.path.exists(utils_src):
        shutil.copy2(utils_src, os.path.join(rl_dst, "utils.py"))

    # 4. Copy models if present
    models_src = os.path.join(ROOT_DIR, "models")
    if os.path.exists(models_src):
        shutil.copytree(models_src, os.path.join(output_dir, "models"), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    print(f"Staged all shared dependencies into {output_dir}")

    # Optional: create zip artifact
    zip_path = None
    if zip_output:
        zip_path = os.path.join(ROOT_DIR, "backend", "decision_engine_lambda.zip")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(output_dir):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, output_dir)
                    zf.write(full_p, rel_p)
        print(f"Created deployment archive: {zip_path}")
        return zip_path

    return output_dir

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Package decision engine lambda.")
    parser.add_argument("--no-zip", action="store_true", help="Do not create zip archive, leave staging dir.")
    args = parser.parse_args()
    build_lambda_package(zip_output=not args.no_zip)
