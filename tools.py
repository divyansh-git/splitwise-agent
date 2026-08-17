import ollama
import os
import requests
from rich.markdown import Markdown
from rich.panel import Panel
import requests

MY_CHAT_ID=os.getenv("MY_CHAT_ID")       
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("SPLITWISE_API_KEY")

def add_expenses(cost: float, description: str,groupid:str) -> dict:
    """Add an expense to the user's Splitwise account via the Splitwise API.
    It adds the expense to the groupid fetched from the group name adding cost and description.

    Args:
        cost: The value of the expense to be added
        description: text explaining the purpose of the expense
        groupid: groupid in which the expense is need to be added

    Returns:
        The API response describing whether the expense was created, including the expense ID.
    """
    url = "https://secure.splitwise.com/api/v3.0/create_expense"
    payload = {
        "cost": str(cost),
        "description": description,
        "group_id": int(groupid),
        "split_equally": True,
        "currency_code": "INR",
    }
    response = requests.post(
        url,
        json=payload,
        headers={"Authorization": f"Bearer {API_KEY}"},
    )
    print(f"Status Code: {response.status_code}")
    response.raise_for_status()
    return response.json()

def groupIdLookup()->list:
    """This tool makes the list of group name and groupid as a dict
   
    Args:
        No Args
   
    Returns:
        list of dicts containing mapping of group_name : group_id 
    """
    url = "https://secure.splitwise.com/api/v3.0/get_groups"
    response = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
    response.raise_for_status()

    groups = response.json()["groups"]
    result=[]
    for group in groups:
        result.append({group['name']:group['id']})

    return result

def getGroupExpenses(groupid:int)->list:
    """This tool makes the list of group name and groupid as a dict
       
    Args:
        No Args   
    Returns:
        list of dicts containing the cost, description, date,currency, created_by
    """
    url = f"https://secure.splitwise.com/api/v3.0/get_expenses?group_id={groupid}&limit=1000"
    response = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
    response.raise_for_status()
    
    expenses = response.json()["expenses"]
    result=[]
    for expense in expenses:
        result.append({"cost":expense['cost'],"description":expense['description'],"date":expense['date'],"created_by":f"{expense['created_by']['first_name']} {expense['created_by']['last_name']}"})
    
    return result

def getFriendsList()->list:
    """This tool makes the list of friends of the user
           
    Args:
        No Args   
    Returns:
        list of dicts containing the friend_name:friend_id
    """
    url = f"https://secure.splitwise.com/api/v3.0/get_friends"
    response = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
    response.raise_for_status()
        
    friends= response.json()["friends"]
    result=[]
    for friend in friends:
        result.append({f"{friend['first_name']} {friend['last_name']}":friend['id']})
    return result

def getGroupDetails(group_id:int)->list:
    """This tool gives the details of a group provided its groupid 
               
        Args:
            group_id: id of the group for which the details are needed
        Returns:
            returns the dictionary of the group details.
            for ex:- {
                "group": {
                    "id": 321,
                    "name": "Housemates 2020",
                    "group_type": "home",
                    "updated_at": "2019-08-24T14:15:22Z",
                    "simplify_by_default": true,
                    "members": [
                    {
                        "id": 0,
                        "first_name": "Ada",
                        "last_name": "Lovelace",
                        "email": "ada@example.com",
                        "registration_status": "confirmed",
                        "picture": {
                        "small": "string",
                        "medium": "string",
                        "large": "string"
                        },
                        "custom_picture": false,
                        "balance": [
                        {
                            "currency_code": "USD",
                            "amount": "-5.02"
                        }
                        ]
                    }
                    ],
                    "original_debts": [
                    {
                        "from": 18523,
                        "to": 90261,
                        "amount": "414.5",
                        "currency_code": "USD"
                    }
                    ],
                    "simplified_debts": [
                    {
                        "from": 18523,
                        "to": 90261,
                        "amount": "414.5",
                        "currency_code": "USD"
                    }
                    ],
                    "avatar": {
                    "original": null,
                    "xxlarge": "https://s3.amazonaws.com/splitwise/uploads/group/default_avatars/avatar-ruby2-house-1000px.png",
                    "xlarge": "https://s3.amazonaws.com/splitwise/uploads/group/default_avatars/avatar-ruby2-house-500px.png",
                    "large": "https://s3.amazonaws.com/splitwise/uploads/group/default_avatars/avatar-ruby2-house-200px.png",
                    "medium": "https://s3.amazonaws.com/splitwise/uploads/group/default_avatars/avatar-ruby2-house-100px.png",
                    "small": "https://s3.amazonaws.com/splitwise/uploads/group/default_avatars/avatar-ruby2-house-50px.png"
                    },
                    "custom_avatar": true,
                    "cover_photo": {
                    "xxlarge": "https://s3.amazonaws.com/splitwise/uploads/group/default_cover_photos/coverphoto-ruby-1000px.png",
                    "xlarge": "https://s3.amazonaws.com/splitwise/uploads/group/default_cover_photos/coverphoto-ruby-500px.png"
                    },
                    "invite_link": "https://www.splitwise.com/join/abQwErTyuI+12"
                }
        }
    """
    url = f"https://secure.splitwise.com/api/v3.0/get_group/{group_id}"
    response = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
    response.raise_for_status()
            
    group= response.json()["group"]
    return group
