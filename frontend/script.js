// ===============================
// FORENSIC SCANNER PROJECT
// Frontend JavaScript
// ===============================


// ===============================
// GET HTML ELEMENTS
// ===============================

const imageInput = document.getElementById("imageInput");
const previewImage = document.getElementById("previewImage");
const fileName = document.getElementById("fileName");
const fileSize = document.getElementById("fileSize");
const analyzeBtn = document.getElementById("analyzeBtn");
const resultBox = document.getElementById("resultBox");
const uploadBox = document.getElementById("uploadBox");


// ===============================
// SCROLL TO ANALYSIS
// ===============================

function scrollToAnalysis() {

    const analysisSection =
        document.getElementById("analysis");

    if (analysisSection) {

        analysisSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }
}


// ===============================
// SCROLL TO RESULT
// ===============================

function scrollToResult() {

    if (!resultBox) {
        return;
    }

    setTimeout(function () {

        const resultPosition =
            resultBox.getBoundingClientRect().top +
            window.pageYOffset;

        const screenPosition =
            window.innerHeight * 0.20;

        const scrollPosition =
            resultPosition - screenPosition;

        window.scrollTo({
            top: Math.max(0, scrollPosition),
            left: 0,
            behavior: "smooth"
        });

    }, 300);
}


// ===============================
// CONFIDENCE DISPLAY
// ===============================

function updateConfidenceDisplay(
    confidenceValue,
    confidence
) {

    if (!confidenceValue) {
        return;
    }


    // Remove all old classes

    confidenceValue.classList.remove(
        "confidence-high",
        "confidence-low",
        "confidence-red"
    );


    // Remove old inline styles

    confidenceValue.style.background = "";
    confidenceValue.style.color = "";


    let confidenceLevel = "";
    let confidenceClass = "";


    // ===============================
    // HIGH CONFIDENCE
    // ===============================

    if (confidence >= 70) {

        confidenceLevel =
            "High Confidence";

        confidenceClass =
            "confidence-high";
    }


    // ===============================
    // LOW CONFIDENCE
    // ===============================

    else if (confidence >= 50) {

        confidenceLevel =
            "Low Confidence";

        confidenceClass =
            "confidence-low";
    }


    // ===============================
    // NOT RELIABLY IDENTIFIED
    // ===============================

    else {

        confidenceLevel =
            "Not Reliably Identified";

        confidenceClass =
            "confidence-red";
    }


    // ===============================
    // APPLY CONFIDENCE CLASS
    // ===============================

    confidenceValue.classList.add(
        confidenceClass
    );


    // ===============================
    // DISPLAY CONFIDENCE
    // ===============================

    confidenceValue.textContent =
        confidence.toFixed(2) +
        "% (" +
        confidenceLevel +
        ")";
}


// ===============================
// IMAGE SELECT
// ===============================

if (imageInput) {

    imageInput.addEventListener(
        "change",
        function () {

            const file =
                this.files[0];

            if (!file) {
                return;
            }


            // ===============================
            // ALLOWED IMAGE TYPES
            // ===============================

            const allowedTypes = [
                "image/jpeg",
                "image/jpg",
                "image/png"
            ];

            if (!allowedTypes.includes(file.type)) {

                alert(
                    "Please select JPG, JPEG or PNG image."
                );

                imageInput.value = "";

                return;
            }


            // ===============================
            // MAXIMUM FILE SIZE
            // ===============================

            const maxSize =
                10 * 1024 * 1024;

            if (file.size > maxSize) {

                alert(
                    "Image size must be less than 10 MB."
                );

                imageInput.value = "";

                return;
            }


            // ===============================
            // IMAGE PREVIEW
            // ===============================

            const reader =
                new FileReader();

            reader.onload =
                function (event) {

                    if (previewImage) {

                        previewImage.src =
                            event.target.result;

                        previewImage.style.display =
                            "block";
                    }
                };

            reader.readAsDataURL(file);


            // ===============================
            // FILE NAME
            // ===============================

            if (fileName) {

                fileName.textContent =
                    file.name;
            }


            // ===============================
            // FILE SIZE
            // ===============================

            const sizeMB =
                (file.size / (1024 * 1024))
                    .toFixed(2);

            if (fileSize) {

                fileSize.textContent =
                    sizeMB + " MB";
            }


            // ===============================
            // ENABLE ANALYZE BUTTON
            // ===============================

            if (analyzeBtn) {

                analyzeBtn.disabled =
                    false;

                analyzeBtn.textContent =
                    "Analyze Image";
            }


            // ===============================
            // HIDE OLD RESULT
            // ===============================

            if (resultBox) {

                resultBox.style.display =
                    "none";
            }


            // ===============================
            // RESET CONFIDENCE
            // ===============================

            const confidenceValue =
                document.getElementById(
                    "confidenceValue"
                );

            if (confidenceValue) {

                confidenceValue.classList.remove(
                    "confidence-high",
                    "confidence-low",
                    "confidence-red"
                );

                confidenceValue.textContent =
                    "--";
            }

        }
    );
}


// ===============================
// ANALYZE IMAGE
// ===============================

if (analyzeBtn) {

    analyzeBtn.addEventListener(
        "click",
        async function () {

            const file =
                imageInput.files[0];


            // ===============================
            // CHECK FILE
            // ===============================

            if (!file) {

                alert(
                    "Please select an image first."
                );

                return;
            }


            // ===============================
            // DISABLE BUTTON
            // ===============================

            analyzeBtn.disabled =
                true;

            analyzeBtn.textContent =
                "Analyzing...";


            // ===============================
            // SHOW RESULT BOX
            // ===============================

            if (resultBox) {

                resultBox.style.display =
                    "block";
            }


            // ===============================
            // GET RESULT ELEMENTS
            // ===============================

            const scannerResult =
                document.getElementById(
                    "scannerResult"
                );

            const confidenceValue =
                document.getElementById(
                    "confidenceValue"
                );

            const resultStatus =
                document.getElementById(
                    "resultStatus"
                );

            const processingTime =
                document.getElementById(
                    "processingTime"
                );


            // ===============================
            // INITIAL VALUES
            // ===============================

            if (scannerResult) {

                scannerResult.textContent =
                    "Processing...";
            }

            if (confidenceValue) {

                confidenceValue.textContent =
                    "--";

                confidenceValue.classList.remove(
                    "confidence-high",
                    "confidence-low",
                    "confidence-red"
                );
            }

            if (resultStatus) {

                resultStatus.textContent =
                    "Image Processing";
            }

            if (processingTime) {

                processingTime.textContent =
                    "--";
            }


            // ===============================
            // CREATE FORM DATA
            // ===============================

            const formData =
                new FormData();

            formData.append(
                "image",
                file
            );


            // ===============================
            // STATUS
            // ===============================

            if (resultStatus) {

                resultStatus.textContent =
                    "Running ML Analysis";
            }


            try {

                // ===============================
                // SEND IMAGE TO FLASK
                // ===============================

                const response =
                    await fetch(
                        "https://forensicscannerproject.onrender.com/api/analyze",
                        {
                            method: "POST",
                            body: formData
                        }
                    );


                // ===============================
                // GET API RESPONSE
                // ===============================

                const data =
                    await response.json();


                // ===============================
                // CHECK ERROR
                // ===============================

                if (
                    !response.ok ||
                    data.status !== "success"
                ) {

                    throw new Error(
                        data.message ||
                        "Image analysis failed."
                    );
                }


                // ===============================
                // DISPLAY SCANNER RESULT
                // ===============================

                if (scannerResult) {

                    scannerResult.textContent =
                        data.predicted_scanner;
                }


                // ===============================
                // DISPLAY CONFIDENCE
                // ===============================

                if (confidenceValue) {

                    const confidence =
                        Number(data.confidence);

                    updateConfidenceDisplay(
                        confidenceValue,
                        confidence
                    );
                }


                // ===============================
                // RESULT STATUS
                // ===============================

                if (resultStatus) {

                    resultStatus.textContent =
                        data.analysis_status;
                }


                // ===============================
                // PROCESSING TIME
                // ===============================

                if (processingTime) {

                    processingTime.textContent =
                        data.processing_time +
                        " seconds";
                }


                // ===============================
                // BUTTON AFTER SUCCESS
                // ===============================

                analyzeBtn.disabled =
                    false;

                analyzeBtn.textContent =
                    "Analyze Again";


                // ===============================
                // SCROLL TO RESULT
                // ===============================

                scrollToResult();


                // ===============================
                // REFRESH HISTORY
                // ===============================

                if (
                    typeof loadAnalysisHistory ===
                    "function"
                ) {

                    setTimeout(
                        function () {

                            loadAnalysisHistory();

                        },
                        500
                    );
                }

            }

            catch (error) {

                // ===============================
                // ERROR HANDLING
                // ===============================

                console.error(
                    "Analysis Error:",
                    error
                );


                if (scannerResult) {

                    scannerResult.textContent =
                        "Analysis Failed";
                }

                if (confidenceValue) {

                    confidenceValue.textContent =
                        "--";

                    confidenceValue.classList.remove(
                        "confidence-high",
                        "confidence-low",
                        "confidence-red"
                    );
                }

                if (resultStatus) {

                    resultStatus.textContent =
                        error.message;
                }

                if (processingTime) {

                    processingTime.textContent =
                        "--";
                }


                // ===============================
                // ENABLE BUTTON
                // ===============================

                analyzeBtn.disabled =
                    false;

                analyzeBtn.textContent =
                    "Try Again";


                // ===============================
                // SCROLL TO ERROR RESULT
                // ===============================

                scrollToResult();
            }

        }
    );
}


// ===============================
// DRAG AND DROP
// ===============================

if (uploadBox) {

    uploadBox.addEventListener(
        "dragover",
        function (event) {

            event.preventDefault();

            uploadBox.style.borderColor =
                "#607da8";
        }
    );


    uploadBox.addEventListener(
        "dragleave",
        function () {

            uploadBox.style.borderColor =
                "#ccd4e0";
        }
    );


    uploadBox.addEventListener(
        "drop",
        function (event) {

            event.preventDefault();

            uploadBox.style.borderColor =
                "#ccd4e0";


            const file =
                event.dataTransfer.files[0];


            if (!file) {
                return;
            }


            // Put dropped file into input

            imageInput.files =
                event.dataTransfer.files;


            // Trigger change event

            imageInput.dispatchEvent(
                new Event("change")
            );

        }
    );
}


// ==========================================================
// ANALYSIS HISTORY
// ==========================================================

async function loadAnalysisHistory() {

    const tableBody =
        document.getElementById(
            "historyTableBody"
        );

    if (!tableBody) {
        return;
    }


    tableBody.innerHTML = `
        <tr>
            <td colspan="7" class="history-loading">
                Loading history...
            </td>
        </tr>
    `;


    try {

        const response =
            await fetch(
                "https://forensicscannerproject.onrender.com/api/history"
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            data.status !== "success"
        ) {

            throw new Error(
                data.message ||
                "Unable to load history."
            );
        }


        if (
            !data.history ||
            data.history.length === 0
        ) {

            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="history-empty">
                        No analysis history found.
                    </td>
                </tr>
            `;

            return;
        }


        tableBody.innerHTML = "";


        data.history.forEach(
            function (item) {

                const row =
                    document.createElement(
                        "tr"
                    );


                row.innerHTML = `
                    <td>
                        ${item.analysis_id}
                    </td>

                    <td>
                        ${item.image_name}
                    </td>

                    <td>
                        <strong>
                            ${item.predicted_scanner}
                        </strong>
                    </td>

                    <td>
                        <span class="history-confidence ${getConfidenceClass(item.confidence)}">
                            <span class="confidence-dot"></span>
                            ${Number(item.confidence).toFixed(2)}%
                        </span>
                    </td>

                    <td>
                        ${item.processing_time} sec
                    </td>

                    <td>
                        <span class="history-status">
                            ${item.status}
                        </span>
                    </td>

                    <td>
                        ${formatHistoryDate(
                            item.created_at
                        )}
                    </td>
                `;


                tableBody.appendChild(
                    row
                );
            }
        );

    }

    catch (error) {

        console.error(
            "History Error:",
            error
        );


        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="history-error">
                    Unable to load analysis history.
                </td>
            </tr>
        `;
    }
}


// ==========================================================
// HISTORY CONFIDENCE CLASS
// ==========================================================

function getConfidenceClass(confidence) {

    const value =
        Number(confidence);


    if (value >= 70) {

        return "history-confidence-high";
    }


    if (value >= 50) {

        return "history-confidence-low";
    }


    return "history-confidence-red";
}


// ==========================================================
// FORMAT HISTORY DATE
// ==========================================================

function formatHistoryDate(
    dateString
) {

    if (!dateString) {
        return "--";
    }


    const date =
        new Date(dateString);


    if (
        isNaN(
            date.getTime()
        )
    ) {

        return dateString;
    }


    return date.toLocaleString();
}


// ==========================================================
// LOAD HISTORY WHEN PAGE OPENS
// ==========================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        loadAnalysisHistory();

    }
);