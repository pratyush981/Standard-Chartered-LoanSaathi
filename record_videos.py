import cv2
import os
import time
import numpy as np

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Create videos directory if it doesn't exist
videos_dir = os.path.join('static', 'videos')
ensure_dir(videos_dir)

# Define the stages for which we need to record videos
stages = [
    "introduction",
    "personal_details",
    "loan_purpose",
    "loan_amount",
    "employment",
    "documents",
    "result_approved",
    "result_rejected",
    "result_more_info"
]

# Script prompts for each stage
prompts = {
    "introduction": "Hello! I'm your Loan Saathi. I'll guide you through the loan application process. How may I help you today?",
    "personal_details": "Please tell me your full name, age, and contact details.",
    "loan_purpose": "What type of loan are you looking for and what's the purpose?",
    "loan_amount": "How much loan amount are you looking for and what repayment period would you prefer?",
    "employment": "Please share your employment details and monthly income.",
    "documents": "Now I'll need to verify your identity and income. Please upload your ID proof and income documents.",
    "result_approved": "Congratulations! Your loan is pre-approved. Our representative will contact you shortly.",
    "result_rejected": "I'm sorry, but your loan application has been rejected. This could be due to insufficient income or credit history.",
    "result_more_info": "We need more information to process your application. Please provide additional details about your financial situation."
}

def record_video(stage_name, prompt):
    print(f"\n=== Recording video for: {stage_name} ===")
    print(f"Script: {prompt}")
    print("\nInstructions:")
    print("1. Position yourself in front of the camera")
    print("2. Press 'r' to start recording")
    print("3. Read the script naturally, as if you're a bank manager")
    print("4. Press 'q' to stop recording")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = 30
    
    # Wait for 'r' key to start recording
    recording = False
    output_file = os.path.join(videos_dir, f"{stage_name}.mp4")
    out = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image")
            break
        
        # Display recording status
        if recording:
            cv2.putText(frame, "RECORDING", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            # Add script as teleprompter
            lines = [prompt[i:i+40] for i in range(0, len(prompt), 40)]
            y_pos = height - 120
            for line in lines:
                cv2.putText(frame, line, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                y_pos += 30
        else:
            cv2.putText(frame, "Press 'r' to start recording", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imshow('Record Loan Saathi Video', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('r') and not recording:
            recording = True
            out = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
            print("Recording started...")
        elif key == ord('q'):
            if recording:
                recording = False
                out.release()
                print(f"Video saved to {output_file}")
            break
        
        if recording:
            out.write(frame)
    
    cap.release()
    if out is not None:
        out.release()
    cv2.destroyAllWindows()

def main():
    print("=== Loan Saathi Video Recording Tool ===")
    print("This tool will help you record videos for each stage of the conversation.")
    
    while True:
        print("\nAvailable stages:")
        for i, stage in enumerate(stages):
            print(f"{i+1}. {stage}")
        print("0. Exit")
        
        choice = input("\nEnter the number of the stage to record (0 to exit): ")
        if choice == '0':
            break
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(stages):
                stage_name = stages[index]
                record_video(stage_name, prompts[stage_name])
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    print("Thank you for recording the Loan Saathi videos!")

if __name__ == "__main__":
    main()
