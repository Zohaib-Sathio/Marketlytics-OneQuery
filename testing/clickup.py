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

def get_user_info():
    response = requests.get(f"{BASE_URL}/user", headers=HEADERS)
    response.raise_for_status()
    return response.json()['user']

def get_my_space_ids(team_id):
    spaces = get_spaces(team_id)['spaces']
    return set(space['id'] for space in spaces)

def get_all_team_tasks(team_id, include_subtasks=True, include_closed=True):
    tasks = []
    page = 0
    while True:
        params = {
            "page": page,
            "subtasks": str(include_subtasks).lower(),
            "include_closed": str(include_closed).lower()
        }

        response = requests.get(f"{BASE_URL}/team/{team_id}/task", headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        if not data.get("tasks"):
            break
        tasks.extend(data['tasks'])
        page += 1

    return tasks

def get_shared_with_me_tasks(team_id):
    user = get_user_info()
    my_id = user['id']
    my_spaces = get_my_space_ids(team_id)
    
    all_tasks = get_all_team_tasks(team_id, include_subtasks=True, include_closed=True)

    shared_tasks = []
    for task in all_tasks:
        creator_id = task.get("creator", {}).get("id")
        assignees = [a['id'] for a in task.get("assignees", [])]
        space_id = task.get("space", {}).get("id")  # can be missing sometimes

        if (creator_id != my_id and
            my_id not in assignees and
            (not space_id or space_id not in my_spaces)):
            shared_tasks.append(task)

    return shared_tasks


def get_task_by_id(task_id):
    response = requests.get(f"{BASE_URL}/task/{task_id}", headers=HEADERS)
    response.raise_for_status()
    return response.json()

from collections import defaultdict

if __name__ == "__main__":
    if not CLICKUP_API_TOKEN:
        raise ValueError("Missing CLICKUP_API_TOKEN in environment")

    # Step 1: Get Teams
    team_id = get_teams()['teams'][0]['id']
    print(f"[+] Team ID: {team_id}")

    # Step 2: Get shared tasks
    shared_tasks = get_shared_with_me_tasks(team_id)
    print(f"[+] Total shared-with-me tasks: {len(shared_tasks)}")

    # Step 3: Organize tasks by project name
    parent_name_cache = {}
    project_map = defaultdict(list)

    for task in shared_tasks:
        status = task["status"]["status"]
        parent_id = task.get("parent")
        task_name = task["name"]

        if parent_id:
            if parent_id in parent_name_cache:
                project_name = parent_name_cache[parent_id]
            else:
                try:
                    parent_task = get_task_by_id(parent_id)
                    project_name = parent_task.get("name", "[Unnamed Parent Task]")
                    parent_name_cache[parent_id] = project_name
                except requests.HTTPError:
                    project_name = "[Failed to fetch parent]"
                    parent_name_cache[parent_id] = project_name
        else:
            # This is a parent task, becomes its own project
            project_name = task_name

        if project_name == task_name and project_name in project_map:
            continue
        project_map[project_name].append({
            "name": task_name,
            "status": status,
            "id": task["id"]
        })

    # Step 4: Print grouped output
    for project, tasks in project_map.items():
        print(f"\n Project: {project}")
        print("-" * (10 + len(project)))
        for t in tasks:
            print(f"  🔹 {t['name']} | Status: {t['status']}")
        print("*" * 40)
    import json
    from pathlib import Path

    # Save directory
    output_path = Path("config/clickup_projects.json")

    # Convert defaultdict to normal dict
    serializable_project_map = {k: v for k, v in project_map.items()}

    # Write to JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serializable_project_map, f, ensure_ascii=False, indent=4)

    print(f"[✓] Project task map saved to: {output_path.resolve()}")











    # for task in shared_tasks:
    #     print(task)
    #     print(f" - {task['name']} | Status: {task['status']['status']}")

    # print(get_all_team_tasks(team_id))
    
    # # Step 2: Get Spaces
    # spaces_data = get_spaces(team_id)
    # # print(spaces_data)
    
    # print(" Total spaces: ", len(spaces_data['spaces']))

    # for space in spaces_data['spaces']:
        
    #     print(space['name'])
    #     space_id = space['id']
    #     print(f"[+] Space ID: {space_id}")

    #     # Step 3: Get Folders
    #     folders_data = get_folders(space_id)
    #     folders = folders_data.get("folders", [])
        
    #     if folders:
    #         folder_id = folders[0]['id']
    #         print(f"[+] Folder ID: {folder_id}")
            
    #         lists_data = get_lists(folder_id)
    #         list_id = lists_data['lists'][0]['id']
    #         print(f"[+] List ID (from folder): {list_id}")
        
    #     else:
    #         print("[!] No folders found. Trying folderless lists...")
    #         lists_data = get_folderless_lists(space_id)
    #         if not lists_data['lists']:
    #             print("[❌] No lists found in space either.")
    #             exit()

    #         list_id = lists_data['lists'][0]['id']
    #         print(f"[+] List ID (folderless): {list_id}")

    #     # Step 4: Get Tasks
    #     # tasks_data = get_tasks_from_list(list_id)
    #     # tasks = tasks_data.get('tasks', [])
    #     # print(f"[+] Total tasks found: {len(tasks)}")
    #     # for task in tasks:
    #     #     print(f" - {task['name']} | Status: {task['status']['status']}")
    #     tasks_data = get_tasks_from_list(list_id, include_subtasks=True, include_closed=True)
    #     tasks = tasks_data.get("tasks", [])
    #     print(f"[+] Total tasks found: {len(tasks)} (including subtasks)")
    #     tasks.add(shared_tasks)
    #     print(f"[+] Total tasks found: {len(tasks)} (including subtasks)")
    #     for task in tasks:
    #         indent = "    " if task.get("parent") else ""
    #         status = task["status"]["status"]
    #         print(f"{indent}- {task['name']} | Status: {status}")
    #         print('*'*20)