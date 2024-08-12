import fitz   
import re
import json
import gradio as gr
from groq import Groq

GROQ_API_KEY='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'    # Get your api key from https://console.groq.com/keys

def extract_pdf_text(pdfs,):
    pdf_texts = []
    for pdf in pdfs:
        doc = fitz.open(pdf)
        text = ''
        for i in range(doc.page_count):
            text += doc.get_page_text(i)
        pdf_texts.append(text)
    return pdf_texts

def extract_keywords(job_description):
    format = """
    Please provide the response in the following python list format:
    ["keyword1" , "keywords2" , (and so on)]                                                                                                |
    Input: Job Description . Extract only relevant keywords.
    Output:
    """
    prompt = format + 'Extract  relevant keywords from the following job description to search these keywords in CVs.Do not extract general keywords like "CS","IT"\n' + job_description 
    client = Groq(api_key=GROQ_API_KEY,)
    chat_completion = client.chat.completions.create(
    messages=[ {  "role": "user", "content": prompt, } ], 
    model="llama-3.1-70b-versatile", 
    )
    response = chat_completion.choices[0].message.content
    keywords = re.search(r'\[.*\]', response, re.DOTALL)
    keywords_list = keywords.group(0)
    # Convert the extracted string to a Python list
    keywords_list = eval(keywords_list)
    return keywords_list

def filter_resumes(pdfs_text,keywords):
    matching_pdfs = []
    for i in range(len(pdfs_text)):
        if any(keyword.lower() in pdfs_text[i].lower() for keyword in keywords) :
           matching_pdfs.append(pdfs_text[i])
    return matching_pdfs

def get_scoring_from_LLM(resumes,job_description):
    format = """
     Please provide the response in the following JSON format :
       {
        "Candidate Name": "Talha Mohy Ud Din",
        "Contact Number": "(+92) 33333345",
        "Email ID": "talhamd00@gmail.com",
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
        prompt = 'You are an excellent but very strict CV shortlister, you will be provided CV text inside this delimitter ####  and then there is a Job Description inside this delimitter @@@@,you have to intelligently match CV with  given Job Description ' + format + '####' + resume +'####'+ 'Rate very strictly the given resumes out of 100.0 for this job description : \n' +'@@@@'+ job_description + '@@@@' 
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

def get_top_resumes(json_responses, k):
    sorted_data = sorted(json_responses, key=lambda x: x['Rating'], reverse=True)
    top_k_candidates = sorted_data[:k]
    for candidate in top_k_candidates:
       print(candidate)
    return top_k_candidates
     
def save_json_files(json_responses):
    file_path = 'candidates_data.json'
    with open(file_path, 'w') as file:
        json.dump(json_responses, file, indent=4)

def format_candidates(candidates):
    formatted_str = ""
    for candidate in candidates:
        formatted_str += f"""
        <div style='border:1px solid #ddd; padding:10px; margin:10px;'>
            <h2>{candidate['Candidate Name']}</h2>
            <p><strong>Contact Number:</strong> {candidate['Contact Number']}</p>
            <p><strong>Email ID:</strong> {candidate['Email ID']}</p>
            <p><strong>LinkedIn Link:</strong> {candidate['LinkedIn Link'] if candidate['LinkedIn Link'] else 'N/A'}</p>
            <p><strong>Github Link:</strong> {candidate['Github Link'] if candidate['Github Link'] else 'N/A'}</p>
            <p><strong>Cumulative Experience:</strong> {candidate['Cumulative Experience'] if candidate['Cumulative Experience'] else 'N/A'}</p>
            <p><strong>Rating:</strong> {candidate['Rating']}</p>
            <p><strong>Reason:</strong> {candidate['Reason']}</p>
        </div>
        """
    return formatted_str
 
def main(pdfs,job_title,job_description,k):
    k = int(k)
    pdf_texts = extract_pdf_text(pdfs)
    keywords = extract_keywords(job_description)
    print("keywords : ",keywords)
    filtered_resumes = filter_resumes(pdf_texts,keywords)
    print("No of resumes = ",len(filtered_resumes))
    json_responses = get_scoring_from_LLM(filtered_resumes,job_description)  
    #save_json_files(json_responses)
    if k > len(filtered_resumes):
        k = len(filtered_resumes)
    top_resumes = get_top_resumes(json_responses, k)
    print(len(top_resumes))
    fomatted_resumes = format_candidates(top_resumes)
    print(fomatted_resumes)
    return fomatted_resumes

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            pdf_files = gr.File(label="Upload PDF Files", file_count="multiple", file_types=[".pdf"])
            job_title = gr.Textbox(label="Job Title")
            job_description = gr.Textbox(label="Job Description")
            top_k  = gr.Textbox(label="Top K")
            upload_button = gr.Button("Upload")
          
        with gr.Column():
            output_box = gr.HTML(label="Extracted Information")
    
    upload_button.click(main, [pdf_files,job_title,job_description,top_k], output_box)

demo.launch()