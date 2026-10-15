# from flask import Blueprint, request, jsonify, send_file
# import io
# from services.report_service import generate_pdf_report

# report_bp = Blueprint('report', __name__)

# @report_bp.route('/report', methods=['POST'])
# def download_report():
#     data = request.get_json()
#     if not data:
#         return jsonify({'error': 'Report data is required'}), 400
        
#     try:
#         pdf_bytes = generate_pdf_report(data)
#         disease_title = str(data.get('final_diagnosis', data.get('disease', 'Analysis'))).replace(' ', '_')
#         filename = f"Tomato_Disease_Report_{disease_title}.pdf"
        
#         return send_file(
#             io.BytesIO(pdf_bytes),
#             mimetype='application/pdf',
#             as_attachment=True,
#             download_name=filename
#         )
#     except Exception as e:
#         return jsonify({'error': f'Failed to generate PDF report: {str(e)}'}), 500



import io
import re

from flask import Blueprint, request, jsonify, send_file
from services.report_service import generate_pdf_report

report_bp = Blueprint("report", __name__)


# def prepare_report_data(data):
#     """
#     Normalize modality information before generating the PDF.

#     The frontend should send explicit *_uploaded flags whenever possible.
#     Prediction objects may be supplied as leaf, fruit, stem or as
#     leaf_prediction, fruit_prediction, stem_prediction.
#     """
#     report_data = dict(data)

#     individual_predictions = report_data.get(
#         "individual_predictions", []
#     )

#     if not isinstance(individual_predictions, list):
#         individual_predictions = []

#     for part in ("leaf", "fruit", "stem"):
#         uploaded_key = f"{part}_uploaded"
#         status_key = f"{part}_status"
#         confidence_key = f"{part}_confidence"
#         prediction_key = f"{part}_prediction"

#         # Accept either "leaf" or "leaf_prediction" as the model result.
#         prediction = report_data.get(prediction_key)

#         if prediction is None:
#             possible_result = report_data.get(part)
#             if isinstance(possible_result, dict):
#                 prediction = possible_result

#         # Find this modality in the fusion service's prediction list.
#         if prediction is None:
#             for item in individual_predictions:
#                 if (
#                     isinstance(item, dict)
#                     and str(item.get("part", "")).lower() == part
#                 ):
#                     prediction = item
#                     break

#         # Copy values from a prediction response when available.
#         if isinstance(prediction, dict):
#             report_data[prediction_key] = prediction

#             if report_data.get(confidence_key) is None:
#                 confidence = prediction.get(
#                     "confidence",
#                     prediction.get("confidence_score")
#                 )
#                 if confidence is not None:
#                     report_data[confidence_key] = confidence

#         # Determine whether a prediction actually exists.
#         confidence = report_data.get(confidence_key)
#         has_prediction = (
#             isinstance(prediction, dict)
#             and any(
#                 prediction.get(key) is not None
#                 for key in (
#                     "disease",
#                     "predicted_class",
#                     "class_name",
#                     "prediction",
#                     "label",
#                 )
#             )
#         )

#         if confidence is not None or has_prediction:
#             report_data[uploaded_key] = (
#                 report_data.get(uploaded_key) is not False
#             )
#             report_data[status_key] = "analyzed"

#         elif report_data.get(uploaded_key) is True:
#             # Uploaded, but no successful prediction was supplied.
#             report_data[status_key] = "prediction_failed"
#             report_data[confidence_key] = None

#         elif report_data.get(uploaded_key) is False:
#             report_data[status_key] = "not_uploaded"
#             report_data[confidence_key] = None
#             report_data[prediction_key] = None

#         else:
#             # Do not assume a modality was analyzed when the request
#             # does not include upload or prediction information.
#             report_data[uploaded_key] = False
#             report_data[status_key] = "not_uploaded"
#             report_data[confidence_key] = None
#             report_data[prediction_key] = None

#     return report_data


def prepare_report_data(data):
    report_data = dict(data)

    individual_predictions = report_data.get(
        "individual_predictions", []
    )

    if not isinstance(individual_predictions, list):
        individual_predictions = []

    for part in ("leaf", "fruit", "stem"):
        uploaded_key = f"{part}_uploaded"
        status_key = f"{part}_status"
        confidence_key = f"{part}_confidence"
        prediction_key = f"{part}_prediction"

        # Explicit upload flags take priority over prediction data.
        uploaded = report_data.get(uploaded_key)

        if uploaded is False:
            report_data[status_key] = "not_uploaded"
            report_data[confidence_key] = None
            report_data[prediction_key] = None
            continue

        # Get a prediction for this modality.
        prediction = report_data.get(prediction_key)

        if prediction is None:
            possible_result = report_data.get(part)
            if isinstance(possible_result, dict):
                prediction = possible_result

        if prediction is None:
            for item in individual_predictions:
                if (
                    isinstance(item, dict)
                    and str(item.get("part", "")).strip().lower()
                    == part
                ):
                    prediction = item
                    break

        confidence = report_data.get(confidence_key)
        disease = None

        if isinstance(prediction, dict):
            disease = (
                prediction.get("disease")
                or prediction.get("predicted_class")
                or prediction.get("class_name")
                or prediction.get("label")
            )

            if confidence is None:
                confidence = prediction.get(
                    "confidence",
                    prediction.get("confidence_score")
                )

        elif isinstance(prediction, str):
            disease = prediction

        # Check confidence is numeric and within the expected range.
        try:
            valid_confidence = (
                confidence is not None
                and 0 <= float(confidence) <= 100
            )
        except (ValueError, TypeError):
            valid_confidence = False

        # Only an explicit upload flag or a valid prediction can
        # establish that a modality was analyzed.
        if uploaded is True:
            if valid_confidence and disease:
                report_data[status_key] = "analyzed"
                report_data[confidence_key] = confidence
                report_data[prediction_key] = prediction
            else:
                report_data[status_key] = "prediction_failed"
                report_data[confidence_key] = None

        elif valid_confidence and disease:
            report_data[uploaded_key] = True
            report_data[status_key] = "analyzed"
            report_data[confidence_key] = confidence
            report_data[prediction_key] = prediction

        else:
            report_data[uploaded_key] = False
            report_data[status_key] = "not_uploaded"
            report_data[confidence_key] = None
            report_data[prediction_key] = None

    return report_data

@report_bp.route("/report", methods=["POST"])
def download_report():
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify({
            "error": "Report data is required"
        }), 400

    try:
        report_data = prepare_report_data(data)
        pdf_bytes = generate_pdf_report(report_data)

        disease_title = report_data.get(
            "final_diagnosis",
            report_data.get(
                "final_disease",
                report_data.get("disease", "Analysis")
            )
        )

        disease_title = re.sub(
            r"[^A-Za-z0-9_-]+",
            "_",
            str(disease_title)
        ).strip("_") or "Analysis"

        filename = f"Tomato_Disease_Report_{disease_title}.pdf"

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )

    except Exception as exc:
        print(f"PDF report generation error: {exc}")
        return jsonify({
            "error": "Failed to generate PDF report",
            "details": str(exc)
        }), 500
