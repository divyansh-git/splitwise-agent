import os
import ollama
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
import requests
from starlette.requests import Request

console=Console()
load_dotenv(".env")        
SECRET=os.getenv("SECRET")       
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("SPLITWISE_API_KEY")
ALLOWED_USERS = os.getenv("ALLOWED_USERS").split(',')
API = f"https://api.telegram.org/bot{TOKEN}"
app = FastAPI()


class Prompt(BaseModel):
    prompt: str

def add_expenses(cost: float, description: str, group_id: int,
                 paid_by_id: int, member_ids: list[int]) -> dict:
    """Add an expense to a Splitwise group, split equally among the given members.

    Args:
        cost: total amount of the expense
        description: what the expense was for
        group_id: id of the group, from groupIdLookup
        paid_by_id: user id of the person who paid, from getGroupDetails
        member_ids: user ids of everyone sharing the cost, including the payer

    Returns:
        Confirmation text, or the error if Splitwise rejected it.
    """
    n = len(member_ids)
    shares = [round(cost / n, 2)] * n
    shares[0] = round(shares[0] + cost - sum(shares), 2)   # absorb rounding

    payload = {"cost": f"{cost:.2f}", "description": description,
               "group_id": group_id, "currency_code": "INR"}

    for i, uid in enumerate(member_ids):
        payload[f"users__{i}__user_id"]    = uid
        payload[f"users__{i}__owed_share"] = f"{shares[i]:.2f}"
        payload[f"users__{i}__paid_share"] = f"{cost:.2f}" if uid == paid_by_id else "0.00"

    data = requests.post("https://secure.splitwise.com/api/v3.0/create_expense",
                         json=payload,
                         headers={"Authorization": f"Bearer {API_KEY}"},
                         timeout=20).json()

    if data.get("errors"):
        return {"error": data["errors"]}
    return {"ok": True, "expense_id": data["expenses"][0]["id"]}

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


# print(prompt)
messages = [
    {"role": "system", "content":
    "You are a Splitwise agent. Use the tools to complete the task. "
    "Resolve group names with groupIdLookup, then get member ids with getGroupDetails, "
    "then call add_expenses. Never stop after gathering information — "
    "always finish by performing the requested action. "
    "Match names case-insensitively on first name."}
]

async def run_agent(prompt:str)->dict:
    messages.append({"role": "user", "content": prompt})
    for step in range(7):
        print("step number: ",step)
        resp = ollama.chat(model="gemma4:latest", messages=messages, tools=list(TOOLS.values()))
        console.print(Panel(Markdown(str(resp)), title="Splitwise", border_style="cyan"))
        print("hello: ",resp.message)
        messages.append(resp.message)
        if not resp.message.tool_calls:
            return resp.message.content
        for call in resp.message.tool_calls:
            name, args = call.function.name, call.function.arguments
            print(f"tool call: {name}{args}")
            try:
                result = TOOLS[name](**args)          # args is a dict, unpack it
            except Exception as e:
                result = {"error": str(e)}
            messages.append({"role": "tool", "tool_name": name, "content": str(result)})
    return result
TOOLS = {"add_expenses": add_expenses,"groupIdLookup":groupIdLookup,"getGroupExpenses":getGroupExpenses,"getFriendsList":getFriendsList,"getGroupDetails":getGroupDetails}

@app.get("/")
def hello_world():
    return "hello world!!"


@app.post("/prompt")
async def entry_point(req:Request, x_telegram_bot_api_secret_token: str = Header(None)):
    print(req.headers)
    print(x_telegram_bot_api_secret_token)
    if x_telegram_bot_api_secret_token != SECRET :
        raise HTTPException(403)
    res = await req.json()
    print(ALLOWED_USERS, res["message"]['from']['id'])
    if str(res["message"]['from']['id']) not in ALLOWED_USERS:
        return {
        "method": "sendMessage",
        "chat_id": res["message"]["chat"]["id"],
        "text": "Bhakkkk !!!",
        }
    print(res["message"])

    # return {}
    message = res["message"]["text"]
    print(message)
    # ---- your agentic workflow goes here ----
    answer = await run_agent(message)
    # -----------------------------------------
    print(answer)
    return {
        "method": "sendMessage",
        "chat_id": res["message"]["chat"]["id"],
        "text": answer,
    }

