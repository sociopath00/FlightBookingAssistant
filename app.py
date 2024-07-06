import os

import dotenv
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from flask import Flask, render_template, request, jsonify
from src.tools import flight_list


# load env
dotenv.load_dotenv("config/.env")

# llm config
llm_config = {"model": "gpt-3.5-turbo", "api_key": os.environ["OPENAI_API_KEY"]}

app = Flask(__name__)

message_history = {
    "flight_booking_agent": [],
    "user_agent": []
}


def save_history(history):
    global message_history
    message_history = history


def get_history():
    global message_history
    return message_history


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    message = request.json["message"]
    print(get_history())

    def should_terminate_user(msg):
        return "tool_calls" not in msg and msg["role"] != "tool"

    user_agent = UserProxyAgent(
        name="user_agent",
        is_termination_msg=should_terminate_user,
        # max_consecutive_auto_reply=2,  # to avoid loops
        human_input_mode="NEVER",
        code_execution_config=False,
        llm_config=False,
        system_message="You are a helpful assistant who interacts with users",
        description="Assistant who interacts with users"
    )

    flight_booking_agent = AssistantAgent(
        name="flight_booking_agent",
        # max_consecutive_auto_reply=2,
        human_input_mode="NEVER",
        llm_config=llm_config,
        system_message="You are helpful assistant who uses custom tools to extracts list of flights using "
                       "source city, destination city and travel date",
        description="You are helpful assistant who extracts list of flights using "
                       "source city, destination city and travel date"
    )

    flight_booking_agent.register_for_llm(name="flight_list",
                                          description="Function to fetch the list of flights between "
                                                      "source city and destination city for a given travel date")(
        flight_list)
    # status_agent = AssistantAgent(
    #     name="flight_booking_agent",
    #     max_consecutive_auto_reply=2,
    #     human_input_mode="NEVER",
    #     llm_config=llm_config,
    #     system_message="You are helpful assistant who helps users to retrieve status based on PNR code"
    # )

    user_agent.register_for_execution(name="flight_list")(flight_list)

    group_chat = GroupChat(agents=[user_agent, flight_booking_agent],
                           messages=[],
                           send_introductions=True,
                           max_round=20)

    group_manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config,
        human_input_mode="NEVER"
    )

    history = get_history()
    flight_booking_agent._oai_messages = {group_manager: history["flight_booking_agent"]}
    user_agent._oai_messages = {group_manager: history["user_agent"]}

    user_agent.initiate_chat(group_manager, message=message, clear_history=False)

    save_history({
        "flight_booking_agent": flight_booking_agent.chat_messages.get(group_manager),
        "user_agent": user_agent.chat_messages.get(group_manager)
    })

    return jsonify(group_chat.messages[-1])


if __name__ == "__main__":
    app.run(debug=True)

