import os

def clean_members_quests(folder_path):
    # Check if the folder exists
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist.")
        return

    # Iterate through all files in the specified folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Check if it's a file
        if os.path.isfile(file_path):
            # Check if the filename contains "Recipe for Disaster"
            if "Recipe for Disaster" in filename:
                # If the filename is NOT the exact match, delete it
                if filename != "Recipe for Disaster.json":
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")

if __name__ == "__main__":
    folder_path = "MembersQuests"  # Change this to the path of your folder if needed
    clean_members_quests(folder_path)
