import pyodbc


SERVER = r"DESKTOP-CIRBMT0\MRSQL2025"
DATABASE = "ForensicScannerDB"
DRIVER = "ODBC Driver 18 for SQL Server"


def get_connection():
    connection_string = (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(connection_string)


def get_analysis_history():
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
        FROM AnalysisHistory
        ORDER BY AnalysisID DESC
    """)

    records = cursor.fetchall()

    cursor.close()
    connection.close()

    return records


def save_analysis(
    image_name,
    predicted_scanner,
    confidence,
    processing_time,
    status
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO AnalysisHistory
        (
            ImageName,
            PredictedScanner,
            Confidence,
            ProcessingTime,
            Status
        )
        VALUES (?, ?, ?, ?, ?)
    """,
        image_name,
        predicted_scanner,
        confidence,
        processing_time,
        status
    )

    connection.commit()

    cursor.close()
    connection.close()


if __name__ == "__main__":
    try:
        connection = get_connection()

        print("SQL Server connected successfully!")
        print("Database:", DATABASE)

        connection.close()

        save_analysis(
            "python_test.jpg",
            "Scanner A",
            88.5,
            1.10,
            "Analysis Complete"
        )

        print("Test analysis saved successfully!")

        records = get_analysis_history()

        print("\nAnalysis History:")

        for record in records:
            print(record)

    except Exception as error:
        print("SQL Server operation failed!")
        print("Error:", error)