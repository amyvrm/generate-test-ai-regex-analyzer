# TIS Portal TSL Resource Downloader

This agent automates downloading TSL resources (Vulnerability Report PDF, Baseline PCAP, Attack PCAP) from the Trend Micro TIS portal.

## What is an AI Agent?

An **AI Agent** is a software program that can perceive its environment, make decisions, and take actions to achieve specific goals—often using automation, reasoning, or learning techniques. In this project, the agent automates web interactions to reliably download files from the TIS portal.

## Why is this an AI Agent solution?

- **Perception:** The agent observes the web portal's structure and content using Selenium.
- **Decision-making:** It determines how to log in, search, and find/download the correct resources based on the current page state.
- **Action:** It performs actions (filling forms, clicking buttons, downloading files) to achieve its goal.
- **Robustness:** Uses self-healing selectors and adaptive waits to handle minor changes in the portal UI.
- **Autonomy:** Runs unattended, requiring only user credentials and TSL ID as input.
- **Extensibility:** The code is modular and ready for future enhancements (e.g., LLM integration, cloud execution).

## Features
- Logs in to https://portal.com/ using your credentials
- Searches for a given TSL ID
- Downloads the required files from the TSL report page
- Uses robust Selenium best practices and self-healing selectors
- CLI usability for easy automation and scripting

## Prerequisites
- Python 3.8+
- Google Chrome browser (latest) for local execution or Chromium (used in Docker setup)
- ChromeDriver (auto-managed by webdriver-manager)
- macOS (tested)

## Setup
1. Clone or download this repository.
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage
Run the agent from the terminal:

```sh
python agent.py --user-id <UserID> --subscriber <Subscriber> --password <Password> --tsl-id <TSL_ID> [--download-dir <dir>]
```

- `--user-id`: Your portal UserID
- `--subscriber`: Your portal Subscriber
- `--password`: Your portal Password
- `--tsl-id`: The TSL ID to search for
- `--download-dir`: (Optional) Directory to save files (default: `downloads`)

Example:
```sh
python agent.py --user-id myuser --subscriber mysub --password mypass --tsl-id TSL-12345
```

## Docker Usage

You can run this agent in a Docker container for a consistent environment:

1. Build the Docker image:
   ```sh
   docker build -t tsl-downloader .
   ```
2. Run the agent (replace arguments as needed):
   ```sh
   docker run --rm -it \
     -v $(pwd)/downloads:/app/downloads \
     tsl-downloader \
     --user-id <UserID> --subscriber <Subscriber> --password <Password> --tsl-id <TSL_ID> [--download-dir downloads]
   ```

- The `downloads` directory will contain your files.
- All dependencies, Chromium, and ChromeDriver are pre-installed in the container.

## Dockerfile Notes

This project uses a Dockerfile that installs **Chromium** and **ChromiumDriver** (not Google Chrome) for browser automation. This ensures compatibility and ease of use in most Linux-based containers.

```
FROM python:3.12-bookworm

# Install Chromium and ChromiumDriver
RUN apt-get update && \
    apt-get install -y chromium chromium-driver fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "agent.py"]
```

- The agent runs in a headless Chromium browser environment.
- No Chrome or ChromeDriver installation is required.
- This setup is suitable for most CI/CD and cloud environments.

## Notes
- Downloads will appear in the specified directory.
- If a resource is not found, a message will be printed.
- For security, consider using environment variables or a secrets manager for credentials.

## Troubleshooting
- Ensure Chrome is installed and up to date.
- If ChromeDriver issues occur, update `webdriver-manager` or Chrome.
- If portal layout changes, update the selectors in `agent.py` as needed.

---

© 2025 Amit Verma
