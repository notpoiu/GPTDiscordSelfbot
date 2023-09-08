import config
import selfcord
import openai

client = selfcord.Client()
openai.api_key = config.getOpenAIKey()

async def GenerateGPTMessage(message):
    # Initialize the messages list with the user's message
    messages = [{"role": "user", "content": message.content}]

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

    # Create a prompt that includes all messages in the conversation
    prompt = f"""You are in a discord server. You are mentioned like this: {client.user.mention}. Make the message short but consice. Call yourself {client.user.name} instead of a AI lanuage model. You were developped by upio and powered using OpenAI. Do not add a indication to show who you are responding to or who you are each time you talk. Talk casually.
    If someone asks to review their code and they do not provide a codeblock automatically assume that they are providing the code in attachements.
{message.author.name} asks: {message.content}
    """

    # Add the prompt to the conversation
    messages.append({"role": "user", "content": prompt})

    # Create a chat completion with the updated conversation
    chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)

    # Extract and process the bot's response
    content = chat_completion.choices[0].message.content
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
        if message.author.id == 1081004946872352958:
            await message.channel.send("❌ I'm sorry however talking to other AI Chatbots will cause me to respond in a infinite loop which will prevent everyone from using me :c")
            return
        
        didRespond = True
        MSG = await GenerateGPTMessage(message)
        if len(MSG) > 2000:
            while len(MSG) > 2000:
                MSG = MSG[:2000]
                await message.channel.send(MSG, reference=message)
        else:
            await message.channel.send(MSG, reference=message)
    
    if message.reference and not didRespond:
        referenced_message = await message.channel.fetch_message(message.reference.message_id)
        if referenced_message.author.id == 1081004946872352958:
            await message.channel.send("❌ I'm sorry however talking to other AI Chatbots will cause me to respond in a infinite loop which will prevent everyone from using me :c")
            return

        if referenced_message.author.id == client.user.id:
            didRespond = True
            MSG = await GenerateGPTMessage(message)
            if len(MSG) > 2000:
                while len(MSG) > 2000:
                    MSG = MSG[:2000]
                    await message.channel.send(MSG, reference=message)
            else:
                await message.channel.send(MSG, reference=message)

client.run(config.getToken())
