import os
import requests

# Load your ClickUp token from environment
CLICKUP_API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
BASE_URL = "https://api.clickup.com/api/v2"
HEADERS = {
    "Authorization": CLICKUP_API_TOKEN
}

def get_teams():
    response = requests.get(f"{BASE_URL}/team", headers=HEADERS)
    return response.json()

def get_spaces(team_id):
    response = requests.get(f"{BASE_URL}/team/{team_id}/space", headers=HEADERS)
    return response.json()

def get_folders(space_id):
    response = requests.get(f"{BASE_URL}/space/{space_id}/folder", headers=HEADERS)
    return response.json()

def get_lists(folder_id):
    response = requests.get(f"{BASE_URL}/folder/{folder_id}/list", headers=HEADERS)
    return response.json()


# def get_tasks_from_list(list_id):
#     response = requests.get(f"{BASE_URL}/list/{list_id}/task", headers=HEADERS)
#     return response.json()

def get_tasks_from_list(list_id, include_subtasks=True, include_closed=False):
    params = {}
    if include_subtasks:
        params["subtasks"] = "true"
    if include_closed:
        params["include_closed"] = "true"
    response = requests.get(f"{BASE_URL}/list/{list_id}/task",
                            headers=HEADERS,
                            params=params)
    response.raise_for_status()
    return response.json()


def get_folderless_lists(space_id):
    response = requests.get(f"{BASE_URL}/space/{space_id}/list", headers=HEADERS)
    return response.json()

if __name__ == "__main__":
    if not CLICKUP_API_TOKEN:
        raise ValueError("Missing CLICKUP_API_TOKEN in environment")

    # Step 1: Get Teams
    teams_data = get_teams()
    team_id = teams_data['teams'][0]['id']
    print(f"[+] Team ID: {team_id}")

    # Step 2: Get Spaces
    spaces_data = get_spaces(team_id)
    
    print(" Total spaces: ", len(spaces_data['spaces']))

    for space in spaces_data['spaces']:
        
        print(space['name'])
        space_id = space['id']
        print(f"[+] Space ID: {space_id}")

        # Step 3: Get Folders
        folders_data = get_folders(space_id)
        folders = folders_data.get("folders", [])
        
        if folders:
            folder_id = folders[0]['id']
            print(f"[+] Folder ID: {folder_id}")
            
            lists_data = get_lists(folder_id)
            list_id = lists_data['lists'][0]['id']
            print(f"[+] List ID (from folder): {list_id}")
        
        else:
            print("[!] No folders found. Trying folderless lists...")
            lists_data = get_folderless_lists(space_id)
            if not lists_data['lists']:
                print("[❌] No lists found in space either.")
                exit()

            list_id = lists_data['lists'][0]['id']
            print(f"[+] List ID (folderless): {list_id}")

        # Step 4: Get Tasks
        # tasks_data = get_tasks_from_list(list_id)
        # tasks = tasks_data.get('tasks', [])
        # print(f"[+] Total tasks found: {len(tasks)}")
        # for task in tasks:
        #     print(f" - {task['name']} | Status: {task['status']['status']}")
        tasks_data = get_tasks_from_list(list_id, include_subtasks=True, include_closed=True)
        tasks = tasks_data.get("tasks", [])
        print(f"[+] Total tasks found: {len(tasks)} (including subtasks)")

        for task in tasks:
            indent = "    " if task.get("parent") else ""
            status = task["status"]["status"]
            print(f"{indent}- {task['name']} | Status: {status}")
            print('*'*20)