import os
import json
import requests
from bs4 import BeautifulSoup

# Paths to the folders containing the JSON files
free_quests_folder_path = "FreeQuests"
members_quests_folder_path = "MembersQuests"

# Path to the error log file
error_log_path = "error.log"

# Function to handle special cases for URL formatting
def special_case_urls(quest_name):
    special_cases = {
        "Romeo and Juliet": "Romeo_%26_Juliet",
        "Horror from the Deep": "Horror_from_the_Deep",
        "Icthlarin's Little Helper": "Icthlarin's_Little_Helper",
        "Recipe for Disaster": "Recipe_for_Disaster"
    }
    return special_cases.get(quest_name, quest_name.replace(' ', '%20'))

# Function to log errors to the error log file
def log_error(message):
    with open(error_log_path, 'a') as log_file:
        log_file.write(message + '\n')

def fetch_quest_requirements(url, quest_name):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for request errors

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        requirements = {}
        stop_processing = False  # Flag to stop processing once we hit the items required section

        # Iterate through all list items (li elements)
        for element in soup.find_all('li'):
            # Check for the "Items required" header
            if element.find('th', class_='questdetails-header') and 'Items required' in element.text:
                stop_processing = True  # Stop processing any further requirements
                break  # Exit the loop as we don't need to look for more requirements

            # Skip lines containing "Ability to"
            if "Ability to" in element.text:
                continue  # Skip this line and move to the next element

            # If we haven't stopped processing yet, look for skills
            if not stop_processing:
                for span in element.find_all('span', class_='scp'):
                    # Ensure the span has the required attributes before accessing them
                    if 'data-skill' in span.attrs and 'data-level' in span.attrs:
                        skill_name = span['data-skill']  # Extract the skill name
                        skill_level = span['data-level']  # Extract the skill level

                        try:
                            # Handle cases where levels might contain commas or other formats
                            skill_level_int = int(skill_level.replace(',', ''))  # Remove commas for conversion

                            # Validate the skill level: 0-99 for skills, 0-999 for QP
                            if skill_name == "QP":
                                if skill_level_int < 0 or skill_level_int > 999:
                                    raise ValueError(f"QP level out of range: {skill_level_int}")
                            elif skill_level_int < 0 or skill_level_int > 99:
                                raise ValueError(f"Skill level out of range for {skill_name}: {skill_level_int}")

                            requirements[skill_name] = skill_level_int  # Store skill requirements in a dict
                        except ValueError as ve:
                            log_error(f"Invalid level format for {quest_name} ({skill_name}): {skill_level} - {ve}")
                            continue  # Skip invalid levels

        return requirements  # Return the skill requirements found

    except requests.RequestException as req_err:
        log_error(f"Error fetching URL {url} for {quest_name}: {req_err}")  # Log only request-related errors
        return {}
    except Exception as e:
        log_error(f"Error parsing the URL {url} for {quest_name}: {e}")  # Log parsing errors
        return {}

# Function to update JSON files with fetched requirements
def update_json_file(quest_name, requirements, folder_path):
    json_file_path = os.path.join(folder_path, f"{quest_name}.json")
    
    # Load existing data from the JSON file
    try:
        with open(json_file_path, 'r') as file:
            quest_data = json.load(file)
        
        # Update the skills with the fetched requirements
        for skill, level in requirements.items():
            quest_data['Skills'][skill] = level  # Add or update the skill with the new level
        
        # Check for existing QP or Quest Points
        quest_points = quest_data['Skills'].get('Quest points', 0)
        if 'QP' in quest_data['Skills']:
            quest_data['Skills']['QP'] = max(quest_points, quest_data['Skills']['QP'])  # Update QP if necessary
        else:
            quest_data['Skills']['QP'] = quest_points  # Add QP if it doesn't exist
        
        # Remove the "Quest points" key if it exists
        if 'Quest points' in quest_data['Skills']:
            del quest_data['Skills']['Quest points']  # Remove "Quest points" from the dictionary

        # Save the updated data back to the JSON file
        with open(json_file_path, 'w') as file:
            json.dump(quest_data, file, indent=4)  # Use indent for pretty printing
        print(f"Updated {quest_name}.json with requirements: {requirements}")

    except FileNotFoundError:
        log_error(f"JSON file for {quest_name} not found.")
    except json.JSONDecodeError:
        log_error(f"Error decoding JSON for {quest_name}.")
    except Exception as e:
        log_error(f"Error updating {quest_name}.json: {e}")

# Function to process each JSON file in the specified folder
def process_json_files(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            quest_name = filename[:-5].replace('_', ' ')  # Remove .json and replace underscores with spaces
            url_safe_name = special_case_urls(quest_name)  # Get the URL-safe quest name
            url = f"https://oldschool.runescape.wiki/w/{url_safe_name}"  # Format the URL
            print(f"\nFetching requirements for: {quest_name}")

            # Fetch the requirements from the website
            requirements = fetch_quest_requirements(url, quest_name)

            # If requirements were found, update the JSON file
            if requirements:
                update_json_file(quest_name, requirements, folder_path)

# Process both FreeQuests and MembersQuests folders
process_json_files(free_quests_folder_path)
process_json_files(members_quests_folder_path)
