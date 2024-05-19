import cv2
import os

def extract_frames(video_path, output_folder,frame_count):
    # Open the video file for reading
    cap = cv2.VideoCapture(video_path)

    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Get the frames per second (fps) of the video
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # Get the width and height of the video frames
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Initialize a counter for frame numbering


    # Loop through each frame in the video
    while True:
        # Read the next frame
        ret, frame = cap.read()

        # Break the loop if the video has ended
        if not ret:
            break

        # Save the frame as an image file
        frame_filename = os.path.join(output_folder, f"frame_{frame_count[0]:04d}.jpg")
        cv2.imwrite(frame_filename, frame)

        # Increment the frame counter
        frame_count[0] += 1

    # Release the video capture object
    cap.release()

if __name__ == "__main__":
    # Specify the path to the "train" folder containing videos
    train_folder_path = r"video"

    # Specify the output folder for frames
    frames_folder_path = r"frames"

    # Get the list of video files in the "train" folder
    video_files = [f for f in os.listdir(train_folder_path) if f.endswith(".mp4")]
    frame_count = [0]
    # Process each video file
    for video_file in video_files:
        video_path = os.path.join(train_folder_path, video_file)
        output_folder = os.path.join(frames_folder_path, os.path.splitext(video_file)[0])
        extract_frames(video_path, output_folder,frame_count)

    print("Frames extraction completed.")

# ////////

from flask import Flask, render_template, Response, session, request
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField, PasswordField, BooleanField
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.validators import InputRequired, DataRequired
from werkzeug.utils import secure_filename
import os
import cv2
from flask import redirect, url_for

from YOLO_Video import video_detection

app = Flask(__name__)

app.config['SECRET_KEY'] = 'muhammadmoin'
app.config['UPLOAD_FOLDER'] = 'static/files'


class User:
    def __init__(self, username, password, is_admin):
        self.username = username
        self.password = password
        self.is_admin = is_admin


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        users = {
            "admin": generate_password_hash("password"),
            "user": generate_password_hash("user_password"),
        }

        try:
            if username in users and check_password_hash(users[username], password):
                if username == "admin":
                    session['login_type'] = "all_videos"
                else:
                    session['login_type'] = "accident_videos"
                return render_template('dashboard.html')
            else:
                return render_template('login.html', form=form, error="Invalid username or password")
        except Exception as e:
            return render_template('login.html', form=form, error="An error occurred: {}".format(str(e)))
    return render_template('login.html', form=form)


def filter_videos(videos):
    if session.get('login_type') == "accident_videos":
        videos = [video for video in videos if "Accident" in video]
    return videos


class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Run")


def generate_frames(path_x=''):
    try:
        yolo_output = video_detection(path_x)
        for detection_ in yolo_output:
            ref, buffer = cv2.imencode('.jpg', detection_)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except Exception as e:
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n')
        print("Error generating frames:", str(e))


def generate_frames_web(path_x):
    try:
        yolo_output = video_detection(path_x)
        for detection_ in yolo_output:
            ref, buffer = cv2.imencode('.jpg', detection_)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except Exception as e:
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n')
        print("Error generating frames for web:", str(e))


@app.route('/dashboard', methods=['GET'])
def dashboard():
    if not session.get('login_type'):
        return render_template('login.html', error="Please login first")

    folder_path = r"saved_videos"
    videos = [os.path.join(folder_path, video) for video in os.listdir(folder_path) if
              video.endswith('.mp4')]

    return render_template('dashboard.html', videos=videos)


@app.route('/webapp')
def webapp():
    return Response(generate_frames_web(path_x=0), mimetype='multipart/x-mixed-replace; boundary=frame')


class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Run")

#
# def generate_frames(path_x=''):
#     try:
#         yolo_output = video_detection(path_x)
#         for detection_ in yolo_output:
#             ref, buffer = cv2.imencode('.jpg', detection_)
#             frame = buffer.tobytes()
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#     except Exception as e:
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n')
#         print("Error generating frames:", str(e))
#

# def generate_frames_web(path_x):
#     try:
#         yolo_output = video_detection(path_x)
#         for detection_ in yolo_output:
#             ref, buffer = cv2.imencode('.jpg', detection_)
#             frame = buffer.tobytes()
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#     except Exception as e:
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n')
#         print("Error generating frames for web:", str(e))


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    session.clear()
    return redirect('indexproject.html')


@app.route("/webcam", methods=['GET', 'POST'])
def webcam():
    session.clear()
    return render_template('ui.html')


@app.route('/FrontPage', methods=['GET', 'POST'])
def front():
    form = UploadFileForm()
    if form.validate_on_submit():
        file = form.file.data
        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'],
                               secure_filename(file.filename)))
        session['video_path'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'],
                                             secure_filename(file.filename))
    return render_template('videoprojectnew.html', form=form)


@app.route('/video')
def video():
    return Response(generate_frames(path_x=session.get('video_path', None)), mimetype='multipart/x-mixed-replace; boundary=frame')


def gen_frames():
    cap = cv2.VideoCapture('rtsp://192.168.22.4:1935')
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    cap.release()


@app.route("/rtsp_feed")
def rtsp_feed():
    return Response(generate_frames_web('rtsp://192.168.137.206:1935/'), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run(debug=True)
