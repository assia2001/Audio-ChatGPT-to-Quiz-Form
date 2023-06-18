from __future__ import print_function
import requests
import streamlit as st
from streamlit_lottie import st_lottie
from oauth2client import client, file, tools
from apiclient import discovery
from httplib2 import Http
from PIL import Image
import hydralit_components as hc
import streamlit.components.v1 as components
import sounddevice as sd
import soundfile as sf
import librosa
import speech_recognition as sr
import tempfile
import os
import openai
import toml
import requests
import moviepy.editor as mp
import speech_recognition as sr

#responses=[]
ques = []
texte=""
responses = []
def load_audio(audio_file):
    data, sample_rate = sf.read(audio_file)
    return data, sample_rate

def transcribe_audio(audio_data, sample_rate):
    r = sr.Recognizer()
    
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
        temp_file_path = temp_audio_file.name
        sf.write(temp_file_path, audio_data, sample_rate)
        
        
        with sr.AudioFile(temp_file_path) as source:
            audio = r.record(source)
            transcript = r.recognize_google(audio)
    
    
    os.remove(temp_file_path)
    return transcript

def form_generator():
    
            SCOPES = "https://www.googleapis.com/auth/forms.body"
            DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

            store = file.Storage('token.json')
            creds = None
            if not creds or creds.invalid:
                                    flow = client.flow_from_clientsecrets('votre fichier.json', SCOPES)
                                    creds = tools.run_flow(flow, store)

            form_service = discovery.build('forms', 'v1', http=creds.authorize(
            Http()), discoveryServiceUrl=DISCOVERY_DOC, static_discovery=False)
            NEW_FORM = {
                "info": {
                "title": "Quiz forms",
                }
            }
            NEW_QUESTION = {
                "requests": []
            }

            for i in range(len(ques)):
                    question = ques[i]
                    options = responses[i]

                    create_item = {
                            "createItem": {
                                "item": {
                                    "title": question,
                                    "questionItem": {
                                        "question": {
                                            "required": True,
                                            "choiceQuestion": {
                                                "type": "RADIO",
                                                "options": [
                                                        {"value": option} for option in options
                                                        ],
                                                        "shuffle": True
                                            }
                                        }
                                    }
                                },
                                "location": {
                                    "index": 0
                                }
                            }
                        }

                    NEW_QUESTION["requests"].insert(0,create_item)

                    result = form_service.forms().create(body=NEW_FORM).execute()
                    responder_uri = result['responderUri']
                    question_setting = form_service.forms().batchUpdate(formId=result["formId"], body=NEW_QUESTION).execute()
                    get_result = form_service.forms().get(formId=result["formId"]).execute()
                    return responder_uri


def quiz_generator(prompt):
                    api_endpoint = "https://api.openai.com/v1/chat/completions"
                    headers = {
                    "Authorization": "Bearer votre token",
                    "Content-Type": "application/json"
                    }
                    data = {
                        "model": "gpt-3.5-turbo",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7
                        }
                    response = requests.post(api_endpoint, headers=headers, json=data)
                    if response.status_code == 200:
                        questions = response.json()["choices"]
                        return questions
                    else:
                        return None
# Initialize prompt in session state
if "prompt" not in st.session_state:
    st.session_state["prompt"] = ""

if 'audio_data' not in st.session_state:
    st.session_state['audio_data'] = None
#navbar function : définissons les élements et le style du navbar
def navBar():
    menu_data = [ 
    
    {'id':'Quiz Generator using audio','label':'Quiz Generator using audio','icon':'fas fa-microphone'},
    {'id':'Quiz Generator using video','label':'Quiz Generator using video','icon':'fas fa-video'}
    
    
    ]
    over_theme = {'txc_inactive': '#FFFFFF','menu_background':'#8CDD81','txc_active':'#fffff','option_active':'#ffff'}
    menu_id = hc.nav_bar(menu_definition=menu_data,override_theme=over_theme,home_name='Home',first_select=0)
    return menu_id

# configuration de la premiere interface 

st.set_page_config(page_title='Quiz Generator',layout="wide")
menu_id = navBar()
unique_value = 0
# Sélectionner la page "Home"
if menu_id == 'Home':
                    col1,col2 = st.columns(2)
                    st.subheader("")
                    image = Image.open('data.png')
                    col1.image(image,width=700,use_column_width=True)
                    big_title = '<p style="font-family:Courier; color:#2AAA8A; font-size: 25px; font-weight:bold;">Quiz Generator  </p></br>'
                    col2.markdown(big_title,unsafe_allow_html = True)
                    title1 = '<p style="font-family:Courier; color:#868686; font-size: 20px;">1. Voice Recording </p>'
                    title2 = '<p style="font-family:Courier; color:#868686; font-size: 20px;">2. Speech To text  </p>'
                    title3 = '<p style="font-family:Courier; color:#868686; font-size: 20px;"> 3. Generate a Quiz using hatGPT </p>'
                    title4 = '<p style="font-family:Courier; color:#868686; font-size: 20px;"> 4. Generate google Form'
                    col2.markdown(title1,unsafe_allow_html = True)
                    col2.markdown(title2,unsafe_allow_html = True)
                    col2.markdown(title3,unsafe_allow_html = True)
                    col2.markdown(title4,unsafe_allow_html = True)
                    

if menu_id == 'Quiz Generator using audio':
                    
                    
                    # Commençons par l'enregistrement d'un audio dont l'utilisateur va exprimer la sujet du Quiz à générer
                            def record_audio(duration):
                                sample_rate = 44100  
                                channels = 2        
                                audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels)
                                sd.wait()
                                return audio, sample_rate
                    # enregistrer l'audio 

                            def save_audio(audio, sample_rate, filepath):
                                sf.write(filepath, audio, sample_rate)

                            def convert_audio_to_text(filepath):
                                r = sr.Recognizer()
                                with sr.AudioFile(filepath) as source:
                                     audio_data = r.record(source)
                                     texte = r.recognize_google(audio_data)
                                return texte
                    # 

                            

                            
                            duration = st.number_input("Recording duration (seconds)", min_value=1.0, value=5.0, step=1.0)
                            if "prompt" not in st.session_state:
                                st.session_state["prompt"] = ""
                            if st.button("Record"):
                                st.info("Recording...")
                                audio, sample_rate = record_audio(duration)
                                st.success("Recording complete!")
                                filepath = st.text_input("Enter file path to save the audio", "recorded_audio.wav")
                                save_audio(audio, sample_rate, filepath)
                                st.audio(filepath, format='audio/wav')
                                texte = convert_audio_to_text(filepath)
                                st.header("Extracted Text")
                                st.write(texte)
                                st.session_state["prompt"] = texte
                                st.header("Quiz ")
                                prompt = st.text_area(" ", value=texte)
                            #générer les questions du sujet exprimé par l'utilisateur
                            if st.button("Generate Questions"):
                                prompt = st.session_state["prompt"]
                                if prompt:
                                    questions = quiz_generator(prompt)
                                    
                                    if questions:
                                        content = questions[0]["message"]["content"]
                                        
                                        question_data = content.split('\n\n')

                                        for item in question_data:
                                             item = item.strip()  
                                             if item:
                                                question, choices = item.split('\n', 1)  
                                                question = question.strip()  
                                                choices = choices.split('\n')  
                                                choices = [choice.strip() for choice in choices]  
                                                ques.append(question)
                                                responses.append(choices)
                
                                        print('Questions ',ques)
                                        print('Responses ',responses)
                                        for i in range(len(ques)):
                                            st.success(ques[i])
                                            for j in range(len(responses[0])):
                                                st.write(responses[i][j])
                                                if i==4:
                                                    st.write('')
                    
                                        st.write(form_generator())  
                            primaryColor = st.get_option("theme.primaryColor")
                            s = f"""
                            <style>
                            div.stButton > button:first-child {{ border: 5px solid {primaryColor}; border-radius: 20px; background-color:#8CDD81;margin-left:400px; width:180px; color:#FFFF;}}
                            .stTextInput>div>div>input{{box-shadow: 0 2px 28px 0 rgba(159, 226, 191);color: #FFFFF;text-align:center;}}
                            div.sTitle > title:first-child {{text-align: center;}}
                            <style>
                            """
                            st.markdown(s, unsafe_allow_html=True)
if menu_id == 'Quiz Generator using video':
       
    import moviepy.editor as mp
    import speech_recognition as sr

    def video_to_text(video_path):
    # Load the video using moviepy
        video = mp.VideoFileClip(video_path)
    
    # Extract the audio from the video
        audio = video.audio
        temp_audio_path = "temp_audio.wav"
        audio.write_audiofile(temp_audio_path)
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_audio_path) as source:
       
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
    
    
        os.remove(temp_audio_path)
    
        return text
    st.title("Video Speech-to-Text Conversion")
    # File uploader to load the video
    video_file = st.file_uploader("Upload a video", type=["mp4", "mov"])
    
    if video_file is not None:
        
            temp_video_path = "temp_video.mp4"
            with open(temp_video_path, "wb") as file:
                file.write(video_file.read())
            texte = video_to_text(temp_video_path)
            st.subheader("Extracted Text")
            st.write(texte)
            st.session_state["prompt"] = texte
            prompt = st.text_area(" ", value=texte)

    if st.button("Generate Questions"):
                                
                                prompt = st.session_state["prompt"]
                                
                                if prompt:
                                    questions = quiz_generator(prompt)
                                    
                                    if questions:
                                        content = questions[0]["message"]["content"]
                                        
                                        question_data = content.split('\n\n')

                                        for item in question_data:
                                             item = item.strip()  
                                             if item:
                                                question, choices = item.split('\n', 1)  
                                                question = question.strip()  
                                                choices = choices.split('\n')  
                                                choices = [choice.strip() for choice in choices]  
                                                ques.append(question)
                                                responses.append(choices)
                
                                        print('Questions ',ques)
                                        print('Responses ',responses)
                                        for i in range(len(ques)):
                                            
                                            st.success(ques[i])
                                            for j in range(len(responses[0])):
                                                st.write(responses[i][j])
                                                if i==4:
                                                    st.write('')
                    
                                        st.write(form_generator())
    primaryColor = st.get_option("theme.primaryColor")
    s = f"""
        <style>
        div.stButton > button:first-child {{ border: 5px solid {primaryColor}; border-radius: 20px; background-color:#8CDD81;margin-left:400px; width:180px; color:#FFFF;}}
        .stTextInput>div>div>input{{box-shadow: 0 2px 28px 0 rgba(159, 226, 191);color: #FFFFF;text-align:center;}}
        div.sTitle > title:first-child {{text-align: center;}}
        <style>
        """
    st.markdown(s, unsafe_allow_html=True)

        
        
            






