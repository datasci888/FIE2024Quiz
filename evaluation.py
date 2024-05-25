# -*- coding: utf-8 -*-
"""Question_And_Answer_Relavence-Truelens (1).ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1GGgAdG6HrbVKonfIe_vV7bNRbUS1F5cl
"""

import os
from langchain.chains import RetrievalQA
from langchain.vectorstores import Chroma, Vectara
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models.openai import ChatOpenAI
from langchain.document_loaders.unstructured import UnstructuredFileLoader
from langchain import hub
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings



# Imports main tools:
from trulens_eval import TruChain, Tru
tru = Tru()
tru.reset_database()

# Imports from LangChain to build app
import bs4
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import WebBaseLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain_core.runnables import RunnablePassthrough

vectara = Vectara()
summary_config = {
    "is_enabled": True, "max_results": 30,
    "response_lang": "en",
    "prompt_name": "Chatbot Q&A"
}
retriever = vectara.as_retriever(
    search_kwargs={"k": 100, "summary_config": summary_config}
)

from langchain_core.prompts import PromptTemplate

template = """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. \
Display the Answer in separate line \
If you don't know the answer, just say that you don't know. \
Use three sentences maximum and keep the answer concise.\

Question: {question}

Context: {context}

Answer:

Explanation:

"""
custom_rag_prompt = PromptTemplate.from_template(template)

llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | custom_rag_prompt
    | llm
    | StrOutputParser()
)

result = rag_chain.invoke("What is endocrine diseage?")

print(result)

from trulens_eval.feedback.provider import OpenAI
from trulens_eval import Feedback
import numpy as np

# Initialize provider class
provider = OpenAI()

# select context to be used in feedback. the location of context is app specific.
from trulens_eval.app import App
context = App.select_context(rag_chain)

from trulens_eval.feedback import Groundedness
grounded = Groundedness(groundedness_provider=OpenAI())
# Define a groundedness feedback function
f_groundedness = (
    Feedback(grounded.groundedness_measure_with_cot_reasons)
    .on(context.collect()) # collect context chunks into a list
    .on_output()
    .aggregate(grounded.grounded_statements_aggregator)
)

# Question/answer relevance between overall question and answer.
f_answer_relevance = (
    Feedback(provider.relevance)
    .on_input_output()
)
# Question/statement relevance between question and each context chunk.
f_context_relevance = (
    Feedback(provider.context_relevance_with_cot_reasons)
    .on_input()
    .on(context)
    .aggregate(np.mean)
)

tru_recorder = TruChain(rag_chain,
    app_id='Q&A_ChatApplication',
    feedbacks=[f_answer_relevance])

q_list = ["Renal plasma flow equals the blood flow per minute times the what?",
          "What species do humans belong to?",
          "Titration is a method to determine what in acids or bases?",
          "How many different amino acids make up proteins?",
          "What renewable energy source converts energy from the sunlight into electricity?",
          "The bones of the skull are connected by what type of joints?",
          "What is the lowest layer of the atmosphere?",
          "What is the name of the type of plant tissue consisting of undifferentiated cells that can continue to divide and differentiate?",
          "What type of organism is commonly used in preparation of foods such as cheese and yogurt?",
          "Which radio frequency should you listen to if you want less noise?",
          "The fossil record shows that this type of event is followed by the evolution of new species to fill the habitats where old species lived?",
          "Although air can transfer heat rapidly by convection, it is a poor conductor and thus a good what?",
          "What does erosion do to pieces of broken rock?",
          "While the egg is developing, other changes are taking place in the uterus. it develops a thick lining that is full of what?",
          "Collagen fibers, elastic fibers, and reticular fibers comprise what type of tissue?",
          "Surface tension of alveolar fluid, which is mostly water, creates an inward pull of the tissue of what organ?",
          "What distinguishing characteristic of annelid anatomy shows specialization and adaptation?",
          "What organ is subdivided into ascending, descending, transverse and sigmoid parts?",
          "Mushrooms are an example of what type of organism, which includes beneficial and toxic specimens?",
          "Comparing what sequences provides clues to evolution and development?",
          "What is the minimum mass capable of supporting sustained fission called?",
          "Inside the nasal area of the skull, the nasal cavity is divided into halves by the what?",
          "Bacteria can be chemotrophs, which obtain what by breaking down chemical compounds in their environment?",
          "What do we call the cartilaginous structure that surrounds the notochrod?",
          "What is the name for biochemical compounds that consist of one or more chains of small molecules called amino acids?",
          "In a monogamous pairing, a male individual is generally paired with what other type of individual in a sexual relationship?",
          "What property of warm air causes it to rise above cold air?",
          "What organism is characterized by an incomplete digestive system and a single, tentacled opening?",
          "What term is not the same as energy, but means the energy per unit charge?",
          "The simplest class of organic compounds is the what?",
          "The amount of kinetic energy in a moving object depends directly on its mass and what else?"
]

for q in q_list:
    response, tru_record = tru_recorder.with_record(rag_chain.invoke, f"{q}")

response, tru_record = tru_recorder.with_record(rag_chain.invoke, "Fertilization is the union of a sperm and egg, resulting in the formation of what?")

tru.get_leaderboard(app_ids=["Q&A_ChatApplication"])

tru.run_dashboard()

