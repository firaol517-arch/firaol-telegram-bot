import logging
import os
from collections import defaultdict
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from openai import OpenAI

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Configuration
TELEGRAM_TOKEN = "8847444258:AAGWjra-ERw8Wd12SCwRPar1f7s9GqJhuzI"
client = OpenAI()

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
    """Generate AI response and send it"""
    context_history[chat_id].append({"role": "user", "content": user_text})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(context_history[chat_id][-MAX_CONTEXT:])

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=60
        )
        bot_response = response.choices[0].message.content
        logging.info(f"Bot [{chat_id}]: {bot_response}")

        context_history[chat_id].append({"role": "assistant", "content": bot_response})
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
