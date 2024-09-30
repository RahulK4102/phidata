from phi.agent import Agent, RunResponse  # noqa
from phi.model.cohere import CohereChat
from phi.tools.yfinance import YFinanceTools

agent = Agent(
    model=CohereChat(id="command-r-08-2024"),
    tools=[YFinanceTools(company_info=True, stock_fundamentals=True,)],
    show_tool_calls=True,
    debug_mode=True,
    markdown=True,
)

# Get the response in a variable
# run: RunResponse = agent.run("What is the stock price of NVDA and TSLA")
# print(run.content)

# Print the response on the terminal
agent.print_response("Give me in-depth analysis of NVDA and TSLA")
