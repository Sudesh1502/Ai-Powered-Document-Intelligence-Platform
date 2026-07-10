import os
import yaml
from pathlib import Path
from azure.data.tables import TableServiceClient
from azure.core.exceptions import ResourceExistsError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def migrate_users():
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        print("Error: AZURE_STORAGE_CONNECTION_STRING is not set in .env")
        return

    config_path = Path("auth_config.yaml")
    if not config_path.exists():
        print(f"Error: {config_path} not found.")
        return

    with open(config_path) as file:
        config = yaml.safe_load(file)

    try:
        # Connect to Table Storage
        table_service_client = TableServiceClient.from_connection_string(connection_string)
        
        # Create the Users table if it doesn't exist
        table_name = "Users"
        try:
            table_service_client.create_table(table_name)
            print(f"Created table '{table_name}'.")
        except ResourceExistsError:
            print(f"Table '{table_name}' already exists.")

        table_client = table_service_client.get_table_client(table_name=table_name)
        
        usernames = config.get("credentials", {}).get("usernames", {})
        
        print(f"Found {len(usernames)} users in auth_config.yaml. Migrating...")
        
        for email, user_data in usernames.items():
            # In Azure Table Storage:
            # PartitionKey = "Users"
            # RowKey = email
            entity = {
                "PartitionKey": "Users",
                "RowKey": email,
                "Email": user_data.get("email"),
                "Name": user_data.get("name"),
                "Password": user_data.get("password")
            }
            
            try:
                table_client.upsert_entity(entity=entity)
                print(f"Successfully migrated user: {email}")
            except Exception as e:
                print(f"Failed to migrate user {email}: {e}")

        print("\nMigration complete! You can now safely delete auth_config.yaml.")

    except Exception as e:
        print(f"Critical error connecting to Azure: {e}")

if __name__ == "__main__":
    migrate_users()
