import argparse
import sys
from typing import List
import torch
import tensorflow as tf
from pathlib import Path
from models.experimental import attempt_load
import onnx
from onnx_tf.backend import prepare

# https://github.com/WongKinYiu/yolov7/pull/1156

BATCH_SIZE = 1


def _torch_to_onnx(torch_model_path: Path, img_size: List[int], output_path: Path):
    model = attempt_load(torch_model_path, map_location=torch.device("cpu"))
    model.eval()
    sample_input = torch.rand((BATCH_SIZE, 3, *img_size))
    torch.onnx.export(
        model,
        sample_input,
        output_path,
        verbose=False,
        input_names=["input"],
        output_names=["output"],
        opset_version=12,
    )


def _onnx_to_tf(onnx_model_path: Path, output_path: Path):
    if not Path(output_path).is_dir():
        onnx_model = onnx.load(onnx_model_path)
        tf_rep = prepare(onnx_model)
        tf_rep.export_graph(output_path)


def _tf_to_tflite(tf_model_path: Path, output_path: Path):
    converter = tf.lite.TFLiteConverter.from_saved_model(str(tf_model_path))
    tflite_model = converter.convert()
    with open(output_path, "wb") as f:
        f.write(tflite_model)


def torch_to_tflite(torch_model_path: Path, img_size: List[int], output_dir: Path):
    output_dir = output_dir if isinstance(output_dir, Path) else Path(output_dir)
    torch_model_path = torch_model_path if isinstance(torch_model_path, Path) else Path(torch_model_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    onnx_model_path = output_dir / f"{torch_model_path.stem}.onnx"
    tf_model_path = output_dir / f"{torch_model_path.stem}.pb"
    _torch_to_onnx(torch_model_path, img_size, onnx_model_path)
    _onnx_to_tf(onnx_model_path, tf_model_path)
    _tf_to_tflite(tf_model_path, output_dir / f"{torch_model_path.stem}.tflite")
    keras_model = tf.saved_model.load("D:/Users/Documents/GitHub/YoLov7/runs/train/exp/weights/deploy_bestnew.tflite/deploy_best.pb/", tags=None, options=None)
    return keras_model

def parse_args(cli_args=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-tp",
        "--torch-model-path",
        type=Path,
        required=True,
        help="Path to the torch model to be converted.",
    )
    parser.add_argument(
        "--img-size",
        nargs="+",
        default=(640, 640),
        help="Image size for creating sample input for torch model.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        required=True,
        help="Path to save the outputs.",
    )
    args = parser.parse_args(cli_args)
    return args


if __name__ == "__main__":
    torch_to_tflite(**vars(parse_args()))