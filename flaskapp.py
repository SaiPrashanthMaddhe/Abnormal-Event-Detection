from flask import Flask, render_template, Response, session, request
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField, PasswordField, BooleanField
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.validators import InputRequired, DataRequired
from werkzeug.utils import secure_filename
import os
import cv2
from flask import redirect, url_for
import cloudinary
import cloudinary.uploader
import cloudinary.api
from YOLO_Video import video_detection
from datetime import datetime



app = Flask(__name__)

app.config['SECRET_KEY'] = 'muhammadmoin'
app.config['UPLOAD_FOLDER'] = 'static/files'


# # Configure Cloudinary vamshi
cloudinary.config(
    cloud_name='dq1rqwebs',
    api_key='632195136365794',
    api_secret='gNNhkZy89kyHhzPOcjLAzaKxXNc'
)


# cloudinary.config(
#     cloud_name="dfceagnv7",
#     api_key="975278638957374",
#     api_secret="ScKo_cq8npUKTyDLkSY-vADcDtw"
# )
# User class (if using a database)
class User:
    def __init__(self, username, password, is_admin):
        self.username = username
        self.password = password
        self.is_admin = is_admin

# Login form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

# Define login function as route handler

@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Authenticate with stored usernames and passwords (if not using database)
        users = {
            "police": generate_password_hash("password"),
            "hospital": generate_password_hash("hospital_password"),
            "local": generate_password_hash("local_password"),
        }

        if username in users and check_password_hash(users[username], password):
            if username == "police":
                session['login_type'] = "all_videos"
            elif username == "hospital":
                session['login_type'] = "accident_videos"
            else:
                session['login_type'] = "kidnaping_videos"
            return redirect(url_for('dashboard'))  # Redirect to dashboard route
        else:
            return render_template('login.html', form=form, error="Invalid username or password")
    return render_template('login.html', form=form)

# Define video filtering function
# def filter_videos(videos):
#     # keywords = ["Accident", "Chain", "Kidnapping", "Fighting"]
#     # if session.get('login_type') == "user":
#     #     videos = [video for video in videos if any(video.split('/')[-1].startswith(keyword) for keyword in keywords)]
#     #
#     # return videos\
#     keywords = ["Accident"]
#     if session.get('login_type') == "accident_videos":
#         filtered_videos = []
#         for video in videos:
#             # Extract the date part from the video name
#             date_str = video.split('/')[-1].split('_')[1]  # Assuming the date is the second part of the filename
#             date_obj = datetime.strptime(date_str, "%Y-%m-%d")
#             formatted_date = date_obj.strftime("%Y-%m-%d")
#             # Check if the video starts with "Accident" and has the desired date format
#             if video.split('/')[-1].startswith("Accident"):
#                 filtered_videos.append(video)
#         return filtered_videos
#     else:
#         print(videos)
#         return videos

def filter_videos(videos):
    keywords = ["Accident"]
    if session.get('login_type') == "accident_videos":
        filtered_videos = []
        for video in videos:
            if video.split('/')[-1].startswith("Accident"):
                filtered_videos.append(video)
        return filtered_videos
    else:
        print(videos)
        return videos

# Use FlaskForm to get input video file from user
class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Run")

def generate_frames(path_x=''):
    yolo_output = video_detection(path_x)
    for detection_ in yolo_output:
        ref, buffer = cv2.imencode('.jpg', detection_)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def generate_frames_web(path_x):
    yolo_output = video_detection(path_x)
    for detection_ in yolo_output:
        ref, buffer = cv2.imencode('.jpg', detection_)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if not session.get('login_type'):
        return render_template('login.html', error="Please login first")

    # Get video list from Cloudinary
    folder_path = 'project'
    # videos = fetch_videos_from_cloudinary(folder_path)
    videos = fetch_videos_from_cloudinary(folder_path)
    print(videos)
    # Filter videos based on keywords
    videos = filter_videos(videos)
    print(videos)
    # Display the second video
    second_video = None
    if len(videos) > 1:
        second_video = videos[1]

    return render_template('dashboard.html', videos=videos, second_video=second_video)


def sort_videos_by_date(video_urls):
    # Custom sorting function to extract date from URL and sort
    def extract_date(url):
        # Extract the date part from the URL
        date_part = url.split('/')[-1].split('_')[1]
        # Convert the date string to a datetime object
        return datetime.strptime(date_part, "%Y-%m-%d")

    # Sort the video URLs based on the extracted date (from latest to oldest)
    sorted_urls = sorted(video_urls, key=extract_date, reverse=True)

    return sorted_urls

def convert_cloudinary_url(original_urls):
    # Split the original URL into parts
    list = []
    print(original_urls)
    for original_url in original_urls:
        parts = original_url.split('/')

        # Find the index of 'upload' in the URL parts
        upload_index = parts.index('upload')

        # Insert the transformation parameters just before 'upload'
        transformed_url = '/'.join(parts[:upload_index] + ['upload', 'f_auto:video,q_auto'] + parts[upload_index + 1:])
        list.append((transformed_url))

    return list;


# def fetch_videos_from_cloudinary(folder_path):
#     # List all videos from the specified folder in your Cloudinary account
#     response = cloudinary.api.resources(
#         type='upload',
#         resource_type='video',
#         prefix=folder_path
#     )
#
#     videos = []
#     for item in response['resources']:
#         videos.append(item['url'])
#
#     # vi  =sort_videos_by_date(videos)
#     return convert_cloudinary_url(videos)

def fetch_videos_from_cloudinary(folder_path):
    videos = []
    next_cursor = None  # Cursor for pagination

    # Loop until all pages are fetched
    while True:
        # Fetch resources from Cloudinary using pagination
        response = cloudinary.api.resources(
            type='upload',
            resource_type='video',
            prefix=folder_path,
            next_cursor=next_cursor,  # Use the cursor for pagination
            max_results=500  # Adjust this value as per your needs
        )

        # Append videos from the current page
        for item in response['resources']:
            videos.append(item['url'])

        # Check if there are more pages
        if 'next_cursor' in response:
            next_cursor = response['next_cursor']
        else:
            break  # Exit the loop if there are no more pages
    vi = sort_videos_by_date(videos)
    # Convert Cloudinary URLs
    return convert_cloudinary_url(vi)


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
    return Response(generate_frames_web('rtsp://192.168.137.131:1935/'), mimetype='multipart/x-mixed-replace; boundary=frame')




if __name__ == "__main__":
    app.run(debug=True)
