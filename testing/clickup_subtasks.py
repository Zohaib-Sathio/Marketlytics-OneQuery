import os
import requests

CLICKUP_API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
HEADERS = {"Authorization": CLICKUP_API_TOKEN}
BASE_URL = "https://api.clickup.com/api/v2"

def get_subtasks(task_id):
    url = f"{BASE_URL}/task/{task_id}/subtask"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()  # Raise error if something went wrong
    return response.json()

if __name__ == "__main__":
    task_id = "86etxfehj"
    subtasks_data = get_subtasks(task_id)
    subtasks = subtasks_data.get('tasks', [])

    if subtasks:
        print(f"[+] Subtasks for task '{task_id}':")
        for subtask in subtasks:
            name = subtask.get('name', 'Unnamed')
            status = subtask.get('status', {}).get('status', 'Unknown')
            print(f"   - 🔹 {name} | Status: {status}")
    else:
        print(f"[!] No subtasks found for task '{task_id}'")
