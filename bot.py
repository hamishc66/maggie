import os
import random
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# the genai client automatically detects your GEMINI_API_KEY environment variable
google_client = genai.Client()

class MagicalBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # synchronizes your slash commands across your servers instantly
        await self.tree.sync()
        print("✨ registered all application slash commands! ✨")

bot = MagicalBot()

@bot.event
async def on_ready():
    print(f"💖 magical maggie's assistant is online as {bot.user}!")

# 1. /ai command (themed preppy chat using gemini)
@bot.tree.command(name="ai", description="chat with the preppy magical assistant 💅")
@app_commands.describe(prompt="what do you want to tell maggie?", tts="should maggie speak this out loud?")
async def ai_cmd(interaction: discord.Interaction, prompt: str, tts: bool = False):
    await interaction.response.defer()
    
    system_prompt = (
        "You are 'Magical Maggie's Assistant', a Discord bot. You are super preppy, magic-themed, progressive, "
        "and hilarious. You love shitposting, using excessive emojis (✨, 💖, 🔮, 💅, 💀), and talking like "
        "a hyperactive internet bestie. Keep responses relatively short and extremely funny."
    )
    
    try:
        # standard async client call using the unified google sdk
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=200
            )
        )
        reply = response.text
    except Exception:
        reply = "omg bestie my psychic crystals just short-circuited 💀 hold on a sec"
        
    await interaction.followup.send(content=reply, tts=tts)

# 2. /ermactually command (wikipedia + dictionary + gemini logic synthesis)
@bot.tree.command(name="ermactually", description="nerd out and fact-check something with absolute chaos 🤓")
@app_commands.describe(query="what thing are you fact-checking?", tts="should maggie speak this out loud?")
async def erm_actually_cmd(interaction: discord.Interaction, query: str, tts: bool = False):
    await interaction.response.defer()
    
    wiki_info = "No Wikipedia logs found."
    dict_info = "No official dictionary data found."
    
    async with aiohttp.ClientSession() as session:
        # fetch wikipedia snippet
        try:
            wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={query}&limit=1&format=json"
            async with session.get(wiki_url) as r:
                if r.status == 200:
                    res = await r.json()
                    if len(res) > 2 and res[2]:
                        wiki_info = res[2][0]
        except Exception:
            pass
            
        # fetch free dictionary definition
        try:
            dict_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{query}"
            async with session.get(dict_url) as r:
                if r.status == 200:
                    res = await r.json()
                    if isinstance(res, list) and res[0].get('meanings'):
                        dict_info = res[0]['meanings'][0]['definitions'][0]['definition']
        except Exception:
            pass

    nerd_system = (
        "You are an obnoxious, preppy 'Erm, actually...' fact-checker. You take the Wikipedia and dictionary data "
        "provided, combine it with your AI brain, and construct a highly sarcastic, preppy, know-it-all answer. "
        "Start with '✨ 🤓 Erm, actually... ' and roast or correct the concept using heavy preppy slang and buzzwords."
    )
    user_data = f"Query: {query}\nWiki: {wiki_info}\nDict: {dict_info}"
    
    try:
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_data,
            config=types.GenerateContentConfig(
                system_instruction=nerd_system,
                max_output_tokens=250
            )
        )
        reply = response.text
    except Exception:
        reply = f"✨ 🤓 Erm, actually... my code broke, but wiki says: {wiki_info}"
        
    await interaction.followup.send(content=reply, tts=tts)

# 3. /tarot command
@bot.tree.command(name="tarot", description="pull a preppy tarot vibe check 🔮")
async def tarot_cmd(interaction: discord.Interaction):
    cards = [
        "The Fool ✨ (literal main character energy, go do something unhinged)",
        "The Magician 🔮 (you are manifesting so hard right now, it's scary)",
        "The Tower 💀 (omg massive vibe emergency incoming, brace yourself)",
        "The Lovers 💖 (either a massive crush or a perfectly iced tea is on the way)",
        "Death 💅 (slay! time for a total aesthetic reset, out with the old)",
        "The Star 🌟 (unbothered, moisturized, in your lane, thriving)"
    ]
    await interaction.response.send_message(f"🔮 **your magical card:** {random.choice(cards)}")

# 4. /fortune command
@bot.tree.command(name="fortune", description="predict your magical future 🌟")
async def fortune_cmd(interaction: discord.Interaction):
    fortunes = [
        "i foresee a very expensive iced drink in your future. 🍵✨",
        "the stars say you will post a legendary meme today. 💀",
        "manifesting an absolute win for you, bestie! 💅🔮",
        "vibe check: fully immaculate. keep causing chaos. 💖",
        "the spirits are currently ghosting me, check back later. ✨"
    ]
    await interaction.response.send_message(random.choice(fortunes))

# passive reactions
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
        
    content = message.content.lower()
    if "i hate this" in content:
        if random.random() < 0.4:
            await message.channel.send("omg stop being such a buzzkill, it's literally just a ✨vibe✨ issue, bestie. 💅")
    elif "magic" in content:
        if random.random() < 0.3:
            await message.channel.send("did someone say magic?! 🔮✨ manifest it queen!!")

    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))