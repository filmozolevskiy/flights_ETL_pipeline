# Flights ETL Pipeline — Project TODO List (Linear Issues)

This document outlines the detailed, actionable tasks for Phase 9 of the Flights ETL Pipeline project, derived from the [PRD.md](../docs/PRD.md).

---

## Phase 9 — DevOps & CI/CD

### Task 9.1
**Title:** Create GitHub Actions Workflow for Continuous Integration (CI)  
**Description:** Implement automated linting and unit testing on every Pull Request to maintain code quality.  
**Implementation Steps:**
1. Create `.github/workflows/ci.yml`.
2. Configure the workflow to trigger on `pull_request` to `main`.
3. Add steps to:
   - Set up Python environment.
   - Install dependencies (`ruff`, `pytest`, `boto3`, etc.).
   - Run `ruff check .` for linting.
   - Run `pytest tests/` for unit tests.
**Acceptance Criteria:**
- GitHub Actions workflow is visible in the "Actions" tab.
- PRs are blocked if linting or tests fail.
**Dependencies:** Task 1.2 (Local Dev Env)  
**Labels:** `devops`, `github-actions`

### Task 9.2
**Title:** Develop Unit Tests for Ingestion and Transformation Scripts  
**Description:** Write comprehensive unit tests using `pytest` to ensure the reliability of Python and Spark code.  
**Implementation Steps:**
1. Create `tests/test_ingestion.py` to test API response handling and S3 upload logic (using `moto` for AWS mocking).
2. Create `tests/test_processing.py` to test Spark transformation logic (using a local Spark session).
3. Implement tests for edge cases identified in Phase 3 (e.g., empty API responses, malformed JSON).
**Acceptance Criteria:**
- `pytest` runs locally and passes with >80% code coverage.
- Tests cover both "happy path" and error handling scenarios.
**Dependencies:** Task 2.2, Task 4.2  
**Labels:** `testing`, `python`, `pyspark`

### Task 9.3
**Title:** Create GitHub Actions Workflow for Continuous Deployment (CD)  
**Description:** Automate the synchronization of Airflow DAGs and Terraform infrastructure planning.  
**Implementation Steps:**
1. Create `.github/workflows/cd.yml`.
2. Configure the workflow to trigger on `push` to `main`.
3. Add steps to:
   - Sync files in `dags/` to the Airflow environment (e.g., S3 bucket for MWAA or local volume).
   - Run `terraform plan` to preview infrastructure changes.
   - (Optional) Run `terraform apply` with manual approval for production-like environments.
**Acceptance Criteria:**
- Merging to `main` automatically triggers the CD workflow.
- Airflow DAGs are updated without manual intervention.
**Dependencies:** Task 7.1, Task 9.1  
**Labels:** `devops`, `github-actions`, `infra`

### Task 9.4
**Title:** Configure Secrets Management for CI/CD  
**Description:** Securely store and inject API keys and AWS credentials into the GitHub Actions environment.  
**Implementation Steps:**
1. Add `BRIGHT_DATA_API_KEY`, `AWS_ACCESS_KEY_ID`, and `AWS_SECRET_ACCESS_KEY` to GitHub Repository Secrets.
2. Update CI/CD YAML files to use these secrets as environment variables.
3. Verify that secrets are masked in the workflow logs.
**Acceptance Criteria:**
- Workflows run successfully using GitHub Secrets.
- No sensitive information is exposed in logs or source code.
**Dependencies:** Task 2.4, Task 9.1  
**Labels:** `devops`, `security`

### Task 9.5 (Milestone)
**Title:** Full CI/CD Pipeline Verification  
**Description:** Perform an end-to-end test of the automated workflow from code change to deployment.  
**Implementation Steps:**
1. Create a feature branch and make a small change to a transformation script.
2. Open a Pull Request and verify the CI workflow passes.
3. Merge the PR to `main` and verify the CD workflow updates the environment.
4. Confirm the updated pipeline runs successfully in Airflow.
**Acceptance Criteria:**
- Both CI and CD workflows complete successfully.
- Milestone report confirms the DevOps automation is "Live".
**Dependencies:** Task 9.3, Task 9.4  
**Labels:** `devops`, `testing`
