# Flights ETL Pipeline — Project TODO List (Linear Issues)

This document outlines the detailed, actionable tasks for Phase 1 and Phase 2 of the Flights ETL Pipeline project, derived from the [PRD.md](../docs/PRD.md).

---

## Phase 1 — Project Setup & Infrastructure

### Task 1.1
**Title:** Initialize Git Repository and Project Structure  
**Description:** Set up the foundational repository structure and project management tracking.  
**Implementation Steps:**
1. Initialize a new Git repository.
2. Create a standard directory structure: `src/`, `infra/`, `docs/`, `tests/`, `dags/`.
3. Create a `.gitignore` file (include `.env`, `terraform.tfstate`, `__pycache__`, etc.).
4. Initialize the Linear project with the 10 defined phases.
**Acceptance Criteria:**
- Git repository is initialized with the first commit.
- Directory structure exists.
- `.gitignore` prevents secrets and build artifacts from being tracked.
**Dependencies:** None  
**Labels:** `devops`, `setup`

### Task 1.2
**Title:** Configure Local Development Environment  
**Description:** Install and configure the necessary tools for Python development, Docker orchestration, and Terraform IaC.  
**Implementation Steps:**
1. Install Python 3.9+ and set up a virtual environment (`venv` or `conda`).
2. Install project dependencies: `boto3`, `requests`, `pyspark`, `pytest`, `ruff`.
3. Install Docker Desktop and verify `docker-compose` is available.
4. Install Terraform CLI.
5. Create a `requirements.txt` or `pyproject.toml` file.
**Acceptance Criteria:**
- `python --version`, `docker --version`, and `terraform --version` all return expected versions.
- Virtual environment is active and dependencies are installed.
**Dependencies:** Task 1.1  
**Labels:** `devops`, `setup`

### Task 1.3
**Title:** Configure AWS CLI and IAM Permissions  
**Description:** Set up programmatic access to AWS to allow Terraform and Python scripts to interact with cloud resources.  
**Implementation Steps:**
1. Create an IAM User in the AWS Console with `AdministratorAccess` (for dev purposes) or a scoped policy.
2. Generate Access Key and Secret Key.
3. Run `aws configure` locally to set credentials and default region (e.g., `us-east-1`).
4. Verify access by running `aws s3 ls`.
**Acceptance Criteria:**
- AWS CLI is configured.
- `aws s3 ls` returns successfully (even if empty).
**Dependencies:** Task 1.2  
**Labels:** `infra`, `devops`

### Task 1.4 (Decision Task)
**Title:** Decide on Terraform Backend Storage Strategy  
**Description:** Determine where the Terraform state file (`terraform.tfstate`) will be stored to ensure consistency and prevent state loss.  
**Options:**
- **Option A (Local):** Store state locally (simplest, but risky for collaboration).
- **Option B (S3 + DynamoDB):** Store state in an S3 bucket with DynamoDB for state locking (Best practice).
**Implementation Steps:**
1. Evaluate the options based on the "Learner Subscription" constraints.
2. If Option B is chosen, create a bootstrap script to provision the S3 bucket and DynamoDB table before the main infra.
**Acceptance Criteria:**
- A decision is documented.
- Terraform is initialized (`terraform init`) with the chosen backend configuration.
**Dependencies:** Task 1.3  
**Labels:** `infra`, `decision`

### Task 1.5
**Title:** Provision Core S3 Buckets via Terraform  
**Description:** Use Infrastructure as Code to create the storage layer for the data lakehouse.  
**Implementation Steps:**
1. Create a `main.tf` and `variables.tf` in the `infra/` directory.
2. Define S3 bucket resources for:
   - `flights-bronze-raw`
   - `flights-silver-cleaned`
   - `flights-pipeline-logs`
3. Add tags to resources for cost tracking.
4. Run `terraform plan` and `terraform apply`.
**Acceptance Criteria:**
- Three S3 buckets are visible in the AWS Console.
- Terraform state reflects the created resources.
**Dependencies:** Task 1.4  
**Labels:** `infra`

---

## Phase 2 — Data Ingestion (Bronze)

### Task 2.1
**Title:** Explore Google Flights API and Document Schema  
**Description:** Analyze the RapidAPI Google Flights response to understand the nested JSON structure and identify required fields.  
**Implementation Steps:**
1. Sign up for the Google Flights API on RapidAPI.
2. Use a tool like Postman or a simple Python script to make a sample request.
3. Save the JSON response to `docs/sample_api_response.json`.
4. Create a markdown file `docs/data_dictionary_bronze.md` mapping key fields (e.g., `itineraries`, `legs`, `price`).
**Acceptance Criteria:**
- Sample JSON is saved.
- Data dictionary exists with at least 10 core fields identified.
**Dependencies:** Task 1.2  
**Labels:** `data-ingestion`, `documentation`

### Task 2.2
**Title:** Develop Python Ingestion Script (API to S3)  
**Description:** Create a robust Python script that fetches flight data and uploads it to the Bronze S3 bucket.  
**Implementation Steps:**
1. Create `src/ingestion/extract_flights.py`.
2. Implement the `requests` call to the RapidAPI endpoint.
3. Implement `boto3` logic to upload the raw JSON to S3.
4. Use the partitioning scheme: `s3://flights-bronze-raw/year=YYYY/month=MM/day=DD/flight_data_TIMESTAMP.json`.
**Acceptance Criteria:**
- Script runs locally and successfully uploads a file to S3.
- File path in S3 follows the defined partitioning scheme.
**Dependencies:** Task 1.5, Task 2.1  
**Labels:** `data-ingestion`, `python`

### Task 2.3
**Title:** Implement Error Handling and API Retries  
**Description:** Enhance the ingestion script to handle common network issues and API rate limits.  
**Implementation Steps:**
1. Integrate the `tenacity` library or a custom retry loop for HTTP 429 (Too Many Requests) and 5xx errors.
2. Add logging using the Python `logging` module to track success/failure.
3. Implement a timeout for the API request.
**Acceptance Criteria:**
- Script gracefully handles a simulated 429 error by retrying.
- Logs are visible in the console/log file.
**Dependencies:** Task 2.2  
**Labels:** `data-ingestion`, `python`, `data-quality`

### Task 2.4
**Title:** Secure API Credentials and Configuration  
**Description:** Ensure that API keys and AWS secrets are not hardcoded in the ingestion script.  
**Implementation Steps:**
1. Create a `.env.example` file.
2. Use `python-dotenv` to load credentials from a local `.env` file.
3. Update `extract_flights.py` to use `os.getenv()`.
**Acceptance Criteria:**
- Script runs using environment variables.
- No secrets are present in the source code.
**Dependencies:** Task 2.2  
**Labels:** `devops`, `security`

### Task 2.5 (Milestone)
**Title:** End-to-End Ingestion Verification  
**Description:** Perform a full test of the ingestion process to confirm the Bronze layer is ready for processing.  
**Implementation Steps:**
1. Run the ingestion script for 3 different flight routes.
2. Verify that 3 distinct JSON files exist in the Bronze S3 bucket.
3. Manually inspect one JSON file in S3 to ensure it is not corrupted.
**Acceptance Criteria:**
- Data for multiple routes is present in S3.
- Milestone report (short comment in Linear) confirms the Bronze layer is "Live".
**Dependencies:** Task 2.3, Task 2.4  
**Labels:** `data-ingestion`, `testing`
