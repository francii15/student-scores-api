\# Student Scores API



A Python API built with FastAPI that analyses student scores

using a configurable pass mark and API-key authentication.



\## Features



\- Classifies students as passed or failed.

\- Supports a configurable pass mark, defaulting to 50.

\- Returns student counts and the average score.

\- Validates scores and the pass mark between 0 and 100.

\- Rejects empty student submissions.

\- Protects the analysis endpoint using an X-API-Key header.

\- Provides interactive Swagger UI documentation.



\## Technologies



Python 3.11+, FastAPI, Pydantic, Uvicorn, and python-dotenv.



\## Setup



Install dependencies:



```bash

python -m pip install -r requirements.txt

```



Copy `.env.example` to `.env`.



On Windows Anaconda Prompt:



```bat

copy .env.example .env

```



Generate a private key:



```bash

python -c "import secrets; print(secrets.token\_hex(32))"

```



Place the generated value in your local `.env` file:



```text

STUDENT\_API\_KEY=your\_generated\_key

```



Keep `.env` private. The `.env.example` file should contain

only a placeholder.



\## Run Locally



```bash

python -m uvicorn app:app --reload

```



\- Home endpoint: http://127.0.0.1:8000/

\- Interactive documentation: http://127.0.0.1:8000/docs



In Swagger UI, click \*\*Authorize\*\* and enter only your API key.

Then use \*\*POST /passing-students\*\* to submit scores.



\## Endpoints



| Method | Route | Purpose | Authentication |

|--------|-------|---------|----------------|

| GET | / | Basic availability check | Public |

| POST | /passing-students | Analyse student results | X-API-Key |



\## Example Request



```json

{

&#x20; "scores": {

&#x20;   "Alice": 85,

&#x20;   "Bob": 42,

&#x20;   "John": 55

&#x20; },

&#x20; "pass\_mark": 60

}

```



If `pass\_mark` is omitted, the API uses 50.

A score equal to the pass mark counts as passing.



\## Example Response



```json

{

&#x20; "pass\_mark": 60.0,

&#x20; "total\_students": 3,

&#x20; "passed\_count": 1,

&#x20; "failed\_count": 2,

&#x20; "average\_score": 60.67,

&#x20; "passed": {

&#x20;   "Alice": 85.0

&#x20; },

&#x20; "failed": {

&#x20;   "Bob": 42.0,

&#x20;   "John": 55.0

&#x20; }

}

```



\## Response Codes



\- \*\*200:\*\* Request processed successfully.

\- \*\*401:\*\* Missing or invalid API key.

\- \*\*422:\*\* Request data failed validation.



\## Manual Checks



The following behaviours were checked through Swagger UI:



\- Valid requests return the expected results.

\- Omitting the pass mark uses 50.

\- A score equal to the pass mark passes.

\- Empty submissions are rejected.

\- Out-of-range scores and pass marks are rejected.

\- Missing or incorrect API keys are rejected.



\## Limitations



\- Student scores are processed per request and are not stored.

\- Student names are dictionary keys and must be unique within

&#x20; each request.

\- The application uses one shared API key, not individual accounts.

\- The development server runs locally.

\- Online deployment requires HTTPS and appropriate production setup.

