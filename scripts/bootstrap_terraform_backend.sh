#!/usr/bin/env bash
# Bootstrap Terraform backend: S3 bucket + DynamoDB table for state storage and locking.
# Run once before first 'terraform init'. Requires AWS CLI configured.
#
# Region: TF_VAR_aws_region env var (preferred) > positional arg > us-east-1
# Usage: ./scripts/bootstrap_terraform_backend.sh [region]

set -e

REGION="${TF_VAR_aws_region:-${1:-us-east-1}}"
BUCKET_PREFIX="flights-terraform-state"
DYNAMODB_TABLE="terraform-state-lock"

echo "Bootstrap Terraform backend (region: $REGION)..."

if ! command -v aws &>/dev/null; then
  echo "FAIL: aws CLI not found."
  exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET_NAME="${BUCKET_PREFIX}-${ACCOUNT_ID}"

echo "Account ID: $ACCOUNT_ID"
echo "S3 bucket: $BUCKET_NAME"
echo "DynamoDB table: $DYNAMODB_TABLE"

if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
  echo "S3 bucket $BUCKET_NAME already exists."
else
  echo "Creating S3 bucket $BUCKET_NAME..."
  if [ "$REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$BUCKET_NAME"
  else
    aws s3api create-bucket \
      --bucket "$BUCKET_NAME" \
      --create-bucket-configuration "LocationConstraint=$REGION"
  fi
  aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled
  echo "S3 bucket created with versioning enabled."
fi

if aws dynamodb describe-table --table-name "$DYNAMODB_TABLE" --region "$REGION" 2>/dev/null; then
  echo "DynamoDB table $DYNAMODB_TABLE already exists."
else
  echo "Creating DynamoDB table $DYNAMODB_TABLE..."
  aws dynamodb create-table \
    --table-name "$DYNAMODB_TABLE" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region "$REGION"
  echo "Waiting for table to be active..."
  aws dynamodb wait table-exists --table-name "$DYNAMODB_TABLE" --region "$REGION"
  echo "DynamoDB table created."
fi

BACKEND_CONFIG="terraform/backend.hcl"
mkdir -p terraform
cat > "$BACKEND_CONFIG" << EOF
bucket         = "$BUCKET_NAME"
key            = "terraform.tfstate"
region         = "$REGION"
dynamodb_table = "$DYNAMODB_TABLE"
EOF
echo ""
echo "Bootstrap complete. Backend config written to $BACKEND_CONFIG"
echo "Run: cd terraform && terraform init -backend-config=backend.hcl"
