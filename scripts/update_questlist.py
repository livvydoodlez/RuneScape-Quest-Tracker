import os
import json
import requests

# Function to create a safe filename by replacing invalid characters
def safe_filename(name):
    return name.replace(":", "").replace("?", "").replace("<", "").replace(">", "").replace("\"", "").replace("|", "").replace("/", "_").replace("\\", "_").replace("&", "and").strip()

# Step 1: Download the quest list from the URL
url = "https://oldschool.runescape.wiki/w/Quests/List"
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    with open("questlist.htm", "w", encoding='utf-8') as file:
        file.write(response.text)
else:
    print(f"Failed to download the quest list: {response.status_code}")
    exit(1)

# Step 2: Load the downloaded questlist.htm file
with open("questlist.htm", "r", encoding='utf-8') as file:
    content = file.readlines()

# Step 3: Create directories for F2P and P2P quests
os.makedirs("FreeQuests", exist_ok=True)
os.makedirs("MembersQuests", exist_ok=True)

# Step 4: Initialize flags for F2P and P2P quest sections
f2p_header_found = False
members_quests_found = False

# Step 5: Process each line
for i in range(len(content)):
    line = content[i]

    # Check for the Free-to-play quests section marker
    if '<li class="toclevel-1"><a href="#Free-to-play_quests">' in line:
        f2p_header_found = True
        continue

    # Check for the Members' quests section marker
    if '<h2><span class="mw-headline" id="Members\'_quests">' in line:
        members_quests_found = True
        f2p_header_found = False  # Reset F2P header found flag
        continue

    # Process F2P quests
    if f2p_header_found and '<tr data-rowid' in line:
        # Add the class for F2P quests
        line = line.replace('<tr data-rowid', '<tr class="quest-name-f2p" data-rowid')
        content[i] = line

        # Extract quest name
        quest_name = line.split('data-rowid="')[1].split('"')[0]  # Extract quest name
        
        # Replace '&#39;' with "'"
        quest_name = quest_name.replace("&#39;", "'")

        # Ensure there is a next line and it contains QP
        if i + 1 < len(content):
            qp_line = content[i + 1].strip()  # Get the next line for QP
            qp_value_str = qp_line.split('>')[1].split('<')[0].strip()  # Extract number from <td>
            
            # Validate and convert QP value
            if qp_value_str.isdigit() or qp_value_str.replace('.', '', 1).isdigit():  # Check if valid float or int
                qp_value = int(float(qp_value_str))  # Clean and convert to integer
            else:
                qp_value = 0  # Default to 0 if no valid QP found
        else:
            qp_value = 0  # Default to 0 if next line does not exist

        # Prepare data for JSON file
        quest_data = {
            "Title": quest_name.replace("_", " ").title(),  # Format title
            "Skills": {
                "Attack": 0,
                "Defence": 0,
                "Strength": 0,
                "Prayer": 0,
                "Magic": 0,
                "Cooking": 0,
                "Fletching": 0,
                "Fishing": 0,
                "Firemaking": 0,
                "Smithing": 0,
                "Herblore": 0,
                "Thieving": 0,
                "Runecraft": 0,
                "Hunter": 0,
                "Construction": 0,
                "QP": qp_value  # Assign cleaned QP
            }
        }

        # Write to a JSON file in the FreeQuests directory
        json_filename = f"FreeQuests/{safe_filename(quest_name)}.json"
        with open(json_filename, "w", encoding='utf-8') as json_file:
            json.dump(quest_data, json_file, indent=4)

    # Process P2P quests
    if members_quests_found and '<tr data-rowid' in line:
        # Add the class for P2P quests
        line = line.replace('<tr data-rowid', '<tr class="quest-name-p2p" data-rowid')
        content[i] = line

        # Extract quest name
        quest_name = line.split('data-rowid="')[1].split('"')[0]  # Extract quest name
        
        # Replace '&#39;' with "'"
        quest_name = quest_name.replace("&#39;", "'")

        # Ensure there is a next line and it contains QP
        if i + 1 < len(content):
            qp_line = content[i + 1].strip()  # Get the next line for QP
            qp_value_str = qp_line.split('>')[1].split('<')[0].strip()  # Extract number from <td>
            
            # Validate and convert QP value
            if qp_value_str.isdigit() or qp_value_str.replace('.', '', 1).isdigit():  # Check if valid float or int
                qp_value = int(float(qp_value_str))  # Clean and convert to integer
            else:
                qp_value = 0  # Default to 0 if no valid QP found
        else:
            qp_value = 0  # Default to 0 if next line does not exist

        # Prepare data for JSON file
        quest_data = {
            "Title": quest_name.replace("_", " ").title(),  # Format title
            "Skills": {
                "Attack": 0,
                "Defence": 0,
                "Strength": 0,
                "Prayer": 0,
                "Magic": 0,
                "Cooking": 0,
                "Fletching": 0,
                "Fishing": 0,
                "Firemaking": 0,
                "Smithing": 0,
                "Herblore": 0,
                "Thieving": 0,
                "Runecraft": 0,
                "Hunter": 0,
                "Construction": 0,
                "QP": qp_value  # Assign cleaned QP
            }
        }

        # Format JSON filename for P2P quests
        json_filename = f"MembersQuests/{safe_filename(quest_name)}.json"
        with open(json_filename, "w", encoding='utf-8') as json_file:
            json.dump(quest_data, json_file, indent=4)

print("JSON files created for all quests.")
