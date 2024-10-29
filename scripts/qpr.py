import requests
from bs4 import BeautifulSoup
import json
import os
import re

# URL of the Old School RuneScape quest list page
url = "https://oldschool.runescape.wiki/w/Quests/List"

# Make the HTTP request to fetch the page content
response = requests.get(url)
response.raise_for_status()  # Check if the request was successful

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Initialize a dictionary to store quest name and QPR mappings
quest_rewards = {}

# Locate all table rows on the page
rows = soup.find_all("tr")

# Iterate over each row to get the quest name and quest point reward
for row in rows:
    # Get the quest name from the data-rowid attribute
    quest_name = row.get("data-rowid")

    # If quest_name is not None, proceed
    if quest_name:
        # Ensure the row has at least five cells (0-based index for rewards)
        cells = row.find_all("td")
        if len(cells) >= 5:
            # Get the quest point reward from the fifth cell (index 4)
            quest_point_cell = cells[4]

            # Print the cell contents for debugging
            print(f"Row for {quest_name} has cells: {[cell.text.strip() for cell in cells]}")

            # Extract and store the quest point reward as an integer
            try:
                quest_point_reward = int(quest_point_cell.text.strip())
                quest_rewards[quest_name] = quest_point_reward
                # Print out the quest name and quest point reward to verify
                print(f"Scraped: {quest_name} -> QPR: {quest_point_reward}")
            except ValueError:
                # If the reward isn't an integer, check if it's 'N/A' or something else
                print(f"Could not convert quest point reward for {quest_name}: {quest_point_cell.text.strip()}")
                continue

# Define directories for FreeQuests and MembersQuests
directories = ["FreeQuests", "MembersQuests"]

# Initialize total quest points
total_qp = 0

# Iterate over directories to update JSON files
for directory in directories:
    # List all JSON files in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            # Load the current quest's data
            quest_file_path = os.path.join(directory, filename)
            with open(quest_file_path, 'r') as quest_file:
                quest_data = json.load(quest_file)

            # Get the quest title
            quest_title = quest_data["Title"]

            # Check if the quest title matches any scraped quests using a LIKE-style approach
            matched = False
            for scraped_quest in quest_rewards.keys():
                # Use a regex pattern to check for similar quest names
                if re.search(re.escape(quest_title), scraped_quest, re.IGNORECASE):
                    matched = True
                    # Update the "QP" field with the quest point reward
                    quest_data["Skills"]["QP"] = quest_rewards[scraped_quest]
                    print(f"Updating {quest_title} QP: {quest_rewards[scraped_quest]}")
                    total_qp += quest_rewards[scraped_quest]  # Add to total quest points
                    break
            
            # Save the updated quest data back to the file only if matched
            if matched:
                with open(quest_file_path, 'w') as quest_file:
                    json.dump(quest_data, quest_file, indent=4)

print("Quest point rewards updated in the JSON files.")

# Now write the total QP into total_requirements.json
total_requirements_path = "total_requirements.json"

# Prepare the data for total_requirements.json
total_requirements_data = {
    "Attack": 50,
    "Defence": 65,
    "Strength": 70,
    "Prayer": 50,
    "Magic": 75,
    "Cooking": 70,
    "Fletching": 60,
    "Fishing": 65,
    "Firemaking": 75,
    "Smithing": 70,
    "Herblore": 70,
    "Thieving": 72,
    "Runecraft": 65,
    "Hunter": 70,
    "Construction": 70,
    "QP": total_qp,  # Add the total QP here
    "Combat level": 95,
    "Mining": 72,
    "Crafting": 70,
    "Agility": 70,
    "Woodcutting": 71,
    "Slayer": 69,
    "Ranged": 70,
    "Farming": 70,
    "Hitpoints": 70
}

# Write to total_requirements.json
with open(total_requirements_path, 'w') as total_requirements_file:
    json.dump(total_requirements_data, total_requirements_file, indent=4)

print(f"Total quest points written to {total_requirements_path}: {total_qp}")
