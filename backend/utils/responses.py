# backend/utils/responses.py

# Greetings
GREETING_RESPONSES = [
    "Hello 👋 How can I help you today?",
    "Hi there! What can I do for you?",
    "Greetings! How may I assist you?"
]

# FAQs / FastPaths
FASTPATH_RESPONSES = {
    "company_details": """🏢 Company Information

Name: Mobiloitte Technologies
Founded: 2009
Employees: 250+
Head Office: New Delhi
Website: https://mobiloitte.com
Support: support@mobiloitte.com""",
    
    "working_hours": """🕒 Working Hours

Monday–Friday: 9:30 AM – 6:30 PM
Lunch: 1:00 PM – 2:00 PM
Saturday: Closed
Sunday: Closed""",
    
    "hr_policy": """📜 HR Policy

• Office Conduct
• Attendance
• Dress Code
• Remote Work
• Performance Reviews
• Code of Ethics

For complete policy contact HR.""",
    
    "leave_policy": """🏖 Leave Policy

Annual Leave: 18 Days
Sick Leave: 12 Days
Casual Leave: 6 Days
Maternity Leave: Available

Apply through HR Portal.""",
    
    "contact_hr": """📞 Contact HR

Email: hr@company.com
Phone: +91 98765 43210
Portal: hr.company.com""",
    
    "help": """❓ Help & Commands

I can help you with:
- Company Details
- HR Policies
- Leave Rules
- Office Hours
- Careers & Jobs

Just ask!""",
    
    "careers": """💼 Careers

We are currently hiring for:
- Software Engineer (Frontend)
- Product Designer
- Data Scientist

Visit our careers page at careers.company.com to apply.""",
    
    "who_are_you": """🤖 About Me

I am an AI assistant here to help you with:
- Company Information
- HR Policies
- Leave Policies
- Working Hours

Just ask me a question and I'll do my best to help!""",
    
    "how_are_you": """🤖 I'm doing great, thank you for asking! How can I assist you today?"""
}

# Fallback
FALLBACK_MESSAGE = "I'm sorry, I didn't quite understand that. Could you please rephrase or ask something else?"

# Gibberish
GIBBERISH_MESSAGE = "That doesn't look like a valid message. Please type a clear question or greeting."

# Numeric Only
NUMERIC_ONLY_MESSAGE = "I noticed you entered a number. To assist you better, please enter a valid question or command."
