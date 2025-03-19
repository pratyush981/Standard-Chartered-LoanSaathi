import cv2
import os
import numpy as np
import time

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Create videos directory if it doesn't exist
videos_dir = os.path.join('static', 'videos')
ensure_dir(videos_dir)

# Define the stages for which we need placeholder videos
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

# Create a simple placeholder video for each stage
def create_placeholder_video(stage_name, duration=10):  # Increased duration for more reliable videos
    # Video properties
    width, height = 640, 480
    fps = 30
    
    # Create output video writer
    output_file = os.path.join(videos_dir, f"{stage_name}.mp4")
    
    # Use mp4v codec which is more widely supported
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
    
    # Create frames for the duration
    for i in range(int(fps * duration)):
        # Create a gradient background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                frame[y, x] = [
                    int(255 * (x / width)),
                    int(255 * (y / height)),
                    int(255 * ((x + y) / (width + height)))
                ]
        
        # Add text
        cv2.putText(frame, f"Loan Saathi", (width//2 - 150, height//2 - 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Stage: {stage_name}", (width//2 - 120, height//2), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"Frame: {i}/{int(fps * duration)}", (width//2 - 100, height//2 + 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Write the frame
        out.write(frame)
    
    # Release the video writer
    out.release()
    
    # Verify the file was created successfully
    if os.path.exists(output_file) and os.path.getsize(output_file) > 10000:
        print(f"Created placeholder video for {stage_name}: {output_file}")
    else:
        print(f"Error: Failed to create valid video for {stage_name}")

def main():
    print("Creating placeholder videos for Loan Saathi...")
    
    for stage in stages:
        create_placeholder_video(stage)
        time.sleep(0.5)  # Small delay between videos
    
    print("All placeholder videos created successfully!")

if __name__ == "__main__":
    main()
