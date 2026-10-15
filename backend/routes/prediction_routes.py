# from flask import Blueprint, request, jsonify
# # from services.prediction_service import predict_leaf_disease
# # from services.fusion_service import fuse_predictions
# from services.prediction_service import predict_leaf_disease
# from services.stem_prediction_service import predict_stem_disease
# from services.fusion_service import fuse_predictions
# from services.fruit_prediction_service import predict_fruit_disease
# prediction_bp = Blueprint('prediction', __name__)

# @prediction_bp.route('/predict/leaf', methods=['POST'])
# def predict_leaf():
#     if 'image' not in request.files and 'file' not in request.files:
#         return jsonify({'error': 'No image file provided in request'}), 400
        
#     file = request.files.get('image') or request.files.get('file')
#     if file.filename == '':
#         return jsonify({'error': 'Empty filename selected'}), 400
        
#     try:
#         result = predict_leaf_disease(file)
#         return jsonify(result), 200
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @prediction_bp.route('/predict/fruit', methods=['POST'])
# def predict_fruit():
#     if 'image' not in request.files and 'file' not in request.files:
#         return jsonify({'error': 'No image file provided in request'}), 400

#     file = request.files.get('image') or request.files.get('file')

#     if file.filename == '':
#         return jsonify({'error': 'Empty filename selected'}), 400

#     try:
#         result = predict_fruit_disease(file)
#         return jsonify(result), 200

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# # @prediction_bp.route('/predict/stem', methods=['POST'])
# # def predict_stem():
# #     return jsonify({
# #         'status': 'integration_pending',
# #         'message': 'Stem detection model integration pending. YOLOv8 stem detection model architecture is prepared for future integration.',
# #         'affected_part': 'Stem',
# #         'model': 'YOLOv8-Ready'
# #     }), 200

# @prediction_bp.route('/predict/stem', methods=['POST'])
# def predict_stem():
#     if 'image' not in request.files and 'file' not in request.files:
#         return jsonify({'error': 'No stem image file provided in request'}), 400

#     file = request.files.get('image') or request.files.get('file')

#     if file.filename == '':
#         return jsonify({'error': 'Empty filename selected'}), 400

#     try:
#         result = predict_stem_disease(file)
#         return jsonify(result), 200

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @prediction_bp.route('/fusion', methods=['POST'])
# def perform_fusion():
#     data = request.get_json() or {}
#     leaf_pred = data.get('leaf')
#     fruit_pred = data.get('fruit')
#     stem_pred = data.get('stem')
    
#     fusion_result = fuse_predictions(leaf_pred, fruit_pred, stem_pred)
#     return jsonify(fusion_result), 200



from flask import Blueprint, request, jsonify

from services.prediction_service import predict_leaf_disease
from services.stem_prediction_service import predict_stem_disease
from services.fruit_prediction_service import predict_fruit_disease
from services.fusion_service import fuse_predictions

# Create the Flask Blueprint
prediction_bp = Blueprint("prediction", __name__)


def get_uploaded_file(error_message):
    """Retrieve an uploaded image from either supported form field."""
    if "image" not in request.files and "file" not in request.files:
        return None, (jsonify({"error": error_message}), 400)

    uploaded_file = request.files.get("image") or request.files.get("file")

    if not uploaded_file or not uploaded_file.filename:
        return None, (jsonify({"error": "No image selected"}), 400)

    return uploaded_file, None


@prediction_bp.route("/predict/leaf", methods=["POST"])
def predict_leaf():
    uploaded_file, error = get_uploaded_file(
        "No leaf image file provided"
    )
    if error:
        return error

    try:
        result = predict_leaf_disease(uploaded_file)
        return jsonify(result), 200
    except Exception as exc:
        print(f"Leaf prediction error: {exc}")
        return jsonify({
            "error": "Leaf prediction failed",
            "details": str(exc)
        }), 500


@prediction_bp.route("/predict/fruit", methods=["POST"])
def predict_fruit():
    uploaded_file, error = get_uploaded_file(
        "No fruit image file provided"
    )
    if error:
        return error

    try:
        result = predict_fruit_disease(uploaded_file)
        return jsonify(result), 200
    except Exception as exc:
        print(f"Fruit prediction error: {exc}")
        return jsonify({
            "error": "Fruit prediction failed",
            "details": str(exc)
        }), 500


@prediction_bp.route("/predict/stem", methods=["POST"])
def predict_stem():
    uploaded_file, error = get_uploaded_file(
        "No stem image file provided"
    )
    if error:
        return error

    try:
        result = predict_stem_disease(uploaded_file)
        return jsonify(result), 200
    except Exception as exc:
        print(f"Stem prediction error: {exc}")
        return jsonify({
            "error": "Stem prediction failed",
            "details": str(exc)
        }), 500


@prediction_bp.route("/fusion", methods=["POST"])
def perform_fusion():
    data = request.get_json(silent=True) or {}

    leaf_pred = data.get("leaf")
    fruit_pred = data.get("fruit")
    stem_pred = data.get("stem")

    if not any([leaf_pred, fruit_pred, stem_pred]):
        return jsonify({
            "success": False,
            "error": "Provide at least one leaf, fruit, or stem prediction"
        }), 400

    try:
        fusion_result = fuse_predictions(
            leaf_pred=leaf_pred,
            fruit_pred=fruit_pred,
            stem_pred=stem_pred
        )

        status_code = (
            200 if fusion_result.get("success", True) else 400
        )
        return jsonify(fusion_result), status_code

    except Exception as exc:
        print(f"Fusion error: {exc}")
        return jsonify({
            "success": False,
            "error": "Prediction fusion failed",
            "details": str(exc)
        }), 500
