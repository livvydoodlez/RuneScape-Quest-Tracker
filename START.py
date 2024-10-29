import requests
import os
import json
import glob
import time
import webbrowser
from flask import Flask, request, render_template_string
from datetime import datetime, timedelta

# Define the path for the date file
date_file_path = "last_run_date.txt"

# Function to read the last run date
def get_last_run_date():
    if os.path.exists(date_file_path):
        with open(date_file_path, 'r') as file:
            date_str = file.read().strip()
            if date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
    return None

# Function to update the last run date
def update_last_run_date():
    with open(date_file_path, 'w') as file:
        file.write(datetime.now().strftime('%Y-%m-%d'))

# Check the last run date
last_run_date = get_last_run_date()
current_date = datetime.now()

if last_run_date is None or (current_date - last_run_date) > timedelta(days=30):
    # Run the main part of the script
    exec(open("scripts/update_questlist.py").read())
    print("Getting current quest list...")
    time.sleep(2)

    exec(open("scripts/cleanup.py").read())
    print("Cleaning all quests...")
    time.sleep(2)

    exec(open("scripts/getRequirements.py").read())
    print("Extracting Quest Requirements...")
    time.sleep(2)

    exec(open("scripts/total_requirements.py").read())
    print("Finding total requirements...")
    time.sleep(2)

    exec(open("scripts/qpr.py").read())
    print("Finding quest point rewards...")
    time.sleep(2)

    print("[SERVER] DONE! Starting Webserver:")
    webbrowser.open('http://127.0.0.1:8000', new=2)
    
    # Update the last run date after executing the main tasks
    update_last_run_date()
else:
    print("Script has already run within the last 30 days. Skipping updates.")
    webbrowser.open('http://127.0.0.1:8000', new=2)

app = Flask(__name__)


# Skill names (excluding "Overall")
skills = [
    "Attack", "Defence", "Strength", "Hitpoints", "Ranged", "Prayer",
    "Magic", "Cooking", "Woodcutting", "Fletching", "Fishing", "Firemaking",
    "Crafting", "Smithing", "Mining", "Herblore", "Agility", "Thieving", "Slayer",
    "Farming", "Runecraft", "Hunter", "Construction"
]

# Directory for storing character data
characters_dir = "characters"
quests_dir = ["FreeQuests", "MembersQuests"]

# Ensure characters directory exists
os.makedirs(characters_dir, exist_ok=True)

def load_total_requirements():
    """Load total requirements from JSON file."""
    with open('total_requirements.json', 'r') as file:
        return json.load(file)

def load_quests():
    """Load all quests from JSON files in the specified directories."""
    free_quests = []
    members_quests = []
    
    for directory in quests_dir:
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                with open(os.path.join(directory, filename), 'r') as quest_file:
                    quest_data = json.load(quest_file)
                    if directory == "FreeQuests":
                        free_quests.append(quest_data)
                    elif directory == "MembersQuests":
                        members_quests.append(quest_data)
    
    # Sort quests alphabetically
    free_quests.sort(key=lambda q: q["Title"])
    members_quests.sort(key=lambda q: q["Title"])
    
    return free_quests, members_quests

# HTML template with images for each skill as separate headers
html_template = """
<!doctype html>
<html lang="en">
<head>
    <title>RuneScape Quest Tracker</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            background-color: #121212; /* Dark background */
            color: #ffffff; /* Light text color */
        }
        table { 
            width: 80%; 
            margin: auto; 
            border-collapse: collapse; 
            background-color: #1e1e1e; /* Darker table background */
        }
        th, td { 
            padding: 10px; 
            text-align: center; 
            border: 1px solid #333; /* Lighter border color */
        }
        th { 
            background-color: #1a1a1a; /* Dark header */
        }
        img { 
            width: 32px; 
            height: 32px; 
        }
        .prev-characters { 
            text-align: center; 
            margin-bottom: 20px; 
        }
        .req-meets { 
            background-color: limegreen; /* Green for meeting requirements */
        }  
        .req-not-meets { 
            background-color: red; /* Red for not meeting requirements */
        }
        .quest-completed {
            background-color: #28a745; /* Green for completed quests */
        }
    </style>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>

<script>
    $(document).ready(function() {
        // Initialize total quest points based on loaded data
        let totalQP = {{ character_data.quest_points | default(0) }};
        $('#skills-table td[data-skill="quest"]').text(totalQP); // Display initial total quest points

        // Function to update quest points
        function updateQuestPoints(checkbox) {
            const questQP = parseInt($(checkbox).data('qp'), 10); // Get QP from checkbox
            if ($(checkbox).is(':checked')) {
                totalQP += questQP;  // Add points if checked
            } else {
                totalQP -= questQP;  // Subtract points if unchecked
            }
            $('#skills-table td[data-skill="quest"]').text(totalQP); // Update the display
        }

        // Handle checkbox changes
        $('.quest-checkbox').change(function() {
            const questRow = $(this).closest('tr');
            if ($(this).is(':checked')) {
                questRow.addClass('quest-completed'); // Highlight the completed quest
            } else {
                questRow.removeClass('quest-completed'); // Remove highlight
            }
            updateQuestPoints(this); // Update quest points on change

            // Send the updated quest status to the server
            var questName = $(this).data('quest-name');
            $.post('/update_quest', {
                character_name: '{{ character_name }}',
                quest_name: questName,
                completed: $(this).is(':checked')
            });
        });

        // Initialize checkboxes based on completed quests on page load
        $('.quest-checkbox').each(function() {
            const questName = $(this).data('quest-name');
            if ({{ character_data.completed_quests|tojson }}.includes(questName)) {
                $(this).prop('checked', true); // Check if the quest is completed
                // Do not call updateQuestPoints here to prevent doubling
            }
        });
    });

    // Function to update skills color
    function updateSkillsColor() {
        $('#quest-requirements td[data-requirement]').each(function() {
            var skillClass = $(this).attr('class');
            var requiredLevel = parseInt($(this).data('requirement'));
            var characterLevel = parseInt($('#skills-table .' + skillClass).text());

            if (characterLevel >= requiredLevel) {
                $('#quest-requirements .' + skillClass).addClass('req-meets').removeClass('req-not-meets');
            } else {
                $('#quest-requirements .' + skillClass).addClass('req-not-meets').removeClass('req-meets');
            }
        });
    }

    // Call the function to initialize colors on page load
    $(document).ready(function() {
        updateSkillsColor();
    });
</script>

</head>
<body>
    <h2 style="text-align:center;">RuneScape Quest Tracker by <a href="https://linktr.ee/livvydoodlez/" target="_blank">Livvydoodlez</a></h2>
    <form method="post" style="text-align:center; margin-bottom: 20px;">
        <input type="text" name="character_name" placeholder="Enter character's display name" required>
        <input type="hidden" name="lookup" value="lookup" />
        <button type="submit">Lookup</button>
    </form>
    <h2><center>IS YOUR STATS MISSING?</center></h2>
    <p><center>It's because this is pulling data from hiscores page. If you want, go into the characters folder and open your .json file and manually enter your skill levels into the .json file.</center></p>
    <div class="prev-characters">
        <h3>Previously Looked Up Characters:</h3>
        <ul>
        {% for char in previous_characters %}
            <li>
                {{ char }} 
                <form method="post" style="display:inline;">
                    <input type="hidden" name="character_name" value="{{ char }}">
                    <button type="submit">Load</button>
                </form>
            </li>
        {% endfor %}
        </ul>
    </div>
    
    {% if skills_data %}
    <h3 style="text-align:center;">Skills</h3>
    <table id="skills-table">
        <tr>
            <th>Username</th>
            {% for skill in skills %}
            <th><img src="{{ url_for('static', filename='img/skill_icon_' + skill.lower() + '1.gif') }}" alt="{{ skill }} icon"><br>{{ skill }}</th>
            {% endfor %}
            <th><img src="{{ url_for('static', filename='img/skill_icon_quest1.gif') }}" alt="Quest icon"><br>Quest</th>
        </tr>
        <tr>
            <td>{{ character_name }}</td>
            {% for skill, _, _, level, _ in skills_data %}
            <td class="{{ skill.lower() }}" data-skill="{{ skill.lower() }}">{{ level }}</td> 
            {% endfor %}
            <td data-skill="quest">{{ character_data.quest_points }}</td>  <!-- Display the total quest points -->
        </tr>
    </table>

<h3 style="text-align:center;">Quest Requirements</h3>
<table id="quest-requirements">
    <tr>
        <th>Quest Requirements</th>
        {% for skill in skills %}
        <th><img src="{{ url_for('static', filename='img/skill_icon_' + skill.lower() + '1.gif') }}" alt="{{ skill }} icon"><br>{{ skill }}</th>
        {% endfor %}
        <th><img src="{{ url_for('static', filename='img/skill_icon_quest1.gif') }}" alt="Quest icon"><br>Quest</th>
    </tr>
    <tr>
        <td>Total Requirements</td>
        {% for skill in skills %}
            {% set required_level = total_requirements.get(skill, 0) %}
            <td class="{{ skill.lower() }}" data-requirement="{{ required_level }}">
                {{ required_level }}
            </td>
        {% endfor %}
        <td>{{ total_requirements.get('QP', 0) }}</td>  <!-- This line should show 314 -->
    </tr>
</table>

    <h3 style="text-align:center;">Quest List</h3>
    <table id="quest-list">
        <tr>
            <th>Quest Name</th>
            {% for skill in skills %}
            <th><img src="{{ url_for('static', filename='img/skill_icon_' + skill.lower() + '1.gif') }}" alt="{{ skill }} icon"><br>{{ skill }}</th>
            {% endfor %}
            <th><img src="{{ url_for('static', filename='img/skill_icon_quest1.gif') }}" alt="Quest icon"><br>Quest</th>
        </tr>
        <tr>
            <td style="text-align: center; background-color: #1e1e1e; font-weight: bold;">Free Quests</td>
        </tr>
        {% for quest in free_quests %}
        <tr class="{% if quest['Title'] in character_data.completed_quests %}quest-completed{% endif %}">
            <td>{{ quest['Title'] }}</td>
            {% for skill in skills %}
            <td>{{ quest['Skills'].get(skill, 0) }}</td>
            {% endfor %}
            <td>
                <input type="checkbox" 
                       class="quest-checkbox" 
                       data-quest-name="{{ quest['Title'] }}" 
                       data-qp="{{ quest['Skills'].get('QP', 0) }}"  <!-- Add the quest QP here -->
            </td>
        </tr>
        {% endfor %}
        <tr>
            <td colspan="{{ skills | length + 2 }}" style="text-align: center; background-color: #1e1e1e; font-weight: bold;">Members Quests</td>
        </tr>
        {% for quest in members_quests %}
        <tr class="{% if quest['Title'] in character_data.completed_quests %}quest-completed{% endif %}">
            <td>{{ quest['Title'] }}</td>
            {% for skill in skills %}
            <td>{{ quest['Skills'].get(skill, 0) }}</td>
            {% endfor %}
            <td>
                <input type="checkbox" class="quest-checkbox" 
                       data-quest-name="{{ quest['Title'] }}" 
                       data-qp="{{ quest['Skills'].get('QP', 0) }}" <!-- Add the quest QP here -->
            </td>
        </tr>
        {% endfor %}
    </table>
    {% endif %}
</body>
</html>

"""



@app.route("/", methods=["GET", "POST"])
def index():
    total_requirements = load_total_requirements()
    free_quests, members_quests = load_quests()
    character_data = {"completed_quests": []}
    
    # Initialize skills_data and character_name to default values
    skills_data = []
    character_name = ""  # Initialize character_name

    if request.method == "POST":
        character_name = request.form.get("character_name", "")  # Get character_name from form

        # Check if 'lookup' value is present in the POST request
        if 'lookup' in request.form:
            url = f"https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws?player={character_name}"
            
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data_lines = response.text.strip().split("\n")
                    
                    # Initialize skill data with default values
                    skill_levels = {skill: 0 for skill in skills}

                    # Parse skills data, omitting "Overall"
                    for i, line in enumerate(data_lines[1:len(skills)+1]):
                        values = line.split(",")
                        if len(values) < 3:
                            print(f"Warning: Expected 3 values but got {len(values)} for line: {line}")
                            continue
                        
                        rank, level, xp = values
                        skill_levels[skills[i]] = int(level)

                    # Load existing character data if it exists
                    character_file_path = os.path.join(characters_dir, f"{character_name}.json")
                    if os.path.exists(character_file_path):
                        with open(character_file_path, 'r') as json_file:
                            character_data = json.load(json_file)
                            character_data["completed_quests"] = character_data.get("completed_quests", [])

                    # Initialize total quest points
                    total_quest_points = 0

                    # Calculate total quest points from completed quests
                    for quest_name in character_data["completed_quests"]:
                        # Look for the quest in both FreeQuests and MembersQuests directories
                        for directory in quests_dir:
                            quest_file_path = os.path.join(directory, f"{quest_name}.json")
                            if os.path.exists(quest_file_path):
                                with open(quest_file_path, 'r') as quest_file:
                                    quest_data = json.load(quest_file)
                                    # Access the correct QP from the Skills section
                                    total_quest_points += quest_data.get("Skills", {}).get("QP", 0)
                                break  # Exit once the quest is found

                    # Save character data to JSON file
                    character_data = {
                        "Character": character_name,
                        "Skills": skill_levels,
                        "completed_quests": character_data.get("completed_quests", []),
                        "quest_points": total_quest_points  # Set total quest points here
                    }
                    with open(character_file_path, 'w') as json_file:
                        json.dump(character_data, json_file, indent=4)

                    # Prepare data for display
                    skills_data = [(skill, None, None, level, None) for skill, level in skill_levels.items()]
                    
                else:
                    return f"<p style='text-align:center;color:red;'>Error: Character '{character_name}' not found.</p>"
            
            except requests.exceptions.RequestException as e:
                return f"<p style='text-align:center;color:red;'>Error: A network error occurred. {e}</p>"
        
        else:
            # If 'lookup' is not present, load existing character data
            character_file_path = os.path.join(characters_dir, f"{character_name}.json")
            if os.path.exists(character_file_path):
                with open(character_file_path, 'r') as json_file:
                    character_data = json.load(json_file)
                    skills_data = [(skill, None, None, character_data["Skills"].get(skill, 0), None) for skill in skills]
            else:
                return f"<p style='text-align:center;color:red;'>Error: Character '{character_name}' not found.</p>"

    # Load previously looked up characters
    previous_characters = [f[:-5] for f in os.listdir(characters_dir) if f.endswith('.json')]  # Get list of character names

    return render_template_string(html_template, skills_data=skills_data, skills=skills, character_name=character_name, previous_characters=previous_characters, total_requirements=total_requirements, free_quests=free_quests, members_quests=members_quests, character_data=character_data)



@app.route("/update_quest", methods=["POST"])
def update_quest():
    character_name = request.form["character_name"]
    quest_name = request.form["quest_name"]
    completed = request.form.get("completed") == 'true'
    
    # Load existing character data
    character_file_path = os.path.join(characters_dir, f"{character_name}.json")
    if os.path.exists(character_file_path):
        with open(character_file_path, 'r') as json_file:
            character_data = json.load(json_file)

        # Load the quest data to find the QP for the specific quest
        quest_qp = 0
        
        # Look for the quest in both FreeQuests and MembersQuests directories
        for directory in quests_dir:
            quest_file_path = os.path.join(directory, f"{quest_name}.json")
            if os.path.exists(quest_file_path):
                with open(quest_file_path, 'r') as quest_file:
                    quest_data = json.load(quest_file)
                    # Access the correct QP from the Skills section
                    quest_qp = quest_data.get("Skills", {}).get("QP", 0)  # Correct path to the QP
                    print(f"Quest Name: {quest_name}, QP: {quest_qp}")
                break  # Exit once the quest is found

        # Update completed quests and total quest points
        if completed:
            if quest_name not in character_data.get("completed_quests", []):
                character_data["completed_quests"].append(quest_name)
                character_data['quest_points'] += quest_qp  # Add the quest points from the quest data
        else:
            if quest_name in character_data.get("completed_quests", []):
                character_data["completed_quests"].remove(quest_name)
                character_data['quest_points'] -= quest_qp  # Subtract the quest points from the quest data

        # Save updated character data
        with open(character_file_path, 'w') as json_file:
            json.dump(character_data, json_file)

    return '', 204  # No content response




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
