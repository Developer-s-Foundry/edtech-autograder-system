
# EdTech Autograder System
**Required Python Version: 3.10+**


A scalable, asynchronous autograder platform for programming assignments built with **FastAPI, Celery, Redis, PostgreSQL, React, and Judge0**.

This system enables instructors to define structured programming assessments and automatically evaluate student submissions in a secure execution environment without manual intervention.

---

##  Overview

The EdTech Autograder System is a full-stack distributed application designed to solve one of the most time-intensive problems in technical education: grading programming assignments.

* Students upload Python solutions.
* Instructors define evaluation criteria.
* The system grades submissions asynchronously using secure sandboxed execution.

The architecture is designed to reflect real-world production patterns used in scalable systems.

---

##  Core Capabilities

### Instructor Features

* Create and edit programming assignments
* Define IO-based test cases
* Add assert-based unit test specifications
* Configure static code analysis rules
* Publish assignments
* View student submissions and grading breakdowns

### Student Features

* View published assignments
* Upload Python `.py` files
* Track submission status (queued → running → completed)
* View score breakdown
* Receive structured grading feedback
* (Optional) Receive AI-assisted improvement suggestions

---

## ⚙️ Grading Pipeline

The grading engine operates asynchronously:

1. Student uploads solution
2. FastAPI stores submission in PostgreSQL
3. Submission task enqueued in Redis
4. Celery worker processes task
5. Code sent to Judge0 for secure execution
6. IO tests evaluated
7. Unit tests evaluated
8. Static analysis performed (AST + Radon)
9. Weighted score computed
10. Feedback generated
11. Results stored and returned via API

This ensures the API remains responsive even during heavy grading loads.

---

## Architecture

### System Components

* **Frontend:** React
* **Backend API:** FastAPI
* **Database:** PostgreSQL
* **Task Queue:** Celery
* **Message Broker:** Redis
* **Execution Engine:** Judge0 (hosted)
* **Static Analysis:** AST module + Radon

### Architecture Flow

```
Student UI → FastAPI → PostgreSQL
FastAPI → Redis (enqueue task)
Celery Worker ↔ Redis
Celery Worker → Judge0
Celery Worker → PostgreSQL
Student UI ← FastAPI ← PostgreSQL
```

The grading process is fully asynchronous and non-blocking.

---

## Database Design

Core entities include:

* Users (students, instructors)
* Assignments
* IO Test Cases
* Unit Test Specs
* Static Rules
* Submissions
* Grading Runs
* Test Case Results
* Static Analysis Reports

The schema is normalized and supports:

* Multiple submission attempts
* Regrading
* Scalable evaluation
* Feedback persistence
* Future multi-language support

---

## Security Model

* Student code is **never executed on the main server**
* All execution is handled by Judge0 in a sandboxed container
* Execution limits enforced:

  * CPU time
  * Memory
  * Timeout
* Redis only acts as a message broker
* Celery workers handle background processing safely

---

## Scoring Strategy

Each assignment defines weight distribution:

* IO Tests
* Unit Tests
* Static Analysis

Final score is computed as:

```
score_total =
(weight_io × io_score) +
(weight_unit × unit_score) +
(weight_static × static_score)
```

Feedback is generated deterministically from grading results.

AI-generated suggestions (if enabled) never affect scoring.

---

## Example Demo Scenarios

* Fully correct solution → 100% score
* Incorrect logic → partial score
* Infinite loop → timeout handled gracefully
* Syntax error → structured failure response
* Static rule violation → complexity or forbidden import flagged

---

## 🛠 Installation & Setup

### 1️⃣ Clone Repository

```
git clone git@github.com:Developer-s-Foundry/edtech-autograder-system.git
cd edtech-autograder-system
```

---

## 2️⃣ Backend Setup

### Ensure Python Version

This project requires **Python 3.10+**.

Verify your installed version:

```
python --version
```

It must return:

```
Python 3.10.x
```

If you are using `pyenv`:

```
pyenv install 3.10
pyenv local 3.10
```

---

### Create Virtual Environment

Create the virtual environment using Python 3.10:

```
python -m venv venv
```

---

### Activate Virtual Environment

```
# Windows
venv\Scripts\activate 

# macOS/Linux
source venv/bin/activate
```

---

### Install Dependencies

⚠️ Ensure the virtual environment was created using Python 3.10+ before installing dependencies.

```
pip install -r requirements.txt
```

---

### Configure Environment Variables

```
DATABASE_URL=
REDIS_URL=
CELERY_BROKER_URL=
JUDGE0_BASE_URL=
JUDGE0_API_KEY=
```

---

### Run API

```
uvicorn app.main:app --reload
```

---

### Start Celery Worker

```
celery -A app.celery_app worker --loglevel=info
```

---

### 3️⃣ Frontend Setup

```
cd frontend
npm install
npm run dev
```

---

### 4 Database Migration
```
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

---

## Scalability Design

This system demonstrates:

* Asynchronous processing architecture
* Distributed system coordination
* Message broker pattern
* Background worker model
* Separation of concerns
* Execution isolation
* Production-ready data modeling

The design supports horizontal scaling of Celery workers and Redis-backed task distribution.

---

## Technical Concepts Demonstrated

* REST API design
* Role-based authentication (JWT)
* Distributed system messaging
* Background task processing
* Secure remote code execution
* Static code parsing using AST
* Cyclomatic complexity analysis
* Structured feedback generation
* Clean ERD modeling
* MVP-first architecture planning

---

## Future Enhancements

* Multi-language grading (C++, Java, etc.)
* WebSocket real-time result streaming
* Plagiarism detection
* Analytics dashboard
* Rate limiting
* Submission history comparisons
* Kubernetes deployment
* Self-hosted Judge0 cluster
* AI grading for written assignments

---

## Capstone Context

This project was developed as a capstone-level system to demonstrate:

* System design thinking
* Backend architecture proficiency
* Asynchronous processing expertise
* Full-stack development capability
* Secure execution model integration

---

## Contributors:

* [Chima Enyeribe](https://github.com/JasperZeroes)
* [Aisha](https://github.com/)
* [Oluwatobiloba Okunobgbe](https://github.com/JesseGreat)

---

## 📄 License

This project is for educational and demonstration purposes.

---
testing the readme file and my repo access ... Oluwatobiloba
