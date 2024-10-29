import os
import json

def get_highest_requirements(folder):
    highest_requirements = {}

    # Iterate through each file in the specified folder
    for filename in os.listdir(folder):
        if filename.endswith('.json'):
            file_path = os.path.join(folder, filename)
            
            # Read the JSON file
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from file: {file_path}")
                    continue

                # Check for skills in the data (use 'Skills' key as per your JSON structure)
                skills = data.get('Skills', {})
                for skill, level in skills.items():
                    # Ensure we are dealing with integers
                    if isinstance(level, int):
                        if skill not in highest_requirements:
                            highest_requirements[skill] = level
                        else:
                            highest_requirements[skill] = max(highest_requirements[skill], level)

                # Check for QP
                qp = data.get('Skills', {}).get('QP', 0)
                if 'QP' not in highest_requirements:
                    highest_requirements['QP'] = qp
                else:
                    highest_requirements['QP'] = max(highest_requirements['QP'], qp)

    return highest_requirements

def main():
    # Define the paths to the FreeQuests and MembersQuest folders
    freequests_folder = 'FreeQuests'
    membersquest_folder = 'MembersQuests'

    # Get highest requirements from both folders
    total_requirements = {}

    total_requirements.update(get_highest_requirements(freequests_folder))
    total_requirements.update(get_highest_requirements(membersquest_folder))

    # Save the total requirements to a JSON file
    with open('total_requirements.json', 'w') as outfile:
        json.dump(total_requirements, outfile, indent=4)

    print("Total requirements have been saved to total_requirements.json")

if __name__ == '__main__':
    main()
