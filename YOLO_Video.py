from ultralytics import YOLO
import cv2
import math
import pygame
import os
import cloudinary
from cloudinary import uploader
from datetime import datetime


def video_detection(path_x):
    try:
        # Cloudinary configuration vishw
        # cloudinary.config(
        #     cloud_name="dfceagnv7",
        #     api_key="975278638957374",
        #     api_secret="ScKo_cq8npUKTyDLkSY-vADcDtw"
        # )

        cloudinary.config(
            cloud_name='dq1rqwebs',
            api_key='632195136365794',
            api_secret='gNNhkZy89kyHhzPOcjLAzaKxXNc'
        )
        # Create a path for storing recorded frames:
        save_path = "saved_videos"
        os.makedirs(save_path, exist_ok=True)
        video_capture = path_x
        count = 0;
        # Create a VideoCapture object
        cap = cv2.VideoCapture(video_capture)
        if not cap.isOpened():
            raise ValueError("Error opening video capture")

        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))
        buffer_size = 2000
        num_frames_to_record = 1000

        # Initialize variables for frame storage, recording, and buffer:
        frames = []
        is_recording = False
        start_frame = 0
        frames_since_last_save = 0

        model = YOLO("./best.pt")
        classNames = ["chain snatching", "kidnapping", "Accident", "fighting"]

        current_time = datetime.now().strftime("%H-%M-%S")
        location = "hyderabad"
        current_date = datetime.now().date()
        pygame.mixer.init()
        sound = pygame.mixer.Sound("sound1.wav")

        while True:
            success, img = cap.read()
            if not success:
                print("End of video reached")
                # video_name = f"{class_name}_{start_frame}_{cap.get(cv2.CAP_PROP_POS_FRAMES)}.mp4"
                video_name = f"{class_name}_{current_date}_{current_time}_{location}.mp4"
                name =  f"{class_name}_{current_date}_{current_time}_{location}"
                output_path = os.path.join(save_path, video_name)
                count = count + 1;
                writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), 20,
                                         (frame_width, frame_height))
                for frame in frames:
                    writer.write(frame)
                writer.release()
                print(f"Saved video: {video_name}")
                print(output_path)

                # Upload to Cloudinary
                response = cloudinary.uploader.upload_large(output_path, folder="project", resource_type = "video" ,  public_id=video_name)
                print(f"Uploaded to Cloudinary: {response['url']}")
                break

            record_img = img.copy()
            results = model(img, stream=True)

            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                    conf = math.ceil((box.conf[0] * 100)) / 100
                    cls = int(box.cls[0])
                    class_name = classNames[cls]

                    if conf > 0.5:
                        if class_name == 'chain snatching':
                            color = (0, 204, 255)
                        elif class_name == 'kidnapping':
                            color = (222, 82, 175)
                        elif class_name == "Accident":
                            color = (0, 149, 255)
                        elif class_name == "fighting":
                            color = (85, 45, 255)
                        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
                        label = f"{class_name} {conf:.2f}"
                        cv2.putText(img, label, (x1, y1 - 2), 0, 1, [255, 255, 255], thickness=1, lineType=cv2.LINE_AA)
                        sound.play()
                        # while pygame.mixer.music.get_busy():
                        #  pygame.time.Clock().tick(1)

                        # If a class is detected and recording is not in progress, start recording:
                        if not is_recording and count ==0:
                            print(f"Detected {class_name} with confidence {conf}. Starting recording...")
                            is_recording = True
                            start_frame = cap.get(cv2.CAP_PROP_POS_FRAMES) - buffer_size
                            start_frame = max(0, start_frame)
                            frames_since_last_save = 0
                        if not is_recording and count >0:
                            print(f"Detected {class_name} with confidence {conf}. Starting recording...")
                            is_recording = True
                            start_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
                            start_frame = max(0, start_frame)
                            frames_since_last_save = 0

                    # If detection stops or confidence drops, end recording:
                    if  cap.get(cv2.CAP_PROP_POS_FRAMES) - start_frame > num_frames_to_record and is_recording:
                        is_recording = False

                        video_name = f"{class_name}_{current_date}_{current_time}_{location}.mp4"
                        output_path = os.path.join(save_path, video_name)
                        name = f"{class_name}_{current_date}_{current_time}_{location}"
                        count=count+1;
                        writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), 20,
                                                 (frame_width, frame_height))
                        for frame in frames:
                            writer.write(frame)
                        writer.release()
                        print(f"Saved video: {video_name}")
                        print(output_path)

                        # Upload to Cloudinary
                        response = cloudinary.uploader.upload_large(output_path, folder='project',resource_type = "video", public_id=video_name)
                        print(f"Uploaded to Cloudinary: {response['url']}")

                        frames = []
                        start_frame = 0

            # If recording, add frame to buffer and keep the last 50:
            if is_recording:
                frames.append(record_img)
                frames = frames[-buffer_size:]
                if len(frames) > buffer_size:
                    frames.pop(0)

                frames_since_last_save += 1

                # Check if it's time to save the video
                if frames_since_last_save >= num_frames_to_record:
                    is_recording = False
                    frames_since_last_save = 0

            yield img

        cv2.destroyAllWindows()

    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Release resources:
        if cap.isOpened():
            cap.release()

        cv2.destroyAllWindows()
