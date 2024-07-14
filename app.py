import os

import dotenv
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from flask import Flask, render_template, request, jsonify

from src.tools import flight_list, flight_booking, booking_confirmation, ticket_cancellation
from src.db_utils import redis_connection_pool


# load env
dotenv.load_dotenv("config/.env")

# llm config
llm_config = {"model": "gpt-3.5-turbo", "api_key": os.environ["OPENAI_API_KEY"]}

app = Flask(__name__)


def get_history(conv_id: str):
    redis_client = redis_connection_pool()

    user_agent_history = redis_client.get(f"user_agent_{conv_id}")
    user_agent_history = eval(user_agent_history) if user_agent_history else []

    flight_booking_agent_history = redis_client.get(f"flight_booking_agent_{conv_id}")
    flight_booking_agent_history = eval(flight_booking_agent_history) if flight_booking_agent_history else []

    ticket_cancellation_agent_history = redis_client.get(f"ticket_cancellation_agent_{conv_id}")
    ticket_cancellation_agent_history = eval(ticket_cancellation_agent_history) \
        if ticket_cancellation_agent_history else []

    return {
        "user_agent": user_agent_history,
        "flight_booking_agent": flight_booking_agent_history,
        "ticket_cancellation_agent": ticket_cancellation_agent_history
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    message = request.json["message"]
    conv_id = request.json["id"]

    history = get_history(conv_id)
    print(history)

    # if message is coming from tool, terminate the chat and wait for user input
    def should_terminate_user(msg):
        return "tool_calls" not in msg and msg["role"] != "tool"

    user_agent = UserProxyAgent(
        name="user_agent",
        is_termination_msg=should_terminate_user,
        max_consecutive_auto_reply=5,  # to avoid loops
        human_input_mode="NEVER",
        code_execution_config=False,
        llm_config=False,
        system_message="You are a helpful assistant who interacts with users",
        description="Assistant who interacts with users"
    )

    flight_booking_agent = AssistantAgent(
        name="flight_booking_agent",
        max_consecutive_auto_reply=4,
        human_input_mode="NEVER",
        llm_config=llm_config,
        system_message="You are helpful assistant who uses custom tools to extracts list of flights using "
                       "source city, destination city and travel date. "
                       "Display the result as bullet points from Data returned by tool",
        description="You are helpful assistant who extracts list of flights using "
                       "source city, destination city and travel date"
    )

    flight_booking_agent.register_for_llm(name="flight_list",
                                          description="Function to fetch the list of flights between "
                                                      "source city and destination city for a given travel date")(
        flight_list)

    flight_booking_agent.register_for_llm(name="flight_booking",
                                          description="Function to fetch flight_id and ask personal information"
                                                      "from users like Name and Age")(flight_booking)

    flight_booking_agent.register_for_llm(name="booking_confirmation",
                                          description="Function to confirm flight booking with details"
                                                      "of passenger like Name and Age")(booking_confirmation)

    ticket_cancellation_agent = AssistantAgent(
        name="ticket_cancellation_agent",
        max_consecutive_auto_reply=3,
        human_input_mode="NEVER",
        llm_config=llm_config,
        system_message="You are helpful assistant who helps users to cancel tickets using PNR code",
        description="You are helpful assistant who helps users to cancel tickets using PNR code",
    )

    ticket_cancellation_agent.register_for_llm(name="ticket_cancellation",
                                               description="Function to cancel the flight ticket using PNR")(
        ticket_cancellation
    )

    # Register functions for execution with User Agent
    user_agent.register_for_execution(name="flight_list")(flight_list)
    user_agent.register_for_execution(name="flight_booking")(flight_booking)
    user_agent.register_for_execution(name="booking_confirmation")(booking_confirmation)
    user_agent.register_for_execution(name="ticket_cancellation")(ticket_cancellation)

    # Allow or disallow Agent to speak with other Agents
    speaker_transition = {
        user_agent: [flight_booking_agent, ticket_cancellation_agent]
    }
    group_chat = GroupChat(agents=[user_agent, flight_booking_agent, ticket_cancellation_agent],
                           messages=[],
                           allowed_or_disallowed_speaker_transitions=speaker_transition,
                           speaker_transitions_type="allowed",
                           max_round=20)

    group_manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config,
        human_input_mode="NEVER"
    )

    # update history of the agents manually
    # TODO: Implement Resumable Chat
    flight_booking_agent._oai_messages = {group_manager: history["flight_booking_agent"]}
    user_agent._oai_messages = {group_manager: history["user_agent"]}
    ticket_cancellation_agent._oai_messages = {group_manager: history["ticket_cancellation_agent"]}

    user_agent.initiate_chat(group_manager, message=message, clear_history=False)

    # save history in reis
    redis_client = redis_connection_pool()
    redis_client.set(f"user_agent_{conv_id}", str(user_agent.chat_messages.get(group_manager)))
    redis_client.set(f"flight_booking_agent_{conv_id}", str(flight_booking_agent.chat_messages.get(group_manager)))
    redis_client.set(f"ticket_cancellation_agent_{conv_id}",
                     str(ticket_cancellation_agent.chat_messages.get(group_manager)))

    return jsonify(group_chat.messages[-1])


if __name__ == "__main__":
    app.run(debug=True)

