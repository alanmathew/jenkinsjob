import os
import re
import logging
import requests
from requests.auth import HTTPBasicAuth
from concurrent.futures import ThreadPoolExecutor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import IsolationForest

# Jenkins server details
JENKINS_URL = "http://your-jenkins-server"
USERNAME = "your-username"
API_TOKEN = "your-api-token"

# Jobs and number of builds to fetch logs for
JOBS = ["job1", "job2"]
NUM_BUILDS = 2

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def clean_log(log):
    """
    Cleans the log by removing timestamps, repetitive lines, and irrelevant information.
    """
    log = re.sub(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", "", log)  # Remove timestamps
    log = re.sub(r"\b(INFO|DEBUG|TRACE|WARNING|ERROR)\b", "", log, flags=re.IGNORECASE)  # Remove log levels
    log = re.sub(r"\s+", " ", log).strip()  # Remove extra whitespace
    return log


def save_log_to_file(job_name, build_number, log_content):
    """
    Saves the log content to a file for future reference.
    """
    os.makedirs(f"logs/{job_name}", exist_ok=True)
    file_path = f"logs/{job_name}/build_{build_number}.log"
    with open(file_path, "w") as log_file:
        log_file.write(log_content)
    logging.info(f"Log saved to {file_path}")


def fetch_url(url):
    """
    Fetches a URL with retry logic for network-related issues.
    """
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, API_TOKEN))
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch URL {url}: {e}")
        raise


def get_build_logs(job_name, num_builds):
    """
    Fetches logs for the last `num_builds` builds of a Jenkins job.
    """
    logs = []
    try:
        # Get the job details
        job_url = f"{JENKINS_URL}/job/{job_name}/api/json"
        response = fetch_url(job_url)
        job_data = response.json()

        # Get the last `num_builds` builds
        builds = job_data.get("builds", [])[:num_builds]
        for build in builds:
            build_url = build["url"]
            log_url = f"{build_url}consoleText"
            log_response = fetch_url(log_url)
            raw_log = log_response.text
            cleaned_log = clean_log(raw_log)  # Clean the log
            logs.append({"build": build["number"], "log": cleaned_log})
            save_log_to_file(job_name, build["number"], cleaned_log)  # Save log to file
    except Exception as e:
        logging.error(f"Error fetching logs for job {job_name}: {e}")
    return logs


def detect_anomalies(logs):
    """
    Detects anomalies in the logs using Isolation Forest.
    """
    log_texts = [log["log"] for log in logs]

    # Convert logs to numerical features using TF-IDF
    vectorizer = TfidfVectorizer(max_features=1000)
    log_features = vectorizer.fit_transform(log_texts)

    # Train Isolation Forest for anomaly detection
    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(log_features)

    # Predict anomalies (-1 = anomaly, 1 = normal)
    predictions = model.predict(log_features)

    # Annotate logs with anomaly status
    for i, log in enumerate(logs):
        log["anomaly"] = "Anomaly" if predictions[i] == -1 else "Normal"

    return logs


def process_job_logs(job_name, num_builds):
    """
    Fetches, processes, and analyzes logs for a specific Jenkins job.
    """
    logging.info(f"Fetching logs for job: {job_name}")
    logs = get_build_logs(job_name, num_builds)
    logs = detect_anomalies(logs)  # Detect anomalies
    for log in logs:
        logging.info(f"Build #{log['build']} log:")
        logging.info(log["log"])
        logging.info(f"Anomaly Status: {log['anomaly']}")
        logging.info("-" * 80)


def main():
    """
    Main function to process logs for all jobs in parallel.
    """
    with ThreadPoolExecutor() as executor:
        executor.map(lambda job: process_job_logs(job, NUM_BUILDS), JOBS)


if __name__ == "__main__":
    main()