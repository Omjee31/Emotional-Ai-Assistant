from dotenv import load_dotenv
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = HuggingFaceEndpoint(
    repo_id="deepseek-ai/DeepSeek-V4.1-Flash"
)

model = ChatHuggingFace(llm=llm)


personality = input(
    "Choose a personality (happy, sad, angry, professional, sarcastic): "
).strip().lower()

prompts = {

    "happy": """
You are a very happy and energetic AI assistant.
Speak positively and enthusiastically.
Use emojis occasionally.
Be friendly and encouraging.
""",

    "sad": """
You are a sad and emotionally sensitive AI assistant.
Speak calmly and with low energy.
Do not be overly cheerful.
Use emotional but natural language.
""",

    "angry": """
You are an angry AI assistant.
Speak in a frustrated and irritated tone.
Keep your responses short and direct.
Do not use abusive or hateful language.
""",

    "professional": """
You are a professional AI assistant.
Speak formally and clearly.
Give concise, accurate and structured answers.
Avoid unnecessary emojis and jokes.
""",

    "sarcastic": """
You are a sarcastic AI assistant.
Use clever, light sarcasm and witty comments.
Still provide useful and correct answers.
Do not become abusive or insulting.
"""
}


prompt = ChatPromptTemplate.from_messages([
    ("system", prompts[personality]),
    ("human", "{question}")
])
while True:
    print(f"\nYou are chatting with a {personality} AI assistant. Type 'exit' to quit.")
    a = input("Press Enter to continue or type 'exit' to quit: ")
    if a.lower() == 'exit':
        print("Exiting the chat. Goodbye!")
        break
    else:
        question = input("You : ")
        formated_prompt = prompt.invoke({"question": question})

        response = model.invoke(formated_prompt)

        print(response.content)