import os
import threading
import random
import discord
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import encryption
import resend
import re
from flask_cors import CORS

resend.api_key = "re_it7Wdhrt_FBVYCLzNkDM7fQLdLRqpE1iS"

def validate_credit_card(card_number: str) -> bool:
    card_number = card_number.replace(" ", "").replace("-", "")
    
    # Convert string to list of integers
    digits = [int(d) for d in card_number]
    
    # Reverse the digits
    digits.reverse()
    
    # Calculate checksum
    total = 0
    for i, digit in enumerate(digits):
        if i % 2 == 1:  # Double every second digit from the right
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
        
    # Valid if total is divisible by 10
    return total % 10 == 0

load_dotenv()

TOKEN = os.getenv("DISCORD_KEY")
PASSWORD = os.getenv("ENCRYPTION_KEY")
CHANNEL_ID = 1514787612722728990
# Flask app
app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "bot": str(client.user) if client.user else "not logged in"
    })
@app.route("/order", methods=["POST"])
def upload():
    text = request.get_data(as_text=True)
    if not text or not text.strip():
        return jsonify({"error": "empty body"}), 400
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        return jsonify({"error": "channel not found"}), 500
    # Validate credit card BEFORE doing anything else
    match = re.search(r'(\d{4}(?: \d{4}){3})', text)
    if match:
        cc = match.group(1)
        if not validate_credit_card(cc):
            return jsonify({"status": "invalid data"}), 400
    # Only encrypt + send AFTER all validation passes
    encrypted = encryption.encrypt(text, PASSWORD)
    def send_message():
        client.loop.create_task(
            channel.send(f"NEW ORDER: ||{encrypted}||")
        )
    client.loop.call_soon_threadsafe(send_message)
    return jsonify({"status": "sent"}), 200


def run_flask():
    app.run(host="0.0.0.0", port=5000)


# Discord bot
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.reference:
        if "fufill" in message.content:
            parent = await message.channel.fetch_message(message.reference.message_id)
            content = parent.content
            content = content.replace("||", "").replace("NEW ORDER: ", "")
            
            decrypted = encryption.decrypt(content, PASSWORD)
            parts = decrypted.split(":")

            fufillmentaction = message.content.replace("fufill ", "", 1).strip().split(":", 1)

            username = fufillmentaction[0]
            password = fufillmentaction[1]

            if len(parts) >= 7:
                email = parts[-1]
                r = resend.Emails.send({
                    "from": "onboarding@resend.dev",
                    "to": email,
                    "subject": "✅ Order Delivered - Hydra Accounts",
                    "html": f"""
                    <div style="font-family: Arial, sans-serif; background:#f4f4f4; padding:40px;">
                        <div style="max-width:600px; margin:0 auto; background:white; border-radius:12px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.1);">
                            
                            <div style="background:#111827; color:white; padding:24px; text-align:center;">
                                <h1 style="margin:0; font-size:24px;">Hydra Accounts</h1>
                                <p style="margin:8px 0 0; opacity:0.8;">Your order has been delivered</p>
                            </div>

                            <div style="padding:32px;">
                                <p style="font-size:16px; color:#374151;">
                                    Thank you for your purchase! Your account details are below:
                                </p>

                                <div style="background:#f9fafb; border:1px solid #e5e7eb; border-radius:8px; padding:20px; margin:24px 0;">
                                    <p style="margin:0 0 12px;"><strong>Username:</strong> {username}</p>
                                    <p style="margin:0;"><strong>Password:</strong> {password}</p>
                                </div>

                                <p style="font-size:14px; color:#6b7280;">
                                    Please store these credentials securely and change your password if applicable.
                                </p>

                                <p style="margin-top:24px; color:#374151;">
                                    Thank you for choosing <strong>Hydra Accounts</strong>!
                                </p>
                            </div>

                            <div style="background:#f9fafb; padding:16px; text-align:center; color:#6b7280; font-size:12px;">
                                © 2026 Hydra Accounts
                            </div>

                        </div>
                    </div>
                    """
                })
                print(email)


            await message.add_reaction("👍")
        else:
            await message.add_reaction("❌")


if __name__ == "__main__":
    # Start Flask in background thread
    threading.Thread(target=run_flask, daemon=True).start()

    # Start Discord bot
    client.run(TOKEN)
    
