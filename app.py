from flask import Flask, render_template, request, jsonify, session, url_for, redirect
import os
import cv2
import numpy as np
import base64
import json
import time
from datetime import datetime
from werkzeug.utils import secure_filename
from models.document_processor import DocumentProcessor
from models.face_recognition import FaceVerification

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Create directories for static files if they don't exist
for dir_path in ['static/videos', 'static/images', 'static/js', 'static/css']:
    os.makedirs(dir_path, exist_ok=True)

# Initialize processors
document_processor = DocumentProcessor()
face_verification = FaceVerification()

# Loan eligibility rules
def evaluate_loan_eligibility(user_data):
    """
    Evaluate loan eligibility based on user data
    Returns: status (approved, rejected, more_info), reason
    """
    # Extract relevant data
    income = user_data.get('income', 0)
    employment_type = user_data.get('employment_type', '')
    loan_amount = user_data.get('loan_amount', 0)
    credit_score = user_data.get('credit_score', 0)
    
    # Basic eligibility checks
    if not income or not employment_type:
        return "more_info", "Income or employment information missing"
    
    if income < 15000:
        return "rejected", "Income below minimum requirement of ₹15,000"
    
    # Loan amount should not exceed 10 times annual income
    if loan_amount > (income * 10):
        return "rejected", f"Loan amount exceeds maximum eligibility (10x annual income)"
    
    # Credit score check
    if credit_score < 650:
        return "rejected", "Credit score below minimum requirement"
    
    # Employment type check
    if employment_type.lower() not in ['salaried', 'self-employed', 'business']:
        return "more_info", "Employment type needs clarification"
    
    # If all checks pass
    return "approved", "Congratulations! Your loan is pre-approved."

# Function to check if required video files exist
def check_video_files():
    video_files = [
        'introduction.mp4',
        'personal_details.mp4',
        'loan_purpose.mp4',
        'loan_amount.mp4',
        'employment.mp4',
        'documents.mp4',
        'result_approved.mp4',
        'result_rejected.mp4',
        'result_more_info.mp4'
    ]
    
    videos_dir = os.path.join('static', 'videos')
    os.makedirs(videos_dir, exist_ok=True)
    
    # Create a README file if it doesn't exist
    readme_path = os.path.join(videos_dir, 'README.txt')
    if not os.path.exists(readme_path):
        with open(readme_path, 'w') as f:
            f.write("This directory contains video files for the Loan Saathi.\n")
            f.write("Please place your custom videos in this directory with the following names:\n")
            for video in video_files:
                f.write(f"- {video}\n")
    
    # Check for each required video file
    missing_videos = []
    invalid_videos = []
    for video_file in video_files:
        video_path = os.path.join(videos_dir, video_file)
        if not os.path.exists(video_path):
            missing_videos.append(video_file)
        elif os.path.getsize(video_path) < 10000:  # Check if file is too small (less than 10KB)
            invalid_videos.append(video_file)
    
    # Log missing or invalid videos but don't automatically generate them
    if missing_videos or invalid_videos:
        app.logger.info(f"Missing video files: {missing_videos}. Invalid video files: {invalid_videos}.")
        app.logger.info("Please place your custom videos in the static/videos directory.")

# Function to get a video URL with fallback
def get_video_url(video_name):
    video_path = os.path.join('static', 'videos', f"{video_name}.mp4")
    if os.path.exists(video_path) and os.path.getsize(video_path) > 10000:
        return url_for('static', filename=f'videos/{video_name}.mp4')
    else:
        # Try to find any valid video to use as fallback
        videos_dir = os.path.join('static', 'videos')
        for file in os.listdir(videos_dir):
            if file.endswith('.mp4') and os.path.getsize(os.path.join(videos_dir, file)) > 10000:
                app.logger.warning(f"Using {file} as fallback for missing {video_name}.mp4")
                return url_for('static', filename=f'videos/{file}')
        
        # If no valid videos found, return an empty string (will trigger error handling in frontend)
        app.logger.error(f"No valid videos found to use as fallback for {video_name}.mp4")
        return ""

# Routes
@app.route('/')
def index():
    # Reset session data when starting fresh
    session.clear()
    return render_template('index.html')

@app.route('/start-conversation')
def start_conversation():
    # Initialize the user journey
    session['stage'] = 'introduction'
    session['user_data'] = {}
    
    # Check if video files exist, if not create placeholders
    check_video_files()
    
    return render_template('conversation.html')

@app.route('/api/next-question', methods=['POST'])
def next_question():
    current_stage = session.get('stage', 'introduction')
    user_data = session.get('user_data', {})
    
    # Update user data with the latest response
    if request.json and 'response' in request.json:
        user_data[current_stage] = request.json['response']
        session['user_data'] = user_data
    
    # Determine the next stage based on the current stage
    if current_stage == 'introduction':
        next_stage = 'personal_details'
        video_url = get_video_url('personal_details')
        question = "Please tell me your full name, age, and contact details."
    
    elif current_stage == 'personal_details':
        next_stage = 'loan_purpose'
        video_url = get_video_url('loan_purpose')
        question = "What type of loan are you looking for and what's the purpose?"
    
    elif current_stage == 'loan_purpose':
        next_stage = 'loan_amount'
        video_url = get_video_url('loan_amount')
        question = "How much loan amount are you looking for and what repayment period would you prefer?"
    
    elif current_stage == 'loan_amount':
        next_stage = 'employment_details'
        video_url = get_video_url('employment')
        question = "Please share your employment details and monthly income."
    
    elif current_stage == 'employment_details':
        next_stage = 'document_upload'
        video_url = get_video_url('documents')
        question = "Now I'll need to verify your identity and income. Please upload your ID proof and income documents."
    
    elif current_stage == 'document_upload':
        # Process documents and determine eligibility
        next_stage = 'eligibility_check'
        video_url = get_video_url('introduction')  # Placeholder
        question = "Thank you for the documents. Let me check your loan eligibility."
    
    elif current_stage == 'eligibility_check':
        # Final stage - show results
        status, reason = evaluate_loan_eligibility(user_data)
        session['loan_status'] = status
        session['loan_reason'] = reason
        next_stage = 'result'
        
        if status == 'approved':
            video_url = get_video_url('result_approved')
        elif status == 'rejected':
            video_url = get_video_url('result_rejected')
        else:
            video_url = get_video_url('result_more_info')
        
        question = reason
    
    else:
        # Default case or end of conversation
        next_stage = 'end'
        video_url = get_video_url('introduction')  # Fallback to introduction
        question = "Thank you for using our Loan Saathi. Is there anything else I can help you with?"
    
    # Update the session with the new stage
    session['stage'] = next_stage
    
    return jsonify({
        'stage': next_stage,
        'video_url': video_url,
        'question': question
    })

@app.route('/api/capture-video', methods=['POST'])
def capture_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Save the video
    filename = secure_filename(f"{int(time.time())}.webm")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    video_file.save(filepath)
    
    # If this is not the first video, perform face verification
    if 'face_reference' in session:
        verification_result = face_verification.verify(
            session['face_reference'],
            filepath
        )
        if not verification_result['match']:
            return jsonify({
                'error': 'Face verification failed. Please ensure the same person is applying.'
            }), 400
    else:
        # Extract face from the first video and save as reference
        reference_face = face_verification.extract_face(filepath)
        if reference_face is not None:
            session['face_reference'] = reference_face
    
    # Store the video path in session for this stage
    current_stage = session.get('stage', 'introduction')
    user_data = session.get('user_data', {})
    user_data[f"{current_stage}_video"] = filepath
    session['user_data'] = user_data
    
    return jsonify({'success': True, 'message': 'Video captured successfully'})

@app.route('/api/upload-document', methods=['POST'])
def upload_document():
    try:
        if 'document' not in request.files:
            return jsonify({'error': 'No document file provided'}), 400
        
        document_file = request.files['document']
        document_type = request.form.get('type', 'id_proof')
        
        if document_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # Ensure upload folder exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save the document
        filename = secure_filename(f"{document_type}_{int(time.time())}.jpg")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        document_file.save(filepath)
        
        # Process the document based on type
        try:
            extracted_data = document_processor.process_document(filepath, document_type)
        except Exception as e:
            # If document processing fails, still accept the upload but log the error
            app.logger.error(f"Document processing error: {str(e)}")
            extracted_data = {"error": f"Could not process document: {str(e)}"}
        
        # Update user data with extracted information
        user_data = session.get('user_data', {})
        user_data.update(extracted_data)
        session['user_data'] = user_data
        
        return jsonify({
            'success': True, 
            'message': 'Document processed successfully',
            'extracted_data': extracted_data
        })
    except Exception as e:
        app.logger.error(f"Document upload error: {str(e)}")
        return jsonify({'error': f'Document upload failed: {str(e)}'}), 500

@app.route('/result')
def result():
    # Show final result page
    loan_status = session.get('loan_status', 'more_info')
    loan_reason = session.get('loan_reason', 'We need more information to process your application.')
    user_data = session.get('user_data', {})
    
    return render_template('result.html', 
                          status=loan_status, 
                          reason=loan_reason,
                          user_data=user_data)

if __name__ == '__main__':
    app.run(debug=True)
