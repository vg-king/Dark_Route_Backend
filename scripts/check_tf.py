import sys
print('Python:', sys.version)

try:
    import tensorflow as tf
    print('TF:', tf.__version__)
except Exception as e:
    print('TF import failed:', repr(e))

try:
    from tensorflow.keras.models import load_model
    print('Keras load_model available:', bool(load_model))
except Exception as e:
    print('Keras import failed:', repr(e))

import os
from pathlib import Path
model_path = Path(__file__).resolve().parent.parent / 'mobilenetv2_image_classifier.h5'
print('Model path exists:', model_path.exists())
print('Model path:', str(model_path))

if model_path.exists():
    try:
        # attempt to load model briefly without running inference
        m = load_model(str(model_path))
        print('Model loaded OK:', bool(m))
    except Exception as e:
        print('Model load error:', repr(e))
