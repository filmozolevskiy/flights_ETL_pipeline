# Project Requirements Document: Flights Data Engineering Pipeline

## 1. Project Overview

### 1.1 Introduction
This project is a comprehensive, end-to-end data engineering pipeline designed to ingest, process, and analyze flight search data. It simulates a real-world enterprise data platform using a modern lakehouse architecture. The system ingests data from the Google Flights API, processes it using Apache Spark on AWS EMR, and models it for analytics in Snowflake.

### 1.2 Learning Objectives
The primary goal of this project is to demonstrate competency in the following key areas:
-   **Cloud Infrastructure:** Provisioning AWS resources using Infrastructure as Code (Terraform).
-   **Distributed Processing:** utilizing Apache Spark for large-scale data transformation.
-   **Data Lakehouse Architecture:** Implementing the Bronze/Silver/Gold data layering pattern.
-   **Data Warehousing:** Loading and modeling data in Snowflake for analytical queries.
-   **Orchestration:** Managing complex dependencies and workflows with Apache Airflow.
-   **Data Quality:** Implementing automated validation checks (Great Expectations or similar).
-   **DevOps:** Building CI/CD pipelines with GitHub Actions.

### 1.3 Scope
The project focuses on the **batch processing** of flight data.
-   **In Scope:**
    -   Ingestion of flight search results (RapidAPI).
    -   Raw data storage in AWS S3 (Bronze).
    -   Data cleaning and transformation using Spark (Silver).
    -   Dimensional modeling and loading into Snowflake (Gold).
    -   Orchestration via Airflow.
    -   Infrastructure provisioning via Terraform.
    -   CI/CD for code deployment.
-   **Out of Scope:**
    -   Real-time streaming (this is a batch pipeline).
    -   Front-end application development (dashboarding tools like Streamlit or Tableau can be connected later).
    -   Predictive machine learning models (though the data will be ML-ready).

---

## 2. Architecture

### 2.1 High-Level Architecture
The system follows a **Modern Lakehouse Architecture**, leveraging the scalability of a data lake (S3) with the performance and structure of a data warehouse (Snowflake).

**Data Flow:**
1.  **Source:** RapidAPI Google Flights API (JSON response).
2.  **Ingestion:** Python scripts triggered by Airflow fetch data and land it in the **Bronze Layer** (S3).
3.  **Processing:** Apache Spark jobs (running on AWS EMR) read raw data, clean/normalize it, and write to the **Silver Layer** (S3 - Parquet/Delta).
4.  **Modeling:** Spark jobs transform data into a dimensional model and load it into the **Gold Layer** (Snowflake).
5.  **Analytics:** BI tools or SQL queries consume data from Snowflake.

### 2.2 Technology Stack
| Component          | Technology                  | Justification                                                                          | 
| :---               | :---                        | :---                                                                                   |
| **Data Source**    | RapidAPI Google Flights API | Provides realistic, nested JSON data suitable for complex transformation logic.        |
| **Infrastructure** | Terraform                   | Industry-standard IaC tool for reproducible and manageable cloud infrastructure.       |
| **Data Lake**      | Amazon S3                   | Cost-effective, durable storage for raw and processed data.                            |
| **Compute**        | AWS EMR (Spark)             | Managed Hadoop/Spark cluster for distributed processing, a standard enterprise choice. |
| **Orchestration**  | Apache Airflow              | The leading open-source workflow management platform.                                  |
| **Data Warehouse** | Snowflake                   | Separation of storage and compute, excellent concurrency, and ease of use.             |
| **CI/CD**          | GitHub Actions              | Integrated with the repository, free for public repos, and widely used.                |
| **Language**       | Python / SQL                | The standard languages for modern data engineering.                                    |

### 2.3 Layered Data Architecture
-   **Bronze Layer (Raw):**
    -   **Format:** JSON (as received from API).
    -   **Purpose:** Immutable record of history. Allows for reprocessing if logic changes.
    -   **Partitioning:** By ingestion date (`/year=YYYY/month=MM/day=DD/`).
-   **Silver Layer (Cleaned):**
    -   **Format:** Delta Lake.
    -   **Purpose:** Deduplicated, cleaned, type-cast data. Nested structures are flattened where appropriate.
    -   **Partitioning:** Optimized for downstream query patterns (e.g., by flight date).
-   **Gold Layer (Curated):**
    -   **Format:** Snowflake Tables.
    -   **Purpose:** Business-level models ready for reporting.

---

## 3. Infrastructure & DevOps

### 3.1 Infrastructure as Code (IaC)
All AWS resources (S3 buckets, IAM roles, EMR clusters, etc.) will be provisioned using **Terraform**. This ensures the environment is reproducible and can be torn down to save costs.
*   **State Management:** Terraform state should be stored remotely (e.g., in an S3 bucket) to allow for collaboration and consistency.

### 3.2 CI/CD Strategy
**GitHub Actions** will be used for Continuous Integration and Continuous Deployment.
-   **CI:** On every Pull Request, run unit tests (pytest) and linting (ruff).
-   **CD:** On merge to `main`, update Airflow DAGs and deploy infrastructure changes (Terraform apply) if applicable.

### 3.3 Orchestration Deployment Trade-offs
*   **Decision:** We will start with **Local Airflow (Docker Compose)** for development and testing to minimize costs.
*   **Future Path:** For a production-grade portfolio demonstration, we can explore deploying Airflow on a small EC2 instance or using MWAA (Managed Workflows for Apache Airflow) if budget permits.
*   **Reasoning:** Running Airflow 24/7 on the cloud can be expensive. A local setup allows us to develop DAGs and trigger cloud resources (EMR, Snowflake) remotely without incurring orchestration costs.

---

## 4. Development Phases & Linear Task Breakdown

This project is divided into 10 phases. Each phase corresponds to a set of Linear issues.

### Phase 1: Project Setup & Infrastructure
**Goal:** Initialize the repository and provision core AWS infrastructure.
*   **Linear Tasks:**
    1.  Initialize Git Repository & Linear Project.
    2.  Set up local development environment (Python, Docker, Terraform).
    3.  Create Terraform scripts for S3 Buckets (Bronze, Silver, Logs).
    4.  Configure AWS CLI and IAM permissions.

### Phase 2: Data Ingestion (Bronze)
**Goal:** Successfully fetch data from the API and store it in S3.
*   **Linear Tasks:**
    1.  Explore Google Flights API (RapidAPI) and document response structure.
    2.  Develop Python ingestion script (fetch data -> upload to S3 Bronze).
    3.  Implement basic error handling and retries for API calls.
    4.  **Milestone:** Run script locally; verify JSON files appear in S3 Bronze bucket.

### Phase 3: Data Exploration
**Goal:** Understand the data to inform schema design.
*   **Linear Tasks:**
    1.  Use AWS Athena or a local Jupyter Notebook to query Bronze data in S3.
    2.  Identify key fields (price, carrier, duration, stops) and nested arrays.
    3.  Document data quality issues (nulls, duplicates, unexpected formats).

### Phase 4: Data Processing (Silver)
**Goal:** Transform raw JSON into clean, structured Parquet data using Spark.
*   **Linear Tasks:**
    1.  Provision AWS EMR Cluster via Terraform (or configure EMR Serverless).
    2.  Develop PySpark job: Read JSON from Bronze, flatten schema, cast types.
    3.  Implement data cleaning logic (handle missing values, deduplicate).
    4.  Write output to S3 Silver bucket in Parquet format.

### Phase 5: Data Modeling (Gold)
**Goal:** Design the analytical data model.
*   **Linear Tasks:**
    1.  Design Star Schema (Fact Table: `fact_flights`, Dim Tables: `dim_carrier`, `dim_airport`, `dim_date`).
    2.  Create schema diagrams (Entity-Relationship Diagram).
    3.  *Note: Do not implement the load yet, just design the model.*

### Phase 6: Data Warehouse Integration
**Goal:** Load transformed data into Snowflake.
*   **Linear Tasks:**
    1.  Set up Snowflake account (Trial) and create database/schema.
    2.  Develop Spark-to-Snowflake write logic (using Snowflake Connector for Spark).
    3.  Implement "Upsert" or "Append" logic for the Fact table.

### Phase 7: Orchestration
**Goal:** Automate the entire pipeline with Airflow.
*   **Linear Tasks:**
    1.  Set up Airflow locally using Docker Compose.
    2.  Create DAG: `Ingest -> Process (EMR) -> Load (Snowflake)`.
    3.  Configure Airflow connections (AWS, Snowflake, RapidAPI).
    4.  Test end-to-end execution.

### Phase 8: Data Quality
**Goal:** Ensure data reliability.
*   **Linear Tasks:**
    1.  Define data quality expectations (e.g., "price must be > 0", "flight_date must not be null").
    2.  Integrate Data Quality checks into the pipeline (e.g., using Great Expectations or simple SQL checks in Airflow).
    3.  Configure alerts for failed checks (e.g., Email).

### Phase 9: DevOps & CI/CD
**Goal:** Automate testing and deployment.
*   **Linear Tasks:**
    1.  Create GitHub Actions workflow for CI (Linting, Unit Tests).
    2.  Create GitHub Actions workflow for CD (Sync DAGs to Airflow, Plan Terraform).
    3.  Add unit tests for Python ingestion scripts and Spark transformations.

### Phase 10: Portfolio Preparation
**Goal:** Polish the project for presentation.
*   **Linear Tasks:**
    1.  Create final Architecture Diagram (Draw.io and Mermaid).
    2.  Write `README.md` with setup instructions and project summary.
    3.  Capture screenshots of Airflow DAGs, Snowflake tables, and EMR steps.
    4.  Write a blog post or summary article explaining the "Why" behind architectural choices.

---

## 5. Acceptance Criteria

### General
-   All code must be version controlled in Git.
-   No secrets (API keys, passwords) committed to the repo; use `.env` files or Secrets Managers.

### Phase Specific
-   **Ingestion:** Script runs successfully, handles API rate limits, and data lands in S3 partitioned by date.
-   **Processing:** Spark job runs on EMR, reads from Bronze, and writes valid Parquet to Silver.
-   **Warehouse:** Data in Snowflake matches the designed Star Schema and can be queried via SQL.
-   **Orchestration:** Airflow DAG runs green from start to finish without manual intervention.
-   **IaC:** `terraform apply` successfully builds the infrastructure, and `terraform destroy` tears it down.

---

## 6. Cost Management (Learner Subscription)
To stay within the learner subscription limits and avoid unexpected costs:
-   **EMR:** Use "Transient Clusters" (create cluster -> run job -> terminate cluster) managed by Airflow, rather than keeping a cluster running 24/7.
-   **Snowflake:** Utilize the free trial credits efficiently. Suspend warehouses immediately after use (Auto-suspend = 1 minute).
-   **S3:** Implement Lifecycle Policies to delete raw data after X days if storage costs become a concern (though text data is generally cheap).
-   **NAT Gateway:** Be cautious with AWS VPC NAT Gateways which can be expensive; ensure EMR is deployed in a cost-effective network topology (e.g., public subnets for learning purposes, though private is best practice).
