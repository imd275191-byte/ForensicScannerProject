from flask import Flask, request, jsonify
from flask_cors import CORS
from database.database import get_connection, save_analysis
from predict import predict_scanner

import os
import time


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

# Allow frontend running on port 5500 to access backend on port 5000
CORS(app)


# ============================================================
# CONFIGURATION
# ============================================================

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def allowed_file(filename):
    """Check whether uploaded file has an allowed extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# ============================================================
# HOME / BACKEND STATUS
# ============================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "success",
        "message": "Forensic Scanner Identification API is running",
        "backend": "Flask",
        "api": "http://127.0.0.1:5000"
    })


# ============================================================
# DATABASE TEST
# ============================================================

@app.route("/test-db", methods=["GET"])
def test_db():

    try:
        connection = get_connection()

        if connection:
            connection.close()

            return jsonify({
                "status": "success",
                "message": "Flask connected to SQL Server successfully!",
                "database": "ForensicScannerDB"
            })

        return jsonify({
            "status": "error",
            "message": "Database connection failed"
        }), 500

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ============================================================
# IMAGE ANALYSIS
# ============================================================

@app.route("/api/analyze", methods=["POST"])
def analyze_image():

    start_time = time.time()

    try:

        # ----------------------------------------------------
        # Check image
        # ----------------------------------------------------

        if "image" not in request.files:
            return jsonify({
                "status": "error",
                "message": "No image file received"
            }), 400

        image = request.files["image"]

        if image.filename == "":
            return jsonify({
                "status": "error",
                "message": "No image selected"
            }), 400

        if not allowed_file(image.filename):
            return jsonify({
                "status": "error",
                "message": "Only JPG, JPEG and PNG images are allowed"
            }), 400

        # ----------------------------------------------------
        # Save uploaded image
        # ----------------------------------------------------

        filename = os.path.basename(image.filename)

        file_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        image.save(file_path)

        # ----------------------------------------------------
        # ML Prediction
        # ----------------------------------------------------

        prediction = predict_scanner(file_path)

        predicted_scanner = prediction["scanner"]
        confidence = prediction["confidence"]

        processing_time = round(
            time.time() - start_time,
            2
        )

        status = "Analysis Complete"

        # ----------------------------------------------------
        # Save result to SQL Server
        # ----------------------------------------------------

        save_analysis(
            filename,
            predicted_scanner,
            confidence,
            processing_time,
            status
        )

        # ----------------------------------------------------
        # Send result to frontend
        # ----------------------------------------------------

        return jsonify({
            "status": "success",
            "message": "Image analyzed successfully",
            "image_name": filename,
            "predicted_scanner": predicted_scanner,
            "confidence": confidence,
            "processing_time": processing_time,
            "analysis_status": status,
            "probabilities": prediction.get(
                "probabilities",
                {}
            )
        })

    except Exception as e:

        processing_time = round(
            time.time() - start_time,
            2
        )

        print("ANALYSIS ERROR:", e)

        return jsonify({
            "status": "error",
            "message": str(e),
            "processing_time": processing_time
        }), 500


# ============================================================
# ANALYSIS HISTORY
# ============================================================

@app.route("/api/history", methods=["GET"])
def analysis_history():

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                AnalysisID,
                ImageName,
                PredictedScanner,
                Confidence,
                ProcessingTime,
                Status,
                CreatedAt
            FROM dbo.AnalysisHistory
            ORDER BY CreatedAt DESC
        """)

        rows = cursor.fetchall()

        history = []

        for row in rows:

            history.append({
                "analysis_id": row[0],
                "image_name": row[1],
                "predicted_scanner": row[2],
                "confidence": float(row[3]) if row[3] is not None else None,
                "processing_time": float(row[4]) if row[4] is not None else None,
                "status": row[5],
                "created_at": str(row[6]) if row[6] is not None else None
            })

        return jsonify({
            "status": "success",
            "history": history
        })

    except Exception as e:

        print("HISTORY ERROR:", e)

        return jsonify({
            "status": "error",
            "message": str(e),
            "history": []
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )