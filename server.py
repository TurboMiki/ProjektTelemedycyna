from tensorflow.keras.models import load_model
import numpy as np
import cv2
# import smtplib
import socket
import queue
import pickle
import datetime
import time
# import sys
from threading import Thread
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.text import MIMEText
# from email.mime.image import MIMEImage
import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
model_path = r'C:\Users\mikol\Documents\studia_mgr\sem_8\AI-AssistedLiving-master\stand_lie.h5'

# def send_alert():
#     email_host = 'smtp.gmail.com'
#     email_port = 587
#     email_login = 'alert.faint.bot@gmail.com'
#     # email_password = 'alertbotfaint'
#     email_password = 'dlic msqh wtsw ljcd'
#     msg = MIMEMultipart()
#     msg['From'] = email_login
#     msg['To'] = 'adwiesek@wp.pl'
#     msg['Subject'] = 'ALERT!!!!!'
#     messege = 'ALERT the patient has fainted!!!!!!'
#     msg.attach(MIMEText(messege, 'plain'))
#     with open(r'C:\Users\mikol\Documents\studia_mgr\sem_8\AI-AssistedLiving-master\ss.jpg', "rb") as attachment:
#         image_mime = MIMEImage(attachment.read())
#         image_mime.add_header('Content-Disposition',
#                               'attachment', filename="image.jpg")
#         msg.attach(image_mime)
#     server = smtplib.SMTP(email_host, email_port)
#     server.starttls()
#     server.login(email_login, email_password)
#     text = msg.as_string()
#     server.sendmail(email_login, 'adwiesek@wp.pl', text)
#     server.quit()

def recieve_image(client,img_queue):
    flag = False
    data = b""
    while True:
        packet = client.recv(4096)
        if not packet: break
        data += packet
        try:
            image = pickle.loads(data)
            break
        except:
            pass
    if image[1] == 'close': 
        flag = True
        return flag
    timestamp = datetime.datetime.now()
    img_queue.put(image[0])
    print(f'Recieved file type: {type(image[0])}')
    return flag

def resize_image(image, target_size=(640, 480)):
    normalized = image / 255.0
    arr = cv2.resize(normalized, target_size)
    return np.array(arr)

def sceleton_detector(image):
    with mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6) as pose:
        results = pose.process(image)
        detected = False
        try:
            left_ankle = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ANKLE]
            right_ankle = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ANKLE]
            left_hip = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP]
            right_hip = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP]
            left_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                      mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                      mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))
            detected = True
        except:
            detected = False
        return detected

def detect(preprocessed_image,model):
    result = model.predict(preprocessed_image.reshape(1, *preprocessed_image.shape))
    prediction = np.argmax(result)
    if prediction == 0:
        print("lezy")
        return True

    else:
        print("stoi")
        return False

def transmiter(client,img_queue):
    number = 0
    while True:
        model = load_model(model_path) 
        if number == 15:
            number = 0
        image = img_queue.get()
        try:
            if image == 'end':
                print('Closing transmiter thread')
                close = 'end'
                client.send(pickle.dumps(close))
                client.close()
                break
        except:
            pass
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        detected = sceleton_detector(image)
        result = False
        if detected:
            resized_img = resize_image(image)
            result = detect(resized_img, model)
            if result:
                cv2.imwrite(f'zdjecia/ss_{number}.jpg',image)
                number +=1
        print('Info sent!')
        info = pickle.dumps(result)
        client.send(info)

def reciever(client,img_queue):
    while True:
        flag = recieve_image(client,img_queue)
        if flag:
            break
    img_queue.put('end')

def main():
    print('Server up and running...')
    img_queue = queue.Queue()
    host = '0.0.0.0'
    port = 5000
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)
    client, address = server.accept()
    print(f'Estabilished connection with: {str(address)}')
    
    recieving_thread = Thread(target = reciever, args = (client, img_queue))
    transmiter_thread = Thread(target=transmiter,args = (client, img_queue))

    recieving_thread.start()
    transmiter_thread.start()
    recieving_thread.join()
    transmiter_thread.join()
    print('Closing server socket')
    server.close()

if __name__=="__main__":
    main()