# AWS CLI and IAM Setup Guide

This guide walks you through configuring programmatic access to AWS for the Flights ETL Pipeline. Terraform and Python scripts will use these credentials to provision infrastructure and interact with S3.

**Prerequisites:** AWS CLI installed (see Task 1.2).

---

## 1. Create an IAM User

1. Sign in to the [AWS Console](https://console.aws.amazon.com/).
2. Open **IAM** → **Users** → **Create user**.
3. Enter a user name (e.g., `flights-etl-dev`).
4. Click **Next**.

---

## 2. Attach Permissions

**For development / learning:** Attach `AdministratorAccess` to simplify setup.

**For production:** Use a scoped policy that grants only what the pipeline needs (S3, EMR, etc.). Example minimal policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "iam:PassRole",
        "emr:*",
        "ec2:Describe*"
      ],
      "Resource": "*"
    }
  ]
}
```

5. Select the policy and click **Next** → **Create user**.

---

## 3. Generate Access Keys

1. Open the user you created → **Security credentials** tab.
2. Under **Access keys**, click **Create access key**.
3. Choose **Command Line Interface (CLI)** → **Next**.
4. (Optional) Add a description tag → **Create access key**.
5. **Copy the Access Key ID and Secret Access Key.** The secret is shown only once.

---

## 4. Configure AWS CLI Locally

Run:

```bash
aws configure
```

You will be prompted for:

| Prompt           | Example value   | Notes                          |
|------------------|-----------------|--------------------------------|
| AWS Access Key ID| `AKIA...`       | From step 3                    |
| AWS Secret Key   | `...`           | From step 3                    |
| Default region   | `us-east-1`     | Matches common AWS defaults    |
| Default output   | `json`          | Optional; `json` is typical    |

Credentials are stored in `~/.aws/credentials` (never commit this file). The AWS CLI does **not** read from `.env`; use `aws configure` for CLI access.

**Using `.env` for Python scripts:** If you store credentials in `.env` for boto3/Python, ensure `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_DEFAULT_REGION` are exported before running scripts, or load them with `python-dotenv`. The AWS CLI itself still needs `aws configure` or these env vars set in your shell.

---

## 5. Verify Access

Run:

```bash
aws s3 ls
```

- **Success:** You see a list of S3 buckets, **or no output at all** (empty account = no buckets). Check with `echo $?` — exit code `0` means success.
- **Failure:** You see an error message (e.g. `Unable to locate credentials`, `Access Denied`). Check that the access key and secret are correct and that the IAM user has S3 permissions.

For a more thorough check, run the project verification script:

```bash
./scripts/verify_aws_setup.sh
```

---

## Troubleshooting

| Issue                         | Possible cause                | Fix                                     |
|-------------------------------|-------------------------------|-----------------------------------------|
| `Unable to locate credentials`| AWS CLI not configured        | Run `aws configure`                     |
| `Access Denied` / 403         | IAM user lacks S3 permissions | Attach S3 policy to the user            |
| `InvalidClientTokenId`        | Wrong access key or secret    | Regenerate keys and run `aws configure` |
