import gradio as gr
import fitz
import os
import imaplib
from dotenv import load_dotenv, set_key
import time
import email
from email.header import decode_header
from datetime import datetime, timezone
import re
import json
from groq import Groq
GROQ_API_KEY='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'    # Get your api key from https://console.groq.com/keys

start = False
start_datetime = datetime.now(timezone.utc)
start_date_str = start_datetime.strftime("%d-%b-%Y")
print(f"Searching for emails since: {start_date_str} {start_datetime.time()} UTC")

def saveEmailCredential(email,password):
    if not os.path.exists('.env'):
          open('.env', 'w').close()
    load_dotenv()
    set_key('.env', 'Email', email)
    set_key('.env', 'Password', password)
    return "Credentials saved successfully."

def connect_to_mail(email_provider, username, password):
    imap_servers = {
        'gmail': 'imap.gmail.com',
        'outlook': 'imap-mail.outlook.com'
    }

    if email_provider not in imap_servers:
        print(f"Unsupported email provider: {email_provider}")
        return None

    try:
        # Connect to the mail server
        mail = imaplib.IMAP4_SSL(imap_servers[email_provider])
        # Login to your account
        mail.login(username, password)
        print(f"Logged in successfully to {email_provider}")
        return mail
    except imaplib.IMAP4.error as e:
        print(f"Failed to login to {email_provider}: {e}")
        return None
   
def read_JD(JDs):
    JD_Text = {}
    for jd in JDs:
        doc = fitz.open(jd)
        text = ''
        for i in range(doc.page_count):
            text  += doc.get_page_text(i)
        name = os.path.splitext(os.path.basename(jd.name))[0]
        JD_Text[name.lower()] = text
    return JD_Text

def search_emails(mail, subjects=None, from_email=None):
    if mail is None:
        return []

    mail.select("inbox")
    email_ids = []

    search_criteria = [f'SINCE {start_date_str}', 'UNSEEN']

    if subjects:
        for subject in subjects:
            subject_criteria = search_criteria + [f'SUBJECT "{subject}"']
            result, data = mail.search(None, *subject_criteria)
            if result == "OK":
                email_ids.extend(data[0].split())

    if from_email:
        from_criteria = search_criteria + [f'FROM "{from_email}"']
        result, data = mail.search(None, *from_criteria)
        if result == "OK":
            email_ids.extend(data[0].split())

    return list(set(email_ids))  # Remove duplicates

def fetch_email(mail, email_id):
    result, msg_data = mail.fetch(email_id, "(RFC822)")
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            return msg

def save_attachment(msg, download_folder="attachments"):
    filenames = []
    if not os.path.isdir(download_folder):
        os.makedirs(download_folder)

    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get("Content-Disposition") is None:
            continue

        filename = part.get_filename()
        if filename and filename.lower().endswith(".pdf"):
            filepath = os.path.join(download_folder, filename)
            pdf = part.get_payload(decode=True)
            with open(filepath, "wb") as f:
                f.write(pdf)
            print(f"Attachment saved: {filename}")
            filenames.append(filename)
    return filenames

def get_cv_from_mail(mail,subjects,from_email=None):
    Resumes = []
    Subjects = []
    email_ids = search_emails(mail, subjects=subjects, from_email=from_email)
    print("Searched Email IDs : ",email_ids)
    for email_id in email_ids:
        msg = fetch_email(mail, email_id)
        #print("Fetched Msg : ",msg)
        if msg:
            # Check if the email was received after the specified start datetime
            msg_date = msg["Date"]
            msg_datetime = email.utils.parsedate_to_datetime(msg_date)
            if msg_datetime >= start_datetime:
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8")
                from_ = msg.get("From")
                print(f"Subject: {subject}")
                print(f"From: {from_}")
                filenames = save_attachment(msg)
                print()
                if len(filenames)>0:
                     Resumes.append(filenames)
                     Subjects.append(subject)
   
    return (Resumes,Subjects)

def get_scoring_from_LLM(resumes,job_description):
    format = """
     Please provide the response in the following JSON format :
       {
        "Candidate Name": "Talha Mohy Ud Din",
        "Contact Number": "(+92) 33333345",
        "Email ID": "talhamd1200@gmail.com",
        "LinkedIn Link" : "linkedin.com/sjflsdkjf",   (if not provided null)
        "Github Link": "github.com/",      (if not provided null)
        "Rating": 35.3 ,
        "Cumulative Experience" : "2 years, 3 months",
        "Reason": "The candidate lacks experience and skills in software testing and quality assurance, which are the primary requirements for the Senior Software Quality Assurance Engineer role. While the candidate has a strong foundation in programming and has worked on various projects, they do not have the necessary expertise in QA methodologies, automation tools, and test automation frameworks. The candidate's current skillset is more aligned with a junior software development role."
        }
    """
    #print("Type pf Resumes ",type(resumes))
    json_responses = []
    for resume in resumes:
        prompt = 'You are an excellent and very strict CV shortlister, you will be provided CV text inside this delimitter ####  and then there is a Job Description inside this delimitter @@@@,you have to intelligently match CV with  given Job Description ' + format + '####' + resume +'####'+ 'Rate very strictly the given resumes out of 100.0 for this job description : \n' +'@@@@'+ job_description + '@@@@' 
        client = Groq(api_key=GROQ_API_KEY,)
        chat_completion = client.chat.completions.create(
        messages=[ {  "role": "user", "content": prompt, } ], 
        model="llama3-70b-8192", 
        response_format={"type": "json_object"},
        )
        response = chat_completion.choices[0].message.content
        print("Response : ",response)
        json_match = re.search(r'\{.*\}',response,re.DOTALL)
        if json_match:
            json_string = json_match.group(0)
            json_data = json.loads(json_string)
            #print("Parsed JSON: ",json_data)
        else:
            print("No valid JSON found in the response")
            json_data = None
        json_responses.append(json_data)
    
    return json_responses

def extract_pdf_text(pdfs):
    basedir = 'attachments/'
    pdf_texts = []
    for pdf in pdfs:
        if isinstance(pdf, list):
            for p in pdf:
                doc = fitz.open(basedir+p)
                text = ''
                for i in range(doc.page_count):
                    text += doc.get_page_text(i)
                pdf_texts.append(text)
        else:
            doc = fitz.open(basedir+pdf)
            text = ''
            for i in range(doc.page_count):
                text += doc.get_page_text(i)
            pdf_texts.append(text)

    return pdf_texts

def save_json_files(json_responses):
    file_path = 'Rating_Data.json'
    with open(file_path, 'a') as file:
        json.dump(json_responses, file, indent=4)
        file.write('\n')

def append_to_json_file(new_data):
    try:
        file_path = 'Rating_Data.json'
        # Check if the file exists and read the existing data
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                existing_data = json.load(file)
        else:
            existing_data = []
        
        # Ensure existing data is a list, or convert it to a list if necessary
        if not isinstance(existing_data, list):
            existing_data = [existing_data]
        
        # Ensure new data is a list, or convert it to a list if necessary
        if not isinstance(new_data, list):
            new_data = [new_data]
        
        # Append new data to the existing data
        existing_data.extend(new_data)
        
        # Write the updated data back to the file
        with open(file_path, 'w') as file:
            json.dump(existing_data, file, indent=4)
        
        print("Data appended successfully.")
    
    except Exception as e:
        print(f"An error occurred: {e}")

def main(mail,password,pdf_files):
    # save and connect to mail
    saveEmailCredential(mail,password)
    mail = connect_to_mail('gmail',mail,password)
    if mail == None:
       return {status: gr.Textbox(value="Login Failed.Email or Password is incorrect",visible=True)}

    # read job description pdf
    JDs = read_JD(pdf_files)
    print("JDs Read")
    print(JDs)

    #Reterive CV from Email
    global start
    start = True
    try:
        while start:
         resumes,subjects = get_cv_from_mail(mail,subjects=["CV","Resume","cv","Cv","resume"])
         print(f"Found {len(resumes)} resumes")
         if(len(resumes)>0):
          for i in range(len(resumes)):
            print("Type of resumes : ",type(resumes[i]))
            print("Resumes : ",resumes[i])
            dept = subjects[i].split()[0].lower()
            pdf_text = extract_pdf_text(resumes[i])
            print("PDF TEXT : ",pdf_text)
            json_responses = get_scoring_from_LLM(pdf_text,JDs[dept])
            print("Json responses : ",json_responses)
            append_to_json_file(json_responses)
            time.sleep(10)
    except KeyboardInterrupt:
         mail.logout()
         print("Program interrupted by the user")
    
def stop():
    global start
    start = False
    return {stop_status: gr.Textbox(value="Process Stopped Successfully",visible=True)}

def show():
    with open('Rating_Data.json','r') as file:
        ratings = json.load(file)
    return ratings

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            mail = gr.Textbox(label="Email")
            password = gr.Textbox(label="App Specific Password")
            pdf_files = gr.File(label="Upload Job Descriptions PDF", file_count="multiple", file_types=[".pdf"])
            start_button = gr.Button("Start")
            status = gr.Textbox(label="Login Status",visible=False)
            stop_button = gr.Button("Stop")
            stop_status = gr.Textbox(label="Stop Status",visible=False)
        with gr.Column():
            output_box = gr.JSON(label="Extracted Information")
            show_button = gr.Button("Show")

    
    start_button.click(main, [mail,password,pdf_files], status)
    stop_button.click(stop,[],stop_status)
    show_button.click(show,[],output_box)

demo.launch()
