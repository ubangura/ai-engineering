import json

from messaging import add_assistant_message, add_user_message, chat, text_from_message


def generate_dataset():
    prompt = """
    Generate an evaluation dataset for a prompt evaluation. The dataset will be used to evaluate prompts
    that generate Python, JSON, or Regex specifically for AWS-related tasks. Generate an array of JSON objects,
    each representing a task that requires Python, JSON, or a Regex to complete.
    
    Example output:
    ```json
    [
        {
          "task": "Description of task",
          "format": "Python"
          "solution_criteria": "Key criteria for evaluating the solution" 
        },
        ...additional
    ]
    ```

    * Focus on tasks that can be solved by writing a single Python function, a single JSON object, or a regular expression.
    * Focus on tasks that do not require writing much code

    Please generate 3 objects.
    """

    messages = add_user_message([], prompt)
    messages = add_assistant_message(messages, "```json")
    text = text_from_message(chat(messages, max_tokens=1000, stop_sequences=["\n```"]))
    return json.loads(text)


dataset = generate_dataset()

with open("data/dataset.json", "w") as f:
    json.dump(dataset, f, indent=2)
