# Pcap Testing with AI Regex

This open source tool automates the process of downloading vulnerability reports and PCAPs, generating AI-based regex filters, extracting those filters, and running regex analysis on PCAPs. The workflow is modular, containerized, and designed to provide feedback to LLM trainers for improving model performance on vulnerability analysis and regex generation tasks.

## Overview
- Downloads vulnerability reports and PCAPs for specified TSL IDs
- Uses LLMs to analyze reports and generate regex filters
- Applies generated regex to PCAPs for automated analysis
- Produces reports and dashboards for review and feedback
- Designed to help LLM trainers iteratively improve model accuracy

## Getting Started
1. Clone this repository.
2. Set up your `.env` file with required credentials and configuration (see example below).
3. Build and run the workflow using Docker Compose or the provided shell script.

## .env Example
```
USER_ID=your_user_id
SUBSCRIBER=your_subscriber
PASSWORD=your_password
TSL_ID=<TSLID-1>,<TSLID-2>,<TSLID-3>
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
PORTAL_URL=https://your-portal-url/
```

## Architecture Diagram

Below is a high-level architecture diagram of the workflow:

```
+-------------------+      +-------------------+      +-------------------+      +-------------------+
| Security Portal   | ---> | Agent Service     | ---> | AI Regex Service  | ---> | PCAP Analysis     |
| (Web)             |      | (agent.py)        |      | (automate_regex)  |      | (run_regex_on_pcaps) |
+-------------------+      +-------------------+      +-------------------+      +-------------------+
        |                        |                           |                           |
        |                        v                           v                           v
        |                downloads/<TSL_ID>/         report/ai_report/           report/ai_regex/
        |                        |                           |                           |
        |                        +---------------------------+---------------------------+
        |                                                        |
        |                                                        v
        |                                                pcaps/<TSL_ID>/
        |                                                        |
        |                                                        v
        |                                                Final Reports
```

This diagram shows the flow from downloading vulnerability reports and PCAPs, through AI-based regex generation, to automated PCAP analysis and reporting.

## License
This project is licensed under the MIT License. See the LICENSE file for details.