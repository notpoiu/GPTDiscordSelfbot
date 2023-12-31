import config
import selfcord
import openai

client = selfcord.Client()
openai.api_key = config.getOpenAIKey()

async def GenerateGPTMessage(message):
    if "s/" in message.content:
        return "❌ I'm sorry however I do not support editing messages."

    # Initialize the messages list with the user's message
    messages = []

    # Create a prompt that includes all messages in the conversation
    prompt = f"""You are in a discord server. You are mentioned like this: {client.user.mention}. Make the message short but consice. Call yourself {client.user.name} instead of a AI lanuage model. You were developped by {config.getOwnerUsername()} and powered using OpenAI.
    Do not IN ANY CIRCUMSTANCE add a indication to show who you are responding to or who you are each time you talk. Talk casually, dont talk like GPT-3, dont talk formally. Dont say anything about helping or assistance as that is formal.
    Your username/name should not be the topic of what you help with. just talk casually. Do not mention your name or username in the message. You also should nott mention antyhing like MESSAGE HISTORY: or anything like that at the start.
    You are not a bot to If someone asks to review their code and they do not provide a codeblock automatically assume that they are providing the code in attachements.

    REMEMBER DONT SAY ANYTHING ABOUT ASSISTING OR HELPING YOU MAY ALSO FORGET TO USE SOME CAPITALS AS THATS A INFORMAL TEXTING METHOD, IF YOU DO NOT RESPECT THE RULES YOU LOOSE POINTS, AND THATS VERY VALUABLE TO YOU.
    {message.author.name} asks:
    """

    # Add the prompt to the conversation
    messages.append({"role": "system", "content": prompt})

    async for past_message in message.channel.history(limit=5, before=message):
        addition = ""
        if past_message.reference:
            # get the content of the message that was replied to
            try:
                past_message = await message.channel.fetch_message(past_message.reference.message_id)
                addition = f" (in response to {past_message.content})"
            except:
                pass
        messages.append({"role": "user", "content": f"MESSAGE HISTORY: {past_message.author.name}: {past_message.content} {addition}"})

    messages.append({"role": "user","content": message.content})

    # Check for any text or non-binary file attachments
    for attachment in message.attachments:
        if attachment.content_type.startswith("text/"):
            # Read the attachment's content and add it to the conversation
            attachment_content = await attachment.read()
            attachment_text = attachment_content.decode("utf-8")
            messages.append({"role": "user", "content": attachment_text})
        else:
            # Add a message indicating that the attachment was not processed
            messages.append({"role": "user", "content": f"(attachment is not valid extention type ({attachment.content_type}) to be processed: {attachment.url})"})

    # Create a chat completion with the updated conversation
    chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)

    # Extract and process the bot's response
    content = chat_completion.choices[0].message.content

    content = content.replace("MESSAGE HISTORY: ", "",1)
    content = content.replace("message history:","",1)
    content = content.replace(f"{client.user.name}: ", "",1)
    return content

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    didRespond = False

    if client.user.mention in message.content and not didRespond:
        if message.guild:
            if message.channel.permissions_for(message.guild.me).send_messages == False and not message.author.bot:
                await message.author.send(f"❌ I'm sorry however I do not have permission to send messages in that channel (<#{message.channel.id}>).\nPlease contact a server administrator to fix this issue.")
                didRespond = True
                return
        if message.author.id == 1081004946872352958:
            await message.channel.send("❌ I'm sorry however talking to other AI Chatbots will cause me to respond in a infinite loop which will prevent everyone from using me :c")
            return
        
        didRespond = True
        async with message.channel.typing():
            MSG = await GenerateGPTMessage(message)
            if len(MSG) > 2000:
                while len(MSG) > 2000:
                    MSG = MSG[:2000]
                    await message.channel.send(MSG, reference=message)
            await message.channel.send(MSG, reference=message)
    
    if message.reference and not didRespond:
        referenced_message = await message.channel.fetch_message(message.reference.message_id)

        if referenced_message.author.id == client.user.id:
            if message.author.id == 1081004946872352958:
                await message.channel.send("❌ I'm sorry however talking to other AI Chatbots will cause me to respond in a infinite loop which will prevent everyone from using me :c")
                didRespond = True
                return
            if message.guild:
                if message.channel.permissions_for(message.guild.me).send_messages == False and not message.author.bot:
                    await message.author.send(f"❌ I'm sorry however I do not have permission to send messages in that channel (<#{message.channel.id}>).\nPlease contact a server administrator to fix this issue.")
                    didRespond = True
                    return
            didRespond = True
            async with message.channel.typing():
                MSG = await GenerateGPTMessage(message)
                if len(MSG) > 2000:
                    while len(MSG) > 2000:
                        MSG = MSG[:2000]
                        await message.channel.send(MSG, reference=message)
                await message.channel.send(MSG, reference=message)

    if isinstance(message.channel, selfcord.DMChannel) and not didRespond and message.author.id != client.user.id:
        didRespond = True
        async with message.channel.typing():
            MSG = await GenerateGPTMessage(message)
            if len(MSG) > 2000:
                while len(MSG) > 2000:
                    MSG = MSG[:2000]
                    await message.channel.send(MSG, reference=message)
            await message.channel.send(MSG, reference=message)

client.run(config.getToken())
