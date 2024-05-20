from threading import Thread
import sys
import queue
import socket
import pickle
import time
import cv2
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib

client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.connect(('127.0.0.1',5000))

def send_snapshot(vc,img_queue):
    '''
    Takes videocapture, creates snapshot, pickles snapshot 
    and sends it to server. Than is set to sleep for 1 second.
    '''
    _,image = vc.read()
    img_queue.put(image)
    table = [image,'sent']
    image_bytes = pickle.dumps(table)
    try:
        client.send(image_bytes)
    except:
        print('Couldn\'t send the image')
    time.sleep(1)

def send_alert(image):
    email_host = 'smtp.gmail.com'
    email_port = 587
    email_login = 'alert.faint.bot@gmail.com'
    # email_password = 'alertbotfaint'
    email_password = 'dlic msqh wtsw ljcd'
    msg = MIMEMultipart()
    msg['From'] = email_login
    msg['To'] = 'adwiesek@wp.pl'
    msg['Subject'] = 'ALERT!!!!!'
    messege = 'ALERT the patient has fainted!!!!!!'
    msg.attach(MIMEText(messege, 'plain'))
    with image as attachment:
        image_mime = MIMEImage(attachment.read())
        image_mime.add_header('Content-Disposition', 'attachment', filename="image.jpg")
        msg.attach(image_mime)
    server = smtplib.SMTP(email_host, email_port)
    server.starttls()
    server.login(email_login, email_password)
    text = msg.as_string()
    server.sendmail(email_login, 'adwiesek@wp.pl', text)
    server.quit()

def recieve_feedback(fall_list,img_queue):
    flag = False
    try:
        packet = client.recv(1024)
        result = pickle.loads(packet)
    except: 
        pass
    print(result,type(result))
    if result == True:
        fall_list.append(True)
    if len(fall_list) == 4:
        fall_list.pop(0)
    try:
        if len(fall_list) == 3 and fall_list[-1] == fall_list[-2] == fall_list[-3] == True:
            print("ALERT!")
            fall_list.pop(0)
            fall_list.pop(0)
            fall_list.pop(0)
            image = img_queue.get()
            send_alert(image)
    except:
        pass
    image = img_queue.get()
    del image

    return flag

def reciever(img_queue):
    fall_list = []
    while True:
        flag = recieve_feedback(fall_list,img_queue)
        if flag:
            break

def transmiter(idx,img_queue):
    vc = cv2.VideoCapture(0) 
    for i in range(idx):
        send_snapshot(vc,img_queue)
    del vc
    client.send(pickle.dumps([0,'close']))

def main():

    img_queue = queue.Queue()
    recieving_thread = Thread(target = reciever, args = (img_queue))
    transmiter_thread = Thread(target = transmiter, args = (10,img_queue))
    recieving_thread.start()
    transmiter_thread.start()
    transmiter_thread.join()
    recieving_thread.join()

if __name__=="__main__":
    main()
