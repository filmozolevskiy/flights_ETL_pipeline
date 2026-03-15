#!/usr/bin/env bash
# Verifies AWS CLI is configured and S3 access works.
# Exit 0 = success, non-zero = failure.

set -e

echo "Checking AWS CLI..."
if ! command -v aws &>/dev/null; then
  echo "FAIL: aws CLI not found. Install it first."
  exit 1
fi

echo "Checking credentials..."
if ! aws sts get-caller-identity &>/dev/null; then
  echo "FAIL: No valid credentials. Run 'aws configure' or set AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY."
  exit 1
fi

echo "Checking S3 access..."
if ! aws s3 ls &>/dev/null; then
  echo "FAIL: aws s3 ls failed. Check IAM permissions."
  exit 1
fi

echo "OK: AWS CLI is configured and S3 access works."
exit 0
