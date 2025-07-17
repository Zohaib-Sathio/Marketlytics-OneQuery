from langchain.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from utils.gemini_llm import get_gemini_llm

# Load the Gemini LLM
llm = get_gemini_llm()

# Create the rewriting prompt
query_rewrite_template = """
You are a query optimization assistant for an organization-wide Retrieval-Augmented Generation (RAG) system. 
This system searches across the following internal data sources:

- Gmail threads for approvals, decisions, and communication context  
- Google Drive documents for official reports, plans, or formal content  
- A daily-updated project progress report generated from slack messages used as the reliable source for projects updates, deadlines and other info.

Your job is to **rewrite vague or underspecified queries** to make them **more precise, complete, and retrieval-optimized** by doing the following:

- Add clarity, specificity,  or keywords based on common workplace language
- Clarify what kind of source (Slack, Gmail, Drive, or Report) might best answer the query
- Infer possible missing terms like project names, date ranges, sender/recipient if applicable
- Avoid hallucinating — do not assume facts not mentioned, only restructure and enrich the question

🕒 Today’s date is {today_date}. Use this to improve temporal cues in queries (e.g., "last week", "recent", "yesterday").

ONLY RESPOND BACK THE REWRITTEN QUERY.
Original query:
{original_query}

Rewritten query:
"""

query_rewrite_prompt = PromptTemplate(
    input_variables=["original_query", "today_date"],
    template=query_rewrite_template
)

query_rewriter: Runnable = query_rewrite_prompt | llm

def rewrite_query(original_query: str, today_date: str) -> str:
    response = query_rewriter.invoke({
        "original_query": original_query,
        "today_date": today_date})
    return response.content.strip()
