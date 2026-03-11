# 🅿️  Parking Permit Bot
+ [Python](https://www.python.org/downloads/release/python-31213/)
+ [AWS Lambda](https://docs.aws.amazon.com/lambda/)
+ [Docker](https://docs.docker.com/get-started/)
+ [Playwright](https://playwright.dev/python/docs/intro)
+ [Twilio](https://www.twilio.com/docs)
+ [ECR](https://docs.aws.amazon.com/ecr/)

An AWS Lambda-powered automation bot that listens for inbound Twilio SMS messages and uses Playwright to automatically fill out and submit parking permit applications on behalf of registered visitor profiles.

## Overview

Parking Permit Bot is a serverless, event-driven automation system built entirely in Python. 
When a registered visitor texts your Twilio number with their first name, 
the Lambda function looks up their pre-configured profile and uses a headless Playwright browser to complete 
the parking permit form on the target website.

The project is designed with a clean OOP architecture, making it easy to add new visitor profiles, 
swap out vehicle configurations, or extend to other permit portals with minimal changes.

**NOTE: Out of the box, this bot will only work with the www.parkingpermitsofamerica.com parking website. 
It's specifically configured to the web elements on that page. The `run_flow` function in the `parking_registration.py` 
module is where you would modify the web elements if you want to use it with a different website.**

## Project Structure
```
parking-permit-bot/
├── app/
│   ├── __init__.py
│   ├── handler.py          # Lambda entrypoint
│   ├── bot.py              # PermitFormBot class (Playwright logic)
│   ├── profiles.py         # VisitorProfile & VehicleProfile classes
│   ├── profile_manager.py  # ProfileManager — loads & resolves profiles
│   └── config.py           # Config loader
├── config/
│   └── profiles.yaml       # Your visitor & vehicle configurations
├── Dockerfile
├── requirements.txt
├── deploy.sh               # Build, push, and deploy script
└── README.md
```


## Installation

Instructions on how to deploy the Lambda using the AWS CLI with Docker.

1.  Clone the repository

    `git clone https://github.com`.


2.  Install required packages
    
    `pip install -r requirements.txt`


3. Configure any necessary environment variables.


4. First, run these commands to configure the AWS CLI with your credentials if not already configured.

    `AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)`           
    `AWS_REGION=$(aws configure get region)`


5. Then you'll need to authenticate Docker with AWS ECR using a pipe of two commands:

    `aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com`


6. Before creating a new lambda, create the container repository first:

    `aws ecr create-repository --repository-name parking-permit-bot-ecr`


7. Before running this step, make sure you are in the directory that hosts all the project files. 
Then build a Docker image using BuildKit's extended build capabilities, we need a Linux platform image.

    `docker buildx build --platform linux/amd64 -t parking-permit-bot:latest --load .`


8. Create an alias/label for your locally built image, pointing it at your ECR registry address.

    `docker tag parking-permit-bot:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/parking-permit-bot:latest`

9. Upload the image to the ECR using the address that you just tagged.

    `docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/parking-permit-bot:latest`

### Update the Lambda Code
After you've deployed your AWS Lambda and your container image, and you've made some updates to the code. 
You can rerun steps 7-9 to rebuild your image. 

Then run this command to update the Lambda to use the new image.
```
aws lambda update-function-code \
  --function-name parking-permit-bot-docker \
  --image-uri $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/parking-permit-bot:latest
```

## Usage

Provide examples of how to use the project. This section should show the value of your work quickly.

*   To run the program: `npm start`.
*   Access the application by visiting `http://localhost:3000` in your browser.

## Contact

Provide contact information for the project maintainer or team.

*   Author Name – Kuzie Chambers – kuzie.chambers@gmail.com
*   Project Link: [https://github.com](https://github.com)

