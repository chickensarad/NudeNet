import os
import cv2
import tarfile
import pydload
import logging
import numpy as np
import onnxruntime
from .video_utils import get_interest_frames_from_video
from .image_utils import load_images
from PIL import Image as pil_image


class Classifier:
    """
    Class for loading model and running predictions.
    For example on how to use take a look the if __name__ == '__main__' part.
    """

    nsfw_model = None

    def __init__(self):
        """
        model = Classifier()
        """
        url = "https://github.com/notAI-tech/NudeNet/releases/download/v0/classifier_model.onnx"
        home = os.path.expanduser("~")
        model_folder = os.path.join(home, ".NudeNet/")
        if not os.path.exists(model_folder):
            os.mkdir(model_folder)

        model_path = os.path.join(model_folder, os.path.basename(url))

        if not os.path.exists(model_path):
            print("Downloading the checkpoint to", model_path)
            pydload.dload(url, save_to_path=model_path, max_time=None)

        self.nsfw_model = onnxruntime.InferenceSession(model_path)

    def classify_video(
        self,
        video_path,
        batch_size=4,
        image_size=(256, 256),
        categories=["unsafe", "safe"],
    ):
        frame_indices = None
        frame_indices, frames, fps, video_length = get_interest_frames_from_video(
            video_path
        )
        logging.debug(
            f"VIDEO_PATH: {video_path}, FPS: {fps}, Important frame indices: {frame_indices}, Video length: {video_length}"
        )

        frames, frame_names = load_images(frames, image_size, image_names=frame_indices)

        if not frame_names:
            return {}

        preds = []
        model_preds = []
        while len(frames):
            _model_preds = self.nsfw_model.run(
                [self.nsfw_model.get_outputs()[0].name],
                {self.nsfw_model.get_inputs()[0].name: frames[:batch_size]},
            )[0]
            model_preds.append(_model_preds)
            preds += np.argsort(_model_preds, axis=1).tolist()
            frames = frames[batch_size:]

        probs = []
        for i, single_preds in enumerate(preds):
            single_probs = []
            for j, pred in enumerate(single_preds):
                single_probs.append(
                    model_preds[int(i / batch_size)][int(i % batch_size)][pred]
                )
                preds[i][j] = categories[pred]

            probs.append(single_probs)

        return_preds = {
            "metadata": {
                "fps": fps,
                "video_length": video_length,
                "video_path": video_path,
            },
            "preds": {},
        }

        for i, frame_name in enumerate(frame_names):
            return_preds["preds"][frame_name] = {}
            for _ in range(len(preds[i])):
                return_preds["preds"][frame_name][preds[i][_]] = probs[i][_]

        return return_preds
    
def classify(
        self,
        image,
        batch_size=4,
        categories=["unsafe", "safe"],
    ):
        """
        inputs:
            image_paths: list of image paths or can be a string too (for single image)
            batch_size: batch_size for running predictions
            image_size: size to which the image needs to be resized
            categories: since the model predicts numbers, categories is the list of actual names of categories
        """

        preds = []
        model_preds = []
        _model_preds = self.nsfw_model.run(
            [self.nsfw_model.get_outputs()[0].name],
            {self.nsfw_model.get_inputs()[0].name: 1},
        )[0]
        model_preds.append(_model_preds)
        preds += np.argsort(_model_preds, axis=1).tolist()

        probs = []
        for i, single_preds in enumerate(preds):
            single_probs = []
            for j, pred in enumerate(single_preds):
                single_probs.append(
                    model_preds[int(i / batch_size)][int(i % batch_size)][pred]
                )
                preds[i][j] = categories[pred]

            probs.append(single_probs)


        return probs[i][_]


if __name__ == "__main__":
    m = Classifier()

    while 1:
        print(
            "\n Enter single image path or multiple images seperated by || (2 pipes) \n"
        )
        images = input().split("||")
        images = [image.strip() for image in images]
        print(m.predict(images), "\n")
