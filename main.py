import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_PAGE = os.getenv('NOTION_PAGE')

# Google Sheets Authentication
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('project.json', scope)
gc = gspread.authorize(credentials)
worksheet = gc.open('School .23').get_worksheet(1)

# Get the grocery items from the Google Sheet
grocery_row = worksheet.row_values(3)  # Assuming the grocery items are in row 3
grocery_items = ' '.join(grocery_row).split()  # Split by whitespace

# Create a set to store unique grocery items
unique_grocery_items_set = set()

# Create a list to store the final grocery list with one occurrence of each item
unique_grocery_items_list = []

# Iterate through the grocery items
for item in grocery_items:
    # Remove any leading/trailing whitespace and convert to lowercase for case-insensitive comparison
    item = item.strip().lower()

    # Exclude the word "groceries" and items that are already in the set
    if item != 'groceries' and item not in unique_grocery_items_set:
        unique_grocery_items_set.add(item)
        unique_grocery_items_list.append(item)

# Convert to a comma-separated string
grocery_list = ', '.join(unique_grocery_items_list)

# Notion Integration Token
notion_api_key = NOTION_API_KEY  
parent_page_id = NOTION_PAGE

# Send the grocery list to Notion
url = 'https://api.notion.com/v1/pages'
headers = {
    'Authorization': f'Bearer {notion_api_key}',
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28',
}

# Create a checklist block with grocery items
data = {
    'parent': {
        'type': 'page_id',
        'page_id': parent_page_id,
    },
    'properties': {
        'title': [
            {
                'text': {
                    'content': ' ',  # Title of your checklist
                },
            },
        ],
    },
    'children': [
        {
            'object': 'block',
            'type': 'to_do',
            'to_do': {
                'rich_text': [
                    {
                        'text': {
                            'content': item,
                        },
                    },
                ],
            },
        }
        for item in unique_grocery_items_list
    ],
}


response = requests.post(url, headers=headers, data=json.dumps(data))
if response.status_code == 200:
    # Retrieve the ID of the newly created bulleted list block
    block_id = response.json()['id']

    # Add grocery items as individual list items
    for item in unique_grocery_items_list:
        item_data = {
            'object': 'block',
            'type': 'bulleted_list_item',
            'bulleted_list_item': {
                'text': [
                    {
                        'type': 'text',
                        'text': {
                            'content': item,
                        },
                    },
                ],
            },
        }

        # Append each item to the bulleted list
        item_url = f'https://api.notion.com/v1/blocks/{block_id}/children'
        item_response = requests.post(item_url, headers=headers, data=json.dumps(item_data))

    print('Grocery checklist added to Notion!')
else:
    print(f'Error: {response.status_code} - {response.text}')