import os

import ollama
import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv(".env")               
# GROUP_ID = os.getenv("GROUP_ID")
API_KEY = os.getenv("SPLITWISE_API_KEY")

app = FastAPI()


class ExpenseBody(BaseModel):
    cost: float
    description: str
    groupID: str


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

def groupIdLookup(group_name:str)->str:
    """This tool gets the group ID from the group name.
   
    Args:
        name:The name of the group.
   
    Returns:
        The group ID of the group name or if no group name is present, returns empty string
    """
    url = "https://secure.splitwise.com/api/v3.0/get_groups"
    response = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
    response.raise_for_status()

    groups = response.json()["groups"]
    target = group_name.strip().casefold().replace("\u2019", "'")

    def norm(name: str) -> str:
        return name.strip().casefold().replace("\u2019", "'")

    for group in groups:
        if norm(group["name"]) == target:
            return str(group["id"])

    # # fallback: partial match, so "Nepal trip" still finds "Nepal"
    # for group in groups:
    #     if target in norm(group["name"]) or norm(group["name"]) in target:
    #         return str(group["id"])

    return ""
   
TOOLS = {"add_expenses": add_expenses,"groupIdLookup":groupIdLookup}


@app.get("/")
def hello_world():
    return "hello world!!"


@app.post("/prompt")
def entry_point():
    data = "Add 50 rupees on the splitwise for Milk and Bread to group name Room Blr"
    messages = [
        {
            "role": "system",
            "content": (
                "You are a Splitwise agent. Your job is to make CRUD requests on my "
                "Splitwise account. I will give you tasks in natural language and you "
                "must perform them using the appropriate tool. The only tool currently "
                "available are add_expenses and groupIdLookup"
            ),
        },
        {"role": "user", "content": data},
    ]
    for step in range(50):
        resp = ollama.chat(model="gemma4:latest", messages=messages, tools=list(TOOLS.values()))
        print("response: ", resp.message)
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
            print("tool response: ", str(result))
    return "Done processing"