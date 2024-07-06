import os
from autogen import AssistantAgent, UserProxyAgent
import dotenv


dotenv.load_dotenv("../config/.env")
llm_config = {"model": "", "api_key": os.environ["OPENAI_API_KEY"]}


user_agent = UserProxyAgent(
    name="user_agent",
    is_termination_msg=None,
    max_consecutive_auto_reply=2,    # to avoid loops
    human_input_mode="NEVER",
    code_execution_config=False,
    llm_config=False,
    system_message="You are a helpful assistant who interacts with users",
    description="Assistant who interacts with users"
)

# TODO: Implement it later
# flight_information_agent = AssistantAgent(
#     name="flight_information_agent",
#     is_termination_msg=None,
#     max_consecutive_auto_reply=2,
#     human_input_mode="NEVER",
#     llm_config=llm_config,
#     system_message="You are a helpful assistant who helps users to find details about flights using "
#                    "source, destination and date",
#     description="Assistant who helps users to find information about flights"
# )

flight_booking_agent = AssistantAgent(
    name="flight_booking_agent",
    is_termination_msg=None,
    max_consecutive_auto_reply=2,
    human_input_mode="NEVER",
    llm_config=llm_config,
    system_message="You are helpful assistant who helps users to book a flight using source, destination and date"
)

reply = agent.generate_reply(messages=[{"content": "Tell me a joke.", "role": "user"}])
print(reply)