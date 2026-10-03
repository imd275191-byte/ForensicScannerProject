import os
import pickle

import cv2
import pywt
import numpy as np
import torch
import torch.nn as nn

from skimage.feature import local_binary_pattern
from scipy.fft import fft2, fftshift
from scipy import ndimage


# ============================================================
# PROJECT SETTINGS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCANNER_DIR = os.path.join(
    BASE_DIR,
    "temp_scanner_model",
    "scanner"
)

MODEL_PATH = os.path.join(
    SCANNER_DIR,
    "scanner_hybrid.pth"
)

SCALER_PATH = os.path.join(
    SCANNER_DIR,
    "hybrid_feat_scaler.pkl"
)

CLASS_PATH = os.path.join(
    SCANNER_DIR,
    "hybrid_classes.pkl"
)

IMAGE_SIZE = (256, 256)

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# HYBRID CNN MODEL
# ============================================================

class HybridCNN(nn.Module):

    def __init__(self, num_classes, feat_dim):

        super().__init__()

        # Fixed high-pass filter
        hp_kernel = torch.tensor(
            [
                [
                    [-1, -1, -1],
                    [-1, 8, -1],
                    [-1, -1, -1]
                ]
            ],
            dtype=torch.float32
        ).unsqueeze(0)

        self.hp = nn.Conv2d(
            1,
            1,
            3,
            padding=1,
            bias=False
        )

        self.hp.weight.data = hp_kernel
        self.hp.weight.requires_grad = False

        # CNN
        self.cnn = nn.Sequential(

            nn.Conv2d(
                1,
                32,
                3,
                padding=1
            ),

            nn.BatchNorm2d(32),
            nn.ReLU(),

            nn.Conv2d(
                32,
                32,
                3,
                padding=1
            ),

            nn.ReLU(),

            nn.MaxPool2d(2),
            nn.Dropout(0.25),

            nn.Conv2d(
                32,
                64,
                3,
                padding=1
            ),

            nn.BatchNorm2d(64),
            nn.ReLU(),

            nn.Conv2d(
                64,
                64,
                3,
                padding=1
            ),

            nn.ReLU(),

            nn.MaxPool2d(2),
            nn.Dropout(0.25),

            nn.Conv2d(
                64,
                128,
                3,
                padding=1
            ),

            nn.BatchNorm2d(128),
            nn.ReLU(),

            nn.Conv2d(
                128,
                128,
                3,
                padding=1
            ),

            nn.ReLU(),

            nn.MaxPool2d(2),
            nn.Dropout(0.30),

            nn.Conv2d(
                128,
                256,
                3,
                padding=1
            ),

            nn.BatchNorm2d(256),
            nn.ReLU(),

            nn.AdaptiveAvgPool2d(
                (1, 1)
            )
        )

        # Handcrafted feature branch
        self.feat_fc = nn.Sequential(

            nn.Linear(
                feat_dim,
                64
            ),

            nn.BatchNorm1d(64),
            nn.ReLU(),

            nn.Dropout(0.20)
        )

        # Final classifier
        self.classifier = nn.Sequential(

            nn.Linear(
                256 + 64,
                256
            ),

            nn.ReLU(),
            nn.Dropout(0.40),

            nn.Linear(
                256,
                num_classes
            )
        )

    def forward(
        self,
        img,
        feat
    ):

        x = self.hp(img)

        x = self.cnn(x)

        x = x.view(
            x.size(0),
            -1
        )

        f = self.feat_fc(feat)

        combined = torch.cat(
            [x, f],
            dim=1
        )

        return self.classifier(
            combined
        )


# ============================================================
# LOAD IMAGE AND CREATE RESIDUAL
# ============================================================

def load_to_residual(image_path):

    img = cv2.imread(
        image_path,
        cv2.IMREAD_UNCHANGED
    )

    if img is None:

        raise ValueError(
            "Image could not be loaded."
        )

    # Convert to grayscale
    if img.ndim == 3:

        img = cv2.cvtColor(
            img,
            cv2.COLOR_BGR2GRAY
        )

    # Resize exactly like original model
    img = cv2.resize(
        img,
        IMAGE_SIZE
    )

    img = img.astype(
        np.float32
    ) / 255.0

    # Haar wavelet
    cA, (cH, cV, cD) = pywt.dwt2(
        img,
        "haar"
    )

    # Keep low-frequency component only
    cH[:] = 0
    cV[:] = 0
    cD[:] = 0

    reconstructed = pywt.idwt2(
        (cA, (cH, cV, cD)),
        "haar"
    )

    residual = (
        img - reconstructed
    ).astype(
        np.float32
    )

    return residual


# ============================================================
# SCANNER FEATURES
# ============================================================

def make_scanner_feats(res):

    # --------------------------------------------------------
    # FFT FEATURES
    # --------------------------------------------------------

    fft_img = np.abs(
        fftshift(
            fft2(res)
        )
    )

    h, w = fft_img.shape

    ch = h // 2
    cw = w // 2

    low = fft_img[
        ch - 20:ch + 20,
        cw - 20:cw + 20
    ].mean()

    mid = (
        fft_img[
            ch - 60:ch + 60,
            cw - 60:cw + 60
        ].mean()
        - low
    )

    high = (
        fft_img.mean()
        - low
        - mid
    )

    # --------------------------------------------------------
    # LBP FEATURES
    # --------------------------------------------------------

    rng = np.ptp(res)

    if rng < 1e-12:

        res_n = np.zeros_like(
            res,
            dtype=np.uint8
        )

    else:

        res_n = (
            (res - res.min())
            / (rng + 1e-8)
            * 255
        ).astype(
            np.uint8
        )

    lbp = local_binary_pattern(
        res_n,
        8,
        1.0,
        "uniform"
    )

    lbp_hist, _ = np.histogram(
        lbp,
        bins=10,
        range=(0, 10),
        density=True
    )

    # --------------------------------------------------------
    # GRADIENT FEATURES
    # --------------------------------------------------------

    gx = ndimage.sobel(
        res,
        1
    )

    gy = ndimage.sobel(
        res,
        0
    )

    gmag = np.sqrt(
        gx ** 2 + gy ** 2
    )

    # --------------------------------------------------------
    # FINAL 17 FEATURES
    # --------------------------------------------------------

    feats = (
        [low, mid, high]
        + lbp_hist.tolist()
        + [
            np.std(res),
            np.mean(np.abs(res)),
            np.std(gmag),
            np.mean(gmag)
        ]
    )

    return np.array(
        feats,
        dtype=np.float32
    )


# ============================================================
# LOAD PRETRAINED SCANNER MODEL
# ============================================================

_model = None
_classes = None
_scaler = None


def load_scanner_model():

    global _model
    global _classes
    global _scaler

    # Already loaded
    if (
        _model is not None
        and _classes is not None
        and _scaler is not None
    ):
        return (
            _model,
            _classes,
            _scaler
        )

    # Check required files
    required_files = [
        MODEL_PATH,
        SCALER_PATH,
        CLASS_PATH
    ]

    for file_path in required_files:

        if not os.path.exists(file_path):

            raise FileNotFoundError(
                f"Required model file not found:\n{file_path}"
            )

    # Load classes
    with open(
        CLASS_PATH,
        "rb"
    ) as f:

        _classes = pickle.load(f)

    # Load scaler
    with open(
        SCALER_PATH,
        "rb"
    ) as f:

        _scaler = pickle.load(f)

    # Create model
    feat_dim = _scaler.mean_.shape[0]

    _model = HybridCNN(
        len(_classes),
        feat_dim
    ).to(DEVICE)

    # Load trained weights
    state_dict = torch.load(
        MODEL_PATH,
        map_location=DEVICE
    )

    _model.load_state_dict(
        state_dict
    )

    _model.eval()

    return (
        _model,
        _classes,
        _scaler
    )


# ============================================================
# PREDICT SCANNER
# ============================================================

def predict_scanner(image_path):

    if not os.path.exists(
        image_path
    ):

        raise FileNotFoundError(
            f"Image file not found: {image_path}"
        )

    # Load model
    model, classes, scaler = (
        load_scanner_model()
    )

    # Create scanner residual
    residual = load_to_residual(
        image_path
    )

    # --------------------------------------------------------
    # IMAGE TENSOR
    # --------------------------------------------------------

    image_tensor = torch.tensor(
        residual,
        dtype=torch.float32
    ).unsqueeze(0).unsqueeze(0).to(
        DEVICE
    )

    # --------------------------------------------------------
    # HANDCRAFTED FEATURES
    # --------------------------------------------------------

    features = make_scanner_feats(
        residual
    ).reshape(
        1,
        -1
    )

    features = scaler.transform(
        features
    )

    feature_tensor = torch.tensor(
        features,
        dtype=torch.float32
    ).to(
        DEVICE
    )

    # --------------------------------------------------------
    # MODEL PREDICTION
    # --------------------------------------------------------

    with torch.no_grad():

        output = model(
            image_tensor,
            feature_tensor
        )

        probabilities = torch.softmax(
            output,
            dim=1
        ).cpu().numpy()[0]

    # Highest probability
    predicted_index = int(
        np.argmax(probabilities)
    )

    predicted_scanner = str(
        classes[predicted_index]
    )

    confidence = float(
        probabilities[predicted_index]
        * 100
    )

    # All class probabilities
    class_probabilities = {}

    for i, class_name in enumerate(classes):
        class_probabilities[
            str(class_name)
        ] = round(
            float(probabilities[i] * 100),
            2
        )

    # ========================================================
    # CONFIDENCE LEVEL
    # ========================================================

    if confidence >= 70:

        confidence_level = "High Confidence"

    elif confidence >= 50:

        confidence_level = "Low Confidence"

    else:

        confidence_level = "Not Reliably Identified"

    return {
        "scanner": predicted_scanner,

        "confidence": round(
            confidence,
            2
        ),

        "confidence_level": confidence_level,

        "probabilities": class_probabilities
    }


# ============================================================
# TEST PROGRAM
# ============================================================

if __name__ == "__main__":

    print(
        "\n========================================"
    )

    print(
        " Forensic Scanner Identification"
    )

    print(
        "========================================"
    )

    print(
        f"Device: {DEVICE}"
    )

    image_path = input(
        "\nEnter image path: "
    ).strip().strip('"')

    if not os.path.exists(
        image_path
    ):

        print(
            "\nImage file not found."
        )

    else:

        try:

            result = predict_scanner(
                image_path
            )

            print(
                "\nPredicted Scanner:"
            )

            print(
                result["scanner"]
            )

            print(
                f"\nConfidence: "
                f"{result['confidence']:.2f}%"
            )

            print(
                "\nAll Scanner Probabilities:"
            )

            for scanner, probability in (
                result["probabilities"].items()
            ):

                print(
                    f"{scanner}: "
                    f"{probability:.2f}%"
                )

        except Exception as e:

            print(
                "\nPrediction Error:"
            )

            print(
                str(e)
            )