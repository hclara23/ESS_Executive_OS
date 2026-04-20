# Create app password for email: https://myaccount.google.com/u/4/apppasswords

import os
from email.message import EmailMessage
import ssl, smtplib
from Features.Face.Ear import understand
from Features.Face.Mouth import speak
from Features.DataCheck import isBlank, isCorrect
import Features.Database as db

def add_email_to_contact():
        speak("Please type the name of the person below")
        speak("Please type new email id below")
        email_receiver = input("Enter new email id: ")

        #Blank feild
        email_receiver = isBlank(email_receiver, topic_msg="new email id to add.")

        #Same email
        emailinfo=db.Emaildetails()
        if email_receiver == emailinfo[0]:
            speak("You have entered the same current EmailID")
            return
        newname=input("Enter the name: ")
        db.Add_email(newname, email_receiver)
        speak(f"{newname} has been successfully added in your contact")

def set_email_sender():
    #Email ID change
    speak("Please type new email id below")
    new_email = input("Enter new email id: ")
    emailinfo=db.Emaildetails()
    if new_email == emailinfo[0]:
        speak("You have entered the same current EmailID")
        return

    print("--- If you don't know your app password visit \"https://myaccount.google.com/u/4/apppasswords\" to generate new password. --- ")
    speak("Please type your app password for the provided email id below")
    new_pass = input("Enter app password: ")

    db.SetEmailID(new_email,new_pass)
    speak("Your Email and Password for provided email id has been changed successfully.")

def ifyes(contact):
     while True:
        speak(f"Do you want to save this email {contact} in your contact?")
        response = understand()
        if "no" in response or "not" in response or "not correct" in response or "wrong" in response:
            return False
        elif "yes" in response or "correct" in response or "perfect" in response:
            return True
        else:
            speak("Sorry, I couldn't understand. Please say that again.")

def send_email(user=None):
    from server.mail_service import mail_service
    from Features.Face.Ear import understand
    from Features.Face.Mouth import speak
    from Features.DataCheck import isBlank, isCorrect
    import Features.Database as db

    # Receiver email id
    speak("Whom to send mail?")
    email_receiver = understand()
    email_receiver = isBlank(email_receiver, topic_msg="Whom to send mail?")

    if "@" not in email_receiver:
        _, _, found_id = db.Known_email(email_receiver)
        if found_id:
            email_receiver = found_id
        else:
            speak("The receiver is not in your contacts. Please type the email id below.")
            email_receiver = input("Enter receiver's email id: ")
    
    # Subject
    speak("What's the subject?")
    subject = understand()
    subject = isBlank(subject, topic_msg="What's the subject?")
    
    if not isCorrect(subject):
        speak("Type the subject of the email below.")
        subject = input("Enter subject of the email: ")

    # Body
    speak("What's the email body?")
    body = understand(time=10)
    body = isBlank(body, topic_msg="What's the email body?")
    
    if not isCorrect(body):
        speak("Type the email body below.")
        body = input("Enter email body: ")
    
    # Send using MailService
    try:
        result = mail_service.send_email(
            to_email=email_receiver,
            subject=subject,
            body=body,
            from_user=user
        )
        if result.get("status") == "success":
            speak(f"Email has been sent to {email_receiver} successfully.")
            # Check if we should save contact
            if not db.Known_email(email_receiver)[2]:
                if ifyes(email_receiver):
                    speak("Please type the name of the person below")
                    newname = input("Enter the name: ")
                    db.Add_email_receiver(newname, email_receiver)
                    speak(f"{newname} has been successfully added in your contact")
        else:
            speak(f"Failed to send email: {msg}")
    except Exception as e:
        speak(f"An error occurred while sending email: {str(e)}")

# send_email()