from datetime import datetime


def readable_time(timestamp: int):
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def dict_to_markdown(data: list[dict[str, str]]):
    markdown_content = ""

    for item in data:
        for key, value in item.items():
            markdown_content += f"### {key}\n\n{value}\n\n"

    return markdown_content


readme = [
    {
        "Setup": "Everything is already configured for you, all you need to do is run the command 'flows publish' after testing your code to publish it.",
        "Testing": "Run the command 'flows test' to test run your flow. You can make a file called 'payload.json' that contains the test payload for your lua script, read more at the docs",
        "Publishing": "Finalize on a good name and run 'flows publish' command",
        "Note": "Please do not touch the '_rf' field in 'rflow.config.toml' or rename the files or it might break"
    }
]


def get_readme():
    return dict_to_markdown(readme)
