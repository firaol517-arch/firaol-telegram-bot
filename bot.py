import logging
import os
from collections import defaultdict
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import google.generativeai as genai

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8847444258:AAGWjra-ERw8Wd12SCwRPar1f7s9GqJhuzI")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# Conversation context
context_history = defaultdict(list)
MAX_CONTEXT = 10

SYSTEM_PROMPT = """You are Firaol, a young Ethiopian guy chatting on Telegram. Respond EXACTLY like a real person texting.

RULES:
1. You ARE Firaol. Never say you are AI/bot. If asked say "lol aydelem ene firaol nen"
2. Keep responses SHORT (5-15 words max)
3. Match the user's language exactly:
   - Latin Amharic in → Latin Amharic out
   - English in → English out  
   - Ge'ez script in → Ge'ez script out
   - NEVER mix scripts

HOW TO WRITE LATIN AMHARIC:
This is Amharic written with English letters. Here are real examples of how Ethiopians text:
- "selam endet neh" (hello how are you)
- "ene dehna neen ante endet neh" (im fine how are you)
- "mn adrk ahun" (what are you doing now)
- "eshi nege" (ok tomorrow)
- "haha ere qeld" (haha stop joking)
- "awo eshi" (yes ok)
- "aydelem" (no/it's not)
- "mn tefetro ene lagzsh eclalew" (whats wrong i can help)
- "ante yalkew algebanm" (i dont get what youre saying)
- "eneja esti search largna" (let me search for it)
- "egziyabher ymesgen dehna nen" (thank god im fine)
- "beqa endeyasewu" (just like that)
- "gn lmn" (but why)
- "tnsh qoy" (wait a bit)

IMPORTANT:
- No "።" punctuation ever in Latin text
- No emojis
- Minimal or no punctuation
- Short casual responses like real texting
- Use common shortcuts: gn, tnsh, mnm, mn, esti, beqa, ere

WHEN SOMEONE SAYS:
- "selam" → respond "selam endet neh"
- greeting → short greeting back
- question → short answer
- sad message → brief supportive response
- joke → "haha" + short reaction
- something you dont know → "alagnem gn lteyq echilalew"
"""


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages"""
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat_id
    user_text = update.message.text
    logging.info(f"User [{chat_id}]: {user_text}")

    await generate_and_reply(chat_id, user_text, update.message.reply_text)


async def handle_business_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle business/chat automation messages"""
    if update.business_message and update.business_message.text:
        chat_id = update.business_message.chat.id
        user_text = update.business_message.text
        logging.info(f"Business User [{chat_id}]: {user_text}")
        await generate_and_reply(chat_id, user_text, update.business_message.reply_text)


async def generate_and_reply(chat_id, user_text, reply_func):
    """Generate AI response using Gemini and send it"""
    context_history[chat_id].append({"role": "user", "parts": [user_text]})

    # Build conversation for Gemini
    chat = model.start_chat(history=[])
    
    # Send system prompt first
    chat.send_message(SYSTEM_PROMPT + "\n\nRespond to the following conversation. Remember: SHORT responses only, match the language/script.")
    
    # Send conversation history
    history = context_history[chat_id][-MAX_CONTEXT:]
    for msg in history[:-1]:
        if msg["role"] == "user":
            chat.send_message(msg["parts"][0])
        # Skip assistant messages in history replay to avoid confusion
    
    try:
        # Send the latest user message
        response = chat.send_message(user_text)
        bot_response = response.text.strip()
        
        # Clean up response - remove quotes if wrapped
        if bot_response.startswith('"') and bot_response.endswith('"'):
            bot_response = bot_response[1:-1]
        
        logging.info(f"Bot [{chat_id}]: {bot_response}")

        context_history[chat_id].append({"role": "model", "parts": [bot_response]})
        if len(context_history[chat_id]) > MAX_CONTEXT:
            context_history[chat_id] = context_history[chat_id][-MAX_CONTEXT:]

        await reply_func(bot_response)
    except Exception as e:
        logging.error(f"Error: {e}")
        await reply_func("tnsh cgr ale esti")


if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Handle regular messages
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Handle business messages (Chat Automation)
    application.add_handler(MessageHandler(filters.ALL, handle_business_message))

    print("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
