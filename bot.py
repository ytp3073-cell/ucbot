#!/usr/bin/env python3
import cv2
import numpy as np
from flask import Flask, request, jsonify
app = Flask(__name__)
def remove_clothes(image_bytes):
    """
    Remove clothing from an image using edge detection.
    
    Parameters:
        image_bytes: Binary content of the uploaded file
        
    Returns:
        Processed image bytes ready for response
    """
    # Convert binary data to numpy array and then OpenCV format
    img_array = np.frombuffer(image_bytes, np.uint8)
    if len(img_array) == 0 or not isinstance(img_array[0], int):
        return None
    
    try:
        # Load image using OpenCV
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        # Edge detection in grayscale format
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Invert binary image to create clothes mask
        _, mask = cv2.threshold(edges, 75, 255, cv2.THRESH_BINARY_INV)
        
        # Apply the mask to remove unwanted elements
        result = cv2.bitwise_and(image, image, mask=cv2.bitwise_not(mask))
        
        return result
    
    except Exception as e:
        print(f"Error in processing: {str(e)}")
        return None
@app.route('/process', methods=['POST'])
def process():
    """Lambda handler for API requests."""
    
    if 'file' not in request.files or request.content_length > 5 * 1024 * 1024:
        # Check file size limit (max: 5MB)
        return jsonify({'error': 'Invalid request'}), 400
    
    try:
        img = remove_clothes(request.files['file'].read())
        
        if not img:
            return jsonify({'error': 'Processing failed'}), 500
            
        # Convert back to bytes for response
        success, output_bytes = cv2.imencode('.png', img)
        if not success:
            return jsonify({'error': 'Output encoding failed'}), 500
            
        return output_bytes.tobytes(), 200
        
    except Exception as e:
        print(f"Request error: {str(e)}")
        return jsonify({'error': str(e)}), 500
def lambda_handler(event, context):
    """AWS Lambda handler."""
    
    # Flask request conversion for AWS Lambda
    from flask_lambda import FlaskLambda
    
    app = FlaskLambda(__name__)
    return app.handle_request(event, context)
if __name__ == '__main__':
    # For local testing using Flask development server
    app.run(debug=True)
