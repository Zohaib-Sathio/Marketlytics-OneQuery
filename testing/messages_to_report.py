
BASE_PROMPT = """
You are a senior project analyst reviewing a Slack conversation thread to extract accurate and detailed progress over time.

Your job is to:
1. Identify and summarize each meaningful project update or decision.
2. Capture deadlines, milestones, blockers, and next steps.
3. Update or correct previously mentioned info if the newer message provides clarification.
4. Structure the report in chronological order, building one section at a time.
5. Do NOT repeat earlier points unless they were modified or clarified.
6. Remove the unnecessary points.
7. Keep updating the previous report with new updates.
8. If something was not ready or not working and now it is working, then remove the not working part and just add the confirmation of its working.
9. Do not include userids, usernames or links to the report.

Use bullet points, structure by date or topic, and keep it formal, clear, and neutral in tone. This is meant to be read by stakeholders and decision-makers.
"""


import json

with open("reversed_slack_messages.json", "r", encoding="utf-8") as f:
    messages = json.load(f)


def chunk_messages(messages, chunk_size=20):
    """Break messages into equal-sized chunks for processing."""
    for i in range(0, len(messages), chunk_size):
        yield messages[i:i + chunk_size]

def build_prompt(previous_report: str, chunk: list):
    message_block = "\n".join(
        f"{m['ts']} - {m['text']}" for m in chunk
    )
    prompt = f"""{BASE_PROMPT}

Here is the existing project summary (if any):
{previous_report}

Now, continue the report using the new Slack messages:
{message_block}

Return ONLY the updated project report so far. Do not include timestamps in the report. No extra response.
"""
    return prompt


from utils.gemini_llm import get_gemini_llm

llm = get_gemini_llm()

def generate_project_report(messages):
    report = ""  # The progressive report
    count = 0
    for chunk in chunk_messages(messages, chunk_size=20):
        prompt = build_prompt(report, chunk)
        result = llm.invoke(prompt)
        count += 1
        print(f'{count} iteration result.')
        # print(result.content)
        # print('*'*25)
        report = result.content  # Update report cumulatively
    return report


final_report = generate_project_report(messages)

print(f"Total length of text: ", len(final_report))

with open("final_project_report_2.txt", "w", encoding="utf-8") as f:
    f.write(final_report)


print("✅ Project report saved.")





