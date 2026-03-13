# Parking Permit Bot

An event-driven serverless automation bot that registers visitor parking permits via SMS. Built on AWS Lambda with a containerized Python runtime, the bot listens for inbound Twilio SMS messages, looks up the caller's vehicle profile from DynamoDB, and uses a headless Playwright browser to complete and submit the parking permit form automatically.

## How It Works

1. A registered visitor texts the bot's Twilio number with their name
2. The Lambda function receives the webhook, looks up the visitor's vehicle profile from DynamoDB
3. A headless Chromium browser (via Playwright) fills out and submits the parking permit form
4. A screenshot of the confirmation is uploaded to S3 and sent back to the visitor via SMS

## Architecture

```
SMS (Twilio) → Lambda Function URL → AppRunner → Playwright → Parking Portal
                                          ↕               ↕
                                       DynamoDB          S3
```

**Infrastructure provisioned with Terraform:**
- AWS Lambda (container image via ECR)
- Lambda Function URL (public HTTPS endpoint for Twilio webhook)
- DynamoDB — two tables: visitor vehicle profiles and active permit records
- S3 — confirmation screenshot storage
- IAM roles and least-privilege policies for each AWS service
- Secrets Manager — Twilio credentials stored and fetched at runtime
- Remote Terraform state in S3 with DynamoDB state locking

**CI/CD via GitHub Actions** — on every push to `main`:
1. `terraform apply` provisions any infrastructure changes
2. Docker image is built and pushed to ECR
3. Lambda is updated to the new image via `aws lambda update-function-code`

## Project Structure

```
parking-permit-bot/
├── app/
│   ├── handler.py                  # Lambda entrypoint
│   ├── app_runner.py               # Orchestration logic
│   ├── parking_registration.py     # Playwright form automation
│   └── utils.py
├── config/
│   └── profiles_config.py          # DynamoDB profile lookup
├── scripts/
│   └── seed_profiles.py            # One-time DynamoDB seed script
├── tf/
│   ├── main.tf                     # S3 backend + provider config
│   ├── lambda.tf                   # Lambda function + ECR repository
│   ├── dynamodb.tf                 # DynamoDB tables
│   ├── iam.tf                      # IAM roles and policies
│   ├── secrets.tf                  # Secrets Manager resources
│   └── variables.tf
├── Dockerfile
└── requirements.txt
```

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.12 |
| Compute | AWS Lambda (container image) |
| Container Registry | Amazon ECR |
| Browser Automation | Playwright + Chromium |
| Messaging | Twilio SMS |
| Database | Amazon DynamoDB |
| Storage | Amazon S3 |
| Secrets | AWS Secrets Manager |
| Infrastructure | Terraform |
| CI/CD | GitHub Actions |

## Deployment

Infrastructure and code are deployed automatically on push to `main`. To deploy manually:

```bash
# Provision infrastructure
cd tf && terraform init && terraform apply

# Seed visitor profiles (first time only)
python -m scripts.seed_profiles

# Set Twilio credentials in Secrets Manager (first time only)
aws secretsmanager put-secret-value \
  --secret-id parking-permit-bot/twilio \
  --secret-string '{"TWILIO_ACCOUNT_SID":"...","TWILIO_AUTH_TOKEN":"..."}'
```

## Notes

The Playwright automation is configured specifically for [parkingpermitsofamerica.com](https://www.parkingpermitsofamerica.com). To adapt it for a different permit portal, modify the `run_flow` method in `app/parking_registration.py`.

## Contact

Kuzie Chambers — kuzie.chambers@gmail.com
