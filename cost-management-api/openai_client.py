from openai import OpenAI 
import spacy 
 
client = OpenAI()
 
nlp = spacy.load("en_core_web_sm") 
def get_nlp_response(prompt): 
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    ) 
    return completion.choices[0].message.content
