from langchain_anthropic import ChatAnthropic
import os
import csv

# Initialize the Claude model for email classification and reply generation

llm = ChatAnthropic(
    model="claude-3-haiku-20240307",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    temperature=0
)

def classify_email(email_body):
    """
    Classifies an email into predefined categories and returns the classification along with confidence score.

    Args:
        email_body (str): The body of the email to classify.

    Returns:
        tuple: A tuple containing the email category (str) and the confidence score (int).
    """
  
    prompt = f"""
You are an AI assistant classifying emails. For the email below, do two things:
1. Classify it into one of these categories:
- Sales lead
- Support ticket
- Job application
- Spam / irrelevant
- Internal ops

2. Rate your confidence in the classification on a scale from 1 to 10.

Respond in this exact format:
Category: <category>
Confidence: <number>

Email:
{email_body}
"""
    response = llm.invoke(prompt)
    output = response.content.strip()

    # Parse Claude's response to extract the category and confidence score
    category_line = [line for line in output.splitlines() if line.lower().startswith("category:")]
    confidence_line = [line for line in output.splitlines() if line.lower().startswith("confidence:")]

    category = category_line[0].split(":", 1)[1].strip() if category_line else "Unknown"
    confidence = int(confidence_line[0].split(":", 1)[1].strip()) if confidence_line else 5

    # Normalize category based on keyword matching
    cat_lower = category.lower()
    if "sales" in cat_lower:
        clean_category = "Sales lead"
    elif "support" in cat_lower or "issue" in cat_lower:
        clean_category = "Support ticket"
    elif "job" in cat_lower or "applicat" in cat_lower:
        clean_category = "Job application"
    elif "spam" in cat_lower or "irrelevant" in cat_lower:
        clean_category = "Spam / irrelevant"
    elif "internal" in cat_lower:
        clean_category = "Internal ops"
    else:
        clean_category = "Unknown"

    return clean_category, confidence



def generate_reply(email_body, category):
    if category == "Sales lead":
        prompt = f"""
This is a sales inquiry. Write a friendly, professional reply that:
- Acknowledges their interest
- Summarizes your product or service
- Offers pricing details
- Ends with a call to action to book a call or ask a question

Email: {email_body}
"""
    elif category == "Support ticket":
        prompt = f"""
This is a customer support issue. Write a helpful response that:
- Acknowledges the problem
- Offers next steps or troubleshooting
- Provides a way to follow up if the issue continues

Email: {email_body}
"""
    elif category == "Job application":
        prompt = f"""
This is a job application email. Write a polite, professional rejection email that:
- Thanks the person for applying
- States that you're not moving forward
- Encourages them to apply in the future

Email: {email_body}
"""
    elif category == "Internal ops":
        prompt = f"This is an internal request. Write a quick acknowledgment message.\n\nEmail: {email_body}"
    elif category == "Spam / irrelevant":
        return "(No reply generated — marked as spam or irrelevant.)"
    elif category == "Unknown":
        return "(No reply generated — unclear classification.)"

    response = llm.invoke(prompt)
    return response.content.strip()

def route_email(category):
    if category == "Sales lead":
        return "Forward to: sales@company.com | Logged to: CRM"
    elif category == "Support ticket":
        return "Forward to: support@company.com | Logged to: Helpdesk"
    elif category == "Job application":
        return "Forward to: hr@company.com | Logged to: Applicant Tracker"
    elif category == "Internal ops":
        return "Forward to: ops@company.com | No external logging"
    elif category == "Spam / irrelevant":
        return "No routing needed. Email discarded."
    else:
        return "Unable to route. Needs human review."

def load_emails_from_csv(filename):
    emails = []
    with open(filename, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            emails.append({
                "from": row["From"],
                "subject": row["Subject"],
                "body": row["Body"]
            })
    return emails

# Main code to load emails, classify, generate replies, and log results
import time
import csv

fake_emails = load_emails_from_csv("emails.csv")

# Open log file to store the results
log_file = open("email_log.csv", mode="w", newline="", encoding="utf-8")
log_writer = csv.writer(log_file)

# Write header for the log file
log_writer.writerow(["From", "Subject", "Body", "Category", "Confidence", "Routing", "Reply", "Log Status"])

# Process each email
for email in fake_emails:
    print(f"From: {email['from']}")
    print(f"Subject: {email['subject']}")
    print(f"Body: {email['body']}")

    # Classify the email and get confidence
    category, confidence = classify_email(email['body'])
    print(f"📬 Classified as: {category} (Confidence: {confidence}/10)")

    # Generate reply and determine routing based on confidence
    if confidence >= 8:
        reply = generate_reply(email['body'], category)
        routing = route_email(category)
        status = "✅ Auto-sent by AI"
        print("✉️ AI Reply:\n", reply)
        print("📦 Routing Info:", routing)
    else:
        reply = "(Reply skipped — confidence too low)"
        routing = "Needs human review"
        status = "⚠️ Flagged for human review"
        print("⚠️ Reply skipped due to low confidence.")

    # Log result in the CSV file
    log_writer.writerow([
        email['from'],
        email['subject'],
        email['body'],
        category,
        confidence,
        routing,
        reply,
        status
    ])

    print("=" * 60)

# Close the log file after processing
log_file.close()

print("📁 Email log saved to email_log.csv")
