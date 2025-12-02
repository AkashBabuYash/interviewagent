from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import edge_tts
import asyncio
import re
import uuid
import os
from playsound import playsound
import speech_recognition as sr

def clean_text(text):
    return re.sub(r'[^\x00-\x7F]+', ' ', text)


voices = {
    "1": "en-US-AriaNeural",      
    "2": "en-US-JennyNeural",     
    "3": "en-GB-LibbyNeural",     
    "4": "en-AU-NatashaNeural",   
    "5": "en-US-GuyNeural",       
    "6": "en-GB-RyanNeural",      
    "7": "en-AU-WilliamNeural",   
    "8": "en-US-AnaNeural"        
}

print("Select a voice:")
for k, v in voices.items():
    print(f"{k}. {v}")
choice = input("Enter 1-8: ")
voice_choice = voices.get(choice, "en-US-AriaNeural")  

async def speak(text):
    text = clean_text(text)
    communicate = edge_tts.Communicate(text, voice_choice)
    temp_file = f"temp_{uuid.uuid4().hex}.mp3"
    await communicate.save(temp_file)
    playsound(temp_file)
    os.remove(temp_file)

google_api_key = ""
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=google_api_key)

# Prompt as structured interviewer
prompt_template = PromptTemplate(
    input_variables=["history", "question_number"],
    template="""
You are an AI interviewer named Agent Gemini. Your task is to interview a candidate.
- Start by welcoming the candidate and asking them to introduce themselves.
- Then ask exactly 10 interview questions, one at a time.
- After the 10th question, give a short rating/feedback based on the answers.
- Keep questions professional and relevant.
- Only respond to one question at a time.
- Include the question number when asking each question.

Conversation so far:
{history}

Next question number: {question_number}
"""
)

parser = StrOutputParser()
chain = prompt_template | model | parser

history = []
recognizer = sr.Recognizer()
question_number = 1

while question_number <= 10:
    if question_number == 1 and not history:
        greeting = "Welcome to the interview with Agent Gemini. Let's start! Please tell me about yourself."
  
        asyncio.run(speak(greeting))
        history.append(f"Gemini: {greeting}")
    if question_number==10:
        greeting="thank you. You can go"
        asyncio.run(speak(greeting))
        history.append(f"Gemini: {greeting}")

    else:
   
        try:
            with sr.Microphone() as source:
                print("🎤 Speak now (or type if you prefer)...")
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
            user_input = recognizer.recognize_google(audio)
          
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            user_input = input("🗨 You (type): ")

        if user_input.lower() == "stop":
            print("Interview ended by user.")
            break

        history.append(f"You: {user_input}")

        conversation = "\n".join(history)
        response = chain.invoke({"history": conversation, "question_number": question_number})
        history.append(f"Gemini: {response}")
       
        asyncio.run(speak(response))

        question_number += 1


final_feedback_prompt = PromptTemplate(
    input_variables=["history"],
    template="""
You are Agent . Based on the candidate's answers in this conversation, give a short maximum 3 line professional rating and feedback. Conversation:
{history}
"""
)
feedback_chain = final_feedback_prompt | model | parser
feedback = feedback_chain.invoke({"history": "\n".join(history)})

asyncio.run(speak(feedback))
