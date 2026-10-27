\# Student Scores API



\[!\[API Tests](https://github.com/francii15/student-scores-api/actions/workflows/tests.yml/badge.svg)](https://github.com/francii15/student-scores-api/actions/workflows/tests.yml)





A Python API built with FastAPI that analyses student scores using

a configurable pass mark and API-key authentication.



The API returns passing and failing students, student counts,

and the average score.



\## Features



\- Configurable pass mark, defaulting to 50.

\- Passing and failing student classifications.

\- Total, passed, and failed student counts.

\- Average score rounded to two decimal places.

\- Validation of scores and pass marks between 0 and 100.

\- Rejection of empty student submissions.

\- API-key authentication through the `X-API-Key` header.

\- Interactive Swagger UI documentation.

\- Eight automated tests.



\## Technologies



\- Python 3.11+

\- FastAPI

\- Pydantic

\- Uvicorn

\- python-dotenv

\- pytest

\- HTTPX2 for the test client



\## Project Files



| File | Purpose |

|------|---------|

| `app.py` | API routes, authentication, validation, and analysis |

| `test\_app.py` | Automated API tests |

| `requirements.txt` | Python dependencies |

| `.env.example` | Configuration template containing a placeholder |

| `.gitignore` | Excludes private configuration and temporary files |

| `README.md` | Project documentation |



The local `.env` file contains the real API key and must not be

committed to Git.



\## Installation



Clone the repository:



```bash

git clone https://github.com/francii15/student-scores-api.git

cd student-scores-api

```



Create and activate an environment using Anaconda Prompt:



```bat

conda create -n scores-api python=3.11 -y

conda activate scores-api

```



If the environment already exists, activate it without creating it again.



Install dependencies:



```bash

python -m pip install -r requirements.txt

```



\## Configure the API Key



Copy the example configuration to `.env`.



On Windows Anaconda Prompt:



```bat

copy .env.example .env

```



If `.env` already exists, edit it instead of overwriting it.



Generate a random key:



```bash

python -c "import secrets; print(secrets.token\_hex(32))"

```



Open `.env` and replace the placeholder:



```text

STUDENT\_API\_KEY=your\_generated\_key

```



Keep the real key private. `.env.example` should contain only:



```text

STUDENT\_API\_KEY=replace\_with\_your\_own\_generated\_key

```



Restart the application after changing its key.



\## Run Locally



From the project folder:



```bash

python -m uvicorn app:app --reload

```



Open:



\- Home endpoint: http://127.0.0.1:8000/

\- Interactive documentation: http://127.0.0.1:8000/docs



Keep the terminal running while using the API.

Press `Ctrl+C` to stop the server.



The `--reload` option is intended for local development.



\## Endpoints



| Method | Route | Purpose | Authentication |

|--------|-------|---------|----------------|

| GET | `/` | Basic availability check | Public |

| POST | `/passing-students` | Analyse student results | API key required |



\### GET /



Returns:



```json

{

&#x20; "message": "Student Scores API is running"

}

```



\### POST /passing-students



Accepts student scores and an optional pass mark.



\### Request Rules



\- `scores` must contain at least one student.

\- Every score must be between 0 and 100, inclusive.

\- `pass\_mark` must be between 0 and 100, inclusive.

\- If omitted, `pass\_mark` defaults to 50.

\- A score equal to the pass mark counts as passing.

\- Student names must be unique within the request because they

&#x20; are dictionary keys.



\## Authentication



Send your key in the request header:



```http

X-API-Key: your\_generated\_key

```



In Swagger UI:



1\. Click \*\*Authorize\*\*.

2\. Enter only the key value.

3\. Click \*\*Authorize\*\*, then \*\*Close\*\*.

4\. Expand the POST endpoint.

5\. Click \*\*Try it out\*\*, enter the request body, and click \*\*Execute\*\*.



Do not include `STUDENT\_API\_KEY=` or a `Bearer` prefix in the

authorisation field.



Missing or incorrect keys return `401`.



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



| Code | Meaning |

|------|---------|

| `200` | Request processed successfully |

| `401` | Missing or invalid API key |

| `422` | Request data failed validation |



\## Automated Tests



Run the test suite from the project folder:



```bash

python -m pytest -q

```



Uvicorn does not need to be running. FastAPI's `TestClient`

sends requests directly to the application.



The eight tests cover:



1\. Public endpoint availability.

2\. Missing API key rejection.

3\. Incorrect API key rejection.

4\. Results summary calculations.

5\. Default pass mark and exact-boundary behaviour.

6\. Empty score submission rejection.

7\. Out-of-range score rejection.

8\. Out-of-range pass mark rejection.



Tests use a test-only key set inside the test process.

They do not modify your local `.env` file.



The test suite was verified locally with all eight tests passing

and no warnings.



\## Limitations



\- Scores are processed per request and are not stored in a database.

\- The application uses one shared API key rather than individual accounts.

\- The API does not implement rate limiting or per-user permissions.

\- This project does not train or call an AI model.

\- Uploading the code to GitHub does not deploy the API.

\- Online deployment requires HTTPS and appropriate production configuration.



\## Security Notes



\- Never commit real API keys.

\- Keep `.env` excluded through `.gitignore`.

\- Use placeholders in `.env.example`.

\- Replace any key that has been exposed.

\- Removing a secret from the latest file does not remove it

&#x20; from earlier Git commits.

