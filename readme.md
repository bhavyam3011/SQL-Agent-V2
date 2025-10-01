

# SQL Agent – Natural Language Database Interface (v2)
# Using LangChain-Langgraph
# v1 without Langgraph
## 📌 Overview

This project implements a **natural-language to SQL agent** that allows users to query and modify multiple mock databases using plain English.
It supports **CRUD operations** with a **human-in-the-loop verification system** to ensure safe database modifications.

The project is built with:

* **Python + FastAPI** for backend REST API
* **SQLite** for multiple mock databases (HR, Healthcare, E-commerce, Finance, Education)


---

## 🚀 Features

* 🔹 **Interact with 5 mock databases** (`hr.db`, `healthcare.db`, `ecommerce.db`, `finance.db`, `education.db`)
* 🔹 **Natural language CRUD support** (Read/Write/Update/Delete)
* 🔹 **Human-in-the-loop approval** for Create/Update/Delete before commit
* 🔹 **Pending queue manager** to track and approve/reject modifications
* 🔹 **FastAPI REST endpoints** with interactive Swagger UI


---

## ⚙️ Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/mini-sql-agent.git
cd mini-sql-agent
```

### 2. Create Virtual Environment (Optional)

```bash
python -m venv venv
source venv/bin/activate   # on Linux/Mac
venv\Scripts\activate      # on Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
after completed,
pip install langchain_google_genai
```

### 4. Environment Variables

Create a `.env` file in the project root and add your Gemini API key:

```
GEMINI_API_KEY=your_api_key_here

```



### 5. Run FastAPI App

with Uvicorn:

```bash
uvicorn main:app --reload --port 8000
```

---

## 🖥️ API Usage

Once running, access:

* API Docs: [http://localhost:8000/docs] (http://localhost:8000/docs) and initialize database and test your nl-queries
* Example endpoint: `/query?text=Show all employees in HR&db=hr`
* Make sure that the backend url set in app.js is same as localhost port, else change it accordingly. 

---
## FASTAPI Screenshots and also with Frontend. 

<img width="1911" height="1080" alt="Screenshot (218)" src="https://github.com/user-attachments/assets/4bc518fb-f78e-4dfb-a105-0db71decf0fa" />
<img width="1920" height="1080" alt="Screenshot (219)" src="https://github.com/user-attachments/assets/f37e3d4e-cfe0-403b-8ed3-310e3dfb4a69" />
<img width="1920" height="1080" alt="Screenshot (238)" src="https://github.com/user-attachments/assets/b200d927-2d17-48c8-9a4d-c34f99aa2a22" />
<img width="1920" height="1080" alt="Screenshot (239)" src="https://github.com/user-attachments/assets/45611c8d-b9fd-4a45-8260-0608c8f5e73d" />
<img width="1920" height="1080" alt="Screenshot (240)" src="https://github.com/user-attachments/assets/5a053f79-4f31-4349-a101-15b3eca6d370" />
<img width="1920" height="1080" alt="Screenshot (241)" src="https://github.com/user-attachments/assets/624df9a3-6dde-427e-a10b-bfb9988daeea" />
<img width="1920" height="1080" alt="Screenshot (242)" src="https://github.com/user-attachments/assets/d3c14796-5eeb-4cc9-933f-fe9307e6958b" />
<img width="1920" height="1080" alt="Screenshot (243)" src="https://github.com/user-attachments/assets/c832f09e-731d-4e34-827c-05f820bbebe3" />
<img width="1920" height="1080" alt="Screenshot (244)" src="https://github.com/user-attachments/assets/6a056c2d-86bf-4b38-87d9-6607f9d97fe6" />
<img width="1920" height="1080" alt="Screenshot (245)" src="https://github.com/user-attachments/assets/7d7bcdfc-e05e-438d-a2be-f81cba09e6af" />
<img width="1920" height="1080" alt="Screenshot (246)" src="https://github.com/user-attachments/assets/90241cc5-f464-4d17-ad79-826d77f3347e" />

## LangGraph Workflow
<img width="1536" height="1024" alt="ss" src="https://github.com/user-attachments/assets/ee0a4230-e9d9-423b-8d53-9f2f3bb5b664" />





## ✅ Status
This is a classic agentic made with (langchain-LangGraph) but yet slow with other LLMs.
Do try LangSmith Integration, added in the requirements. Add your LangSmith api directly via env file.


---
=======
