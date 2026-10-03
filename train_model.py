import os
import numpy as np
import cv2
import joblib

from PIL import Image
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


# =========================================================
# PROJECT SETTINGS
# =========================================================

DATASET_DIR = "dataset"
MODEL_DIR = "model"
MODEL_FILE = os.path.join(MODEL_DIR, "scanner_model.pkl")

IMAGE_SIZE = (128, 128)

CLASSES = [
    "scanner_A",
    "scanner_B",
    "scanner_C"
]


# =========================================================
# CREATE MODEL FOLDER
# =========================================================

os.makedirs(MODEL_DIR, exist_ok=True)


# =========================================================
# FEATURE EXTRACTION
# =========================================================

def extract_features(image_path):

    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    if image is None:
        raise ValueError("Unable to read image")

    # Resize image
    image = cv2.resize(
        image,
        IMAGE_SIZE
    )

    image_float = image.astype(np.float32)

    features = []

    # -----------------------------------------------------
    # 1. MEAN BRIGHTNESS
    # -----------------------------------------------------

    mean_brightness = np.mean(
        image_float
    )

    features.append(
        mean_brightness
    )


    # -----------------------------------------------------
    # 2. STANDARD DEVIATION / CONTRAST
    # -----------------------------------------------------

    contrast = np.std(
        image_float
    )

    features.append(
        contrast
    )


    # -----------------------------------------------------
    # 3. MINIMUM AND MAXIMUM INTENSITY
    # -----------------------------------------------------

    features.append(
        np.min(image_float)
    )

    features.append(
        np.max(image_float)
    )


    # -----------------------------------------------------
    # 4. IMAGE NOISE
    # -----------------------------------------------------

    blurred = cv2.GaussianBlur(
        image,
        (5, 5),
        0
    )

    noise = (
        image_float -
        blurred.astype(np.float32)
    )

    noise_mean = np.mean(
        np.abs(noise)
    )

    noise_std = np.std(
        noise
    )

    features.append(
        noise_mean
    )

    features.append(
        noise_std
    )


    # -----------------------------------------------------
    # 5. EDGE FEATURES
    # -----------------------------------------------------

    edges = cv2.Canny(
        image,
        50,
        150
    )

    edge_ratio = np.mean(
        edges > 0
    )

    features.append(
        edge_ratio
    )


    # -----------------------------------------------------
    # 6. GRADIENT FEATURES
    # -----------------------------------------------------

    gradient_x = cv2.Sobel(
        image_float,
        cv2.CV_32F,
        1,
        0,
        ksize=3
    )

    gradient_y = cv2.Sobel(
        image_float,
        cv2.CV_32F,
        0,
        1,
        ksize=3
    )

    gradient_magnitude = np.sqrt(
        gradient_x ** 2 +
        gradient_y ** 2
    )

    features.append(
        np.mean(gradient_magnitude)
    )

    features.append(
        np.std(gradient_magnitude)
    )


    # -----------------------------------------------------
    # 7. TEXTURE FEATURES
    # -----------------------------------------------------

    texture_mean = np.mean(
        np.abs(
            cv2.Laplacian(
                image_float,
                cv2.CV_32F
            )
        )
    )

    features.append(
        texture_mean
    )


    # -----------------------------------------------------
    # 8. FREQUENCY FEATURES
    # -----------------------------------------------------

    fft = np.fft.fft2(
        image_float
    )

    fft_shift = np.fft.fftshift(
        fft
    )

    magnitude = np.abs(
        fft_shift
    )

    frequency_mean = np.mean(
        magnitude
    )

    frequency_std = np.std(
        magnitude
    )

    features.append(
        frequency_mean
    )

    features.append(
        frequency_std
    )


    # -----------------------------------------------------
    # FINAL FEATURE ARRAY
    # -----------------------------------------------------

    return np.array(
        features,
        dtype=np.float32
    )


# =========================================================
# LOAD DATASET
# =========================================================

def load_dataset():

    features = []
    labels = []

    print("\n========================================")
    print("Loading Scanner Dataset")
    print("========================================\n")


    for label, class_name in enumerate(CLASSES):

        folder_path = os.path.join(
            DATASET_DIR,
            class_name
        )


        if not os.path.exists(folder_path):

            print(
                f"Folder not found: {folder_path}"
            )

            continue


        print(
            f"Reading: {class_name}"
        )


        image_count = 0


        for file_name in os.listdir(folder_path):

            file_path = os.path.join(
                folder_path,
                file_name
            )


            # ------------------------------------------------
            # ALLOW COMMON IMAGE FORMATS
            # ------------------------------------------------

            valid_extensions = (
                ".jpg",
                ".jpeg",
                ".png",
                ".bmp",
                ".tif",
                ".tiff"
            )


            if not file_name.lower().endswith(
                valid_extensions
            ):

                continue


            try:

                feature_vector = extract_features(
                    file_path
                )


                features.append(
                    feature_vector
                )

                labels.append(
                    label
                )

                image_count += 1


            except Exception as error:

                print(
                    f"Skipped: {file_name}"
                )

                print(
                    f"Reason: {error}"
                )


        print(
            f"Images loaded: {image_count}\n"
        )


    return (
        np.array(features),
        np.array(labels)
    )


# =========================================================
# MAIN TRAINING FUNCTION
# =========================================================

def train_model():

    X, y = load_dataset()


    # =====================================================
    # CHECK IF DATASET EXISTS
    # =====================================================

    if len(X) == 0:

        print("\n========================================")
        print("NO DATASET FOUND")
        print("========================================")

        print(
            "\nPlease add real scanner images to:"
        )

        for class_name in CLASSES:

            print(
                f"dataset/{class_name}/"
            )

        print(
            "\nModel training cancelled."
        )

        return


    # =====================================================
    # SHOW DATASET INFORMATION
    # =====================================================

    print("\n========================================")
    print("DATASET INFORMATION")
    print("========================================")

    print(
        f"Total images: {len(X)}"
    )

    print(
        f"Total features: {X.shape[1]}"
    )


    # =====================================================
    # CHECK NUMBER OF CLASSES
    # =====================================================

    unique_classes = np.unique(
        y
    )


    if len(unique_classes) < 2:

        print(
            "\nAt least 2 scanner classes are required."
        )

        print(
            "Please add images for more scanners."
        )

        return


    # =====================================================
    # CHECK MINIMUM IMAGES PER CLASS
    # =====================================================

    class_counts = np.bincount(
        y
    )


    print(
        "\nImages per scanner:"
    )


    for index, count in enumerate(
        class_counts
    ):

        if index < len(CLASSES):

            print(
                f"{CLASSES[index]}: {count}"
            )


    # =====================================================
    # TRAIN / TEST SPLIT
    # =====================================================

    try:

        X_train, X_test, y_train, y_test = train_test_split(

            X,
            y,

            test_size=0.20,

            random_state=42,

            stratify=y

        )

    except ValueError as error:

        print(
            "\nDataset is too small for stratified training."
        )

        print(
            f"Reason: {error}"
        )

        print(
            "\nPlease add more images for each scanner."
        )

        return


    print(
        f"\nTraining images: {len(X_train)}"
    )

    print(
        f"Testing images: {len(X_test)}"
    )


    # =====================================================
    # CREATE RANDOM FOREST
    # =====================================================

    print(
        "\n========================================"
    )

    print(
        "Training Random Forest Model..."
    )

    print(
        "========================================"
    )


    model = RandomForestClassifier(

        n_estimators=200,

        max_depth=None,

        random_state=42,

        class_weight="balanced"

    )


    # =====================================================
    # TRAIN MODEL
    # =====================================================

    model.fit(
        X_train,
        y_train
    )


    # =====================================================
    # TEST MODEL
    # =====================================================

    predictions = model.predict(
        X_test
    )


    accuracy = accuracy_score(
        y_test,
        predictions
    )


    print(
        f"\nModel Accuracy: {accuracy * 100:.2f}%"
    )


    # =====================================================
    # CLASSIFICATION REPORT
    # =====================================================

    print(
        "\nClassification Report:"
    )


    print(
        classification_report(

            y_test,

            predictions,

            labels=range(len(CLASSES)),

            target_names=CLASSES,

            zero_division=0

        )
    )


    # =====================================================
    # SAVE MODEL
    # =====================================================

    model_data = {

        "model": model,

        "classes": CLASSES,

        "image_size": IMAGE_SIZE,

        "feature_version": "scanner_features_v1"

    }


    joblib.dump(
        model_data,
        MODEL_FILE
    )


    # =====================================================
    # SUCCESS MESSAGE
    # =====================================================

    print(
        "\n========================================"
    )

    print(
        "MODEL SAVED SUCCESSFULLY!"
    )

    print(
        "========================================"
    )

    print(
        f"Model location: {MODEL_FILE}"
    )


# =========================================================
# START PROGRAM
# =========================================================

if __name__ == "__main__":

    train_model()