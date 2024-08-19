import selfcord, openai, g4f, json, os
from config import options

client = selfcord.Client()
openai.api_key = options["model_settings"]["billing"]["openai_key"]

# Functions
def sanitize_message(message, author_name):
    new_message = message.strip(f"{client.user.name}: ")
    new_message = new_message.strip(f"{author_name}: ")

    return new_message

async def ask_gpt_for_response(message):
    if "s/" in message.content:
        return "❌ I'm sorry however I do not support editing messages."

    messages = []

    prompt = f"""You are in a discord server.
You are mentioned like this: {client.user.mention}. Make the message short but consice.
Call yourself {client.user.name} instead of a AI lanuage model. You were developped by {options['owner_username']} and powered using OpenAI.
Do not IN ANY CIRCUMSTANCE add a indication to show who you are responding to or who you are each time you talk. Talk casually, dont talk like GPT-3, dont talk formally. Dont say anything about helping or assistance as that is formal.
Your username/name should not be the topic of what you help with. just talk casually. Do not mention your name or username in the message.
You are not a bot to If someone asks to review their code and they do not provide a codeblock automatically assume that they are providing the code in attachements.
REMEMBER DONT SAY ANYTHING ABOUT ASSISTING OR HELPING YOU MAY ALSO FORGET TO USE SOME CAPITALS AS THATS A INFORMAL TEXTING METHOD, IF YOU DO NOT RESPECT THE RULES YOU LOOSE POINTS, AND THATS VERY VALUABLE TO YOU. DONT SAY "USERNAME: " YOU MAY MENTION USERS IN THE PHRASE BUT DO NOT ADD "USER: "
{message.author.name} asks:"""

    messages.append({"role": "system", "content": prompt})

    async for past_message in message.channel.history(limit=options["model_settings"]["chat_history_limit"], before=message):
        addition = ""
        try:
            if past_message.reference:
                past_message = await message.channel.fetch_message(past_message.reference.message_id)
                addition = f" (in response to {past_message.content})"
        except:
            pass
            
        messages.append({"role": "user", "content": f"{past_message.author.name}: {past_message.content} {addition}"})

    messages.append({"role": "user","content": message.content})

    for attachment in message.attachments:
        if attachment.content_type.startswith("text/"):
            attachment_content = await attachment.read()
            attachment_text = attachment_content.decode("utf-8")
            messages.append({"role": "user", "content": attachment_text})
        else:
            messages.append({"role": "user", "content": f"(attachment is not valid extention type ({attachment.content_type}) to be processed: {attachment.url})"})

    if options["model_settings"]["save_conversations"]:
        data = await fetch_data_from_convo(message)

        if len(data) > 0:
            for key, value in data.items():
                messages.append({"role": "user", "content": value["content"]})

    if options["model_settings"]["billing"]["is_free"]:
        chat_completion = await g4f.ChatCompletion.create_async(model=options["model_settings"]["model"], messages=messages)
        return sanitize_message(chat_completion, message.author.name)
    else:
        chat_completion = openai.ChatCompletion.create(model=options["model_settings"]["model"], messages=messages)
        return sanitize_message(chat_completion.choices[0].message.content, message.author.name)

async def send_message_typing(message):
    async with message.channel.typing():
        MSG = await ask_gpt_for_response(message)
        if len(MSG) > 2000:
            while len(MSG) > 2000:
                MSG = MSG[:2000]
                await message.channel.send(MSG, reference=message)
        await message.channel.send(MSG, reference=message)

# Save Functions
async def fetch_data_from_convo(message):
    if not os.path.isfile(f"conversations/{message.channel.id}.json"):
        with open(f"conversations/{message.channel.id}.json", "w") as file:
            file.write("{}")
            file.close()

        return {}

    with open(f"conversations/{message.channel.id}.json", "r") as file:
        data = json.load(file)
        file.close()
    
    return data

async def save_conversations(message):
    if not os.path.exists("conversations"):
        os.makedirs("conversations")
    
    data = await fetch_data_from_convo(message)

    data[message.id] = {
        "author": message.author.id,
        "content": message.content
    }

    with open(f"conversations/{message.channel.id}.json", "w") as file:
        json.dump(data, file)
        file.close()

# Message Handlers
async def handle_pings(message):
    if not (client.user.mention in message.content):
        return False

    if message.guild and not message.channel.permissions_for(message.guild.me).send_messages and not message.author.bot:
        await message.author.send(f"❌ I'm sorry however I do not have permission to send messages in that channel (<#{message.channel.id}>).\nPlease contact a server administrator to fix this issue.")
        return False
    
    await send_message_typing(message)
    await save_conversations(message)
    return True

async def handle_reply(message, did_respond):
    if message.reference and not did_respond:
        referenced_message = await message.channel.fetch_message(message.reference.message_id)

        if referenced_message.author.id == client.user.id:
            if message.guild and message.channel.permissions_for(message.guild.me).send_messages == False and not message.author.bot:
                await message.author.send(f"❌ I'm sorry however I do not have permission to send messages in that channel (<#{message.channel.id}>).\nPlease contact a server administrator to fix this issue.")
                return
            
            await send_message_typing(message)
            await save_conversations(message)

async def handle_direct_messages(message):
    if isinstance(message.channel, selfcord.DMChannel) and message.author.id != client.user.id:
        await send_message_typing(message)
        await save_conversations(message)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    did_respond = await handle_pings(message)
    await handle_reply(message, did_respond)

    await handle_direct_messages(message)

client.run(options["discord_token"])
