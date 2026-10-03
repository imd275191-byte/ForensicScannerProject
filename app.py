from flask import Flask, render_template, request, jsonify
from database.database import get_connection, save_analysis
import os
import time

# Import working ML prediction function
from predict import predict_scanner


app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/test-db")
def test_db():
    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT DB_NAME()")
        database_name = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        return {
            "status": "success",
            "message": "Flask connected to SQL Server successfully!",
            "database": database_name
        }

    except Exception as error:
        return {
            "status": "error",
            "message": str(error)
        }, 500


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/api/analyze", methods=["POST"])
def analyze_image():

    start_time = time.time()

    # Check image upload
    if "image" not in request.files:
        return jsonify({
            "status": "error",
            "message": "No image uploaded."
        }), 400

    image = request.files["image"]

    # Check selected file
    if image.filename == "":
        return jsonify({
            "status": "error",
            "message": "No image selected."
        }), 400

    # Check file type
    if not allowed_file(image.filename):
        return jsonify({
            "status": "error",
            "message": "Only JPG, JPEG and PNG images are allowed."
        }), 400

    filename = image.filename

    file_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    # Save uploaded image
    image.save(file_path)

    try:
        # ==========================================
        # REAL ML PREDICTION
        # ==========================================

        prediction = predict_scanner(file_path)

        predicted_scanner = prediction["scanner"]
        confidence = prediction["confidence"]

        # ==========================================
        # PROCESSING TIME
        # ==========================================

        processing_time = round(
            time.time() - start_time,
            2
        )

        status = "Analysis Complete"

        # ==========================================
        # SAVE RESULT TO SQL SERVER
        # ==========================================

        save_analysis(
            filename,
            predicted_scanner,
            confidence,
            processing_time,
            status
        )

        # ==========================================
        # RETURN RESULT TO FRONTEND
        # ==========================================

        return jsonify({
            "status": "success",
            "message": "Image analyzed and saved successfully.",
            "image_name": filename,
            "predicted_scanner": predicted_scanner,
            "confidence": confidence,
            "confidence_level": prediction.get("confidence_level", ""),
            "processing_time": processing_time,
            "analysis_status": status
        })

    except Exception as error:

        print("Analysis Error:", error)

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


# ==========================================================
# ANALYSIS HISTORY API
# ==========================================================

@app.route("/api/history", methods=["GET"])
def analysis_history():

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT TOP 50
                AnalysisID,
                ImageName,
                PredictedScanner,
                Confidence,
                ProcessingTime,
                Status,
                CreatedAt
            FROM dbo.AnalysisHistory
            ORDER BY AnalysisID DESC
        """)

        rows = cursor.fetchall()

        history = []

        for row in rows:
            history.append({
                "analysis_id": row[0],
                "image_name": row[1],
                "predicted_scanner": row[2],
                "confidence": row[3],
                "processing_time": row[4],
                "status": row[5],
                "created_at": str(row[6])
            })

        cursor.close()
        connection.close()

        return jsonify({
            "status": "success",
            "history": history
        })

    except Exception as error:

        print("History Error:", error)

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


# ==========================================================
# START FLASK SERVER
# ==========================================================

if __name__ == "__main__":
    app.run(debug=True)