from fetch_emails import fetch_and_store_emails
from llm_utils import analyze_email
from reply_generator import generate_reply
from send_email import send_email

def main():
    emails = fetch_and_store_emails()
    for email in emails:
        summary, intent = analyze_email(email['body'])
        if intent == 'reply_needed':
            reply = generate_reply(email['body'], summary, intent)
            send_email(email['sender'], "Re: " + email['subject'], reply)

if __name__ == '__main__':
    main()
