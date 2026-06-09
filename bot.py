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

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("🚨 container alert: missing GOOGLE_API_KEY or GEMINI_API_KEY variable!")

google_client = genai.Client(api_key=api_key)

# dynamic loader for the bad words file
def load_banned_words():
    if os.path.exists("bad.txt"):
        with open("bad.txt", "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if line.strip()][^1]
    return []

class MagicalBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True # lets maggie see server members for the coachella lineup
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("✨ registered all application commands! ✨")

bot = MagicalBot()

@bot.event
async def on_guild_join(guild):
    owner = guild.owner or await bot.fetch_user(guild.owner_id)
    try:
        embed = discord.Embed(
            title="✨ MAGICAL MAGGIE'S ASSISTANT ✨",
            description=(
                "oK BESITE IM SETTING UP MY TAAROT CARDS, YOU WILL RECIEVE A TUTORIAL IN THE SEVRER SOON 🔮\n\n"
                "all commands use modern slash interactions! 💅"
            ),
            color=discord.Color.from_rgb(255, 105, 180)
        )[^2]
        embed.add_field(name="💅 drama & manipulation", value="`/cancel`, `/gaslight`, `/gatekeep`, `/girlboss`", inline=False)
        embed.add_field(name="🔮 unhinged magic", value="`/starbucks_order`, `/coachella_lineup`, `/spiritual_gossip`, `/realign_chakras`", inline=False)
        embed.add_field(name="🔮 essentials", value="`/ai`, `/ermactually`, `/vibecheck`, `/aura`, `/slaydar`, `/manifest`, `/crystals`, `/potion`, `/bestiematch`, `/manifestation_circle`, `/hex`, `/tarot`, `/fortune`, `/horoscope`", inline=False)
        await owner.send(embed=embed)
    except Exception as e:
        print(f"could not dm owner: {e}")

@bot.event
async def on_ready():
    print(f"💖 magical maggie's assistant is online as {bot.user}!")

# --- 💅 NEW SOCIAL MANIPULATION & DRAMA COMMANDS ---

@bot.tree.command(name="cancel", description="generate a massive public call-out thread or notes app apology 📉")
@app_commands.describe(user="the bestie getting cancelled", reason="what is the drama about?")
async def cancel_cmd(interaction: discord.Interaction, user: discord.Member, reason: str):
    await interaction.response.defer()
    system_prompt = "You are Magical Maggie's Assistant. Generate a dramatic, multi-paragraph, hyper-preppy 'Notes App Apology' or a public call-out on behalf of the user. Use heavy zoomer slang, toxic positivity, and fake accountability. Keep it hilarious."
    try:
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"cancel {user.display_name} because {reason}",
            config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=300)
        )
        reply = response.text
    except Exception: reply = "my cancellation database is lagging 💀"
    await interaction.followup.send(content=f"📢 **PUBLIC STATEMENT REGARDING {user.mention}:**\n\n{reply}")

@bot.tree.command(name="gaslight", description="completely deny reality on behalf of a situation 🌀")
@app_commands.describe(user="who are we gaslighting?", statement="what reality are we rewriting?")
async def gaslight_cmd(interaction: discord.Interaction, user: discord.Member, statement: str):
    await interaction.response.defer()
    system_prompt = "You are Magical Maggie's Assistant. Write a short, highly manipulative but hilarious reply telling the target user that they are entirely crazy, imagining things, and that their bad vibes are literally damaging the spiritual timeline. Never admit the truth."
    try:
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"gaslight {user.display_name} about {statement}",
            config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=200)
        )
        reply = response.text
    except Exception: reply = "spiritual manipulation system offline 💀"
    await interaction.followup.send(content=f"{user.mention} {reply}")

@bot.tree.command(name="gatekeep", description="explain why someone isn't cool or progressive enough for a topic ❌")
@app_commands.describe(topic="what are we gatekeeping?")
async def gatekeep_cmd(interaction: discord.Interaction, topic: str):
    await interaction.response.defer()
    system_prompt = "You are Magical Maggie's Assistant. Write a preppy, sardonically snobby speech explaining why the general public (and specifically the person asking) is completely unaligned and uncool, meaning they are banned from enjoying or talking about the specified topic."
    try:
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"gatekeep {topic}",
            config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=200)
        )
        reply = response.text
    except Exception: reply = "vibe filtering error 💀"
    await interaction.followup.send(content=f"❌ **URGENT NOTICE REGARDING {topic.upper()}:**\n\n{reply}")

@bot.tree.command(name="girlboss", description="generate an unhinged daily rise-and-grind routine 💅")
async def girlboss_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    system_prompt = "You are Magical Maggie's Assistant. Generate a funny, progressive, totally chaotic daily schedule for a 'girlboss'. Include things like drinking multiple iced matchas, manifesting tax evasion, fighting on twitter, and spiritual maintenance. Format it beautifully with bullet points."
    try:
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents="give me a daily routine",
            config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=250)
        )
        reply = response.text
    except Exception: reply = "the grind never stops but my system did 💀"
    await interaction.followup.send(content=f"💅 **DAILY ACCELERATION ROUTINE** 📈\n\n{reply}")

# --- 🔮 NEW UNHINGED MAGIC & POP CULTURE COMMANDS ---

@bot.tree.command(name="starbucks_order", description="brew a chaotic 15-ingredient magical drink order ☕")
async def starbucks_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    system_prompt = "You are Magical Maggie's Assistant. Invent a hyper-complicated, completely ridiculous 15-ingredient custom Starbucks order that sounds highly aesthetic but completely impossible or disgusting. Combine real syrup adjustments with magical elements like 'scorpio tears' or 'astral ice'."
    try:
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents="make an overcomplicated order",
            config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=200)
        )
        reply = response.text
    except Exception: reply = "the barista rejected your vibes 💀"
    await interaction.followup.send(content=f"🍵 **YOUR SPIRITUAL CONCOCTION:**\n\n{reply}")

@bot.tree.command(name="coachella_lineup", description="generate a chaotic music festival poster featuring server members 🎪")
async def coachella_cmd(interaction: discord.Interaction):
    members = [m.display_name for m in interaction.guild.members] if interaction.guild else []
    if len(members) < 3:
        members += ["Dehydrated Scorpio", "Iced Matcha Monster", "Aura Deprived Flop"]
    
    headliner1 = random.choice(members)
    headliner2 = random.choice(members)
    
    reply = (
        f"🎪 **COACHELLA: MAGICAL BESTIES EDITION** 🎪\n\n"
        f"🔥 **MAIN HEADLINERS:**\n"
        f"• **{headliner1}** (performing their viral hit *'vibe check emergency'*)\n"
        f"• **{headliner2}** (live acoustic notes-app apology set)\n\n"
        f"🎵 **SUB-STAGE ACTS:**\n"
        f"Progressive Tax Evasion, Slowed+Reverb Astral Crying, Iced Chai Metalcore, and The Matcha Manifestation Project. 💅"
    )
    await interaction.response.send_message(reply)

@bot.tree.command(name="spiritual_gossip", description="spill some fake astronomical tea about the solar system 🌟")
async def gossip_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    system_prompt = "You are Magical Maggie's Assistant. Write a quick piece of gossip talking about planets and stars as if they are high school drama characters. (e.g., 'venus is talking mad shit about mars behind its back'). Use massive preppy slang."
    try:
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents="spill space tea",
            config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=150)
        )
        reply = response.text
    except Exception: reply = "the cosmos are acting silent right now 🤫"
    await interaction.followup.send(content=f"🔮 **THE ASTRAL TEA IS SPLASHING:**\n\n{reply}")

@bot.tree.command(name="realign_chakras", description="force a passive-aggressive wellness check on someone 🧘")
@app_commands.describe(user="the bestie who needs to touch grass")
async def realign_cmd(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.send_message(
        f"🧘 **CHAKRA EMERGENCY DETECTION** 🧘\n"
        f"hey {user.mention}, your current typing patterns and general output have been flagged as a total spiritual hazard. "
        f"please take a deep breath, go order an expensive iced tea, and stop projecting your internal un-alignment onto the chat. counting to ten starts now! 🔮💅"
    )

# --- 📦 REST OF FOUNDATIONAL COMMANDS RETAINED ---

@bot.tree.command(name="ai", description="chat with the preppy magical assistant 💅")
@app_commands.describe(prompt="what do you want to tell maggie?", tts="should maggie speak this out loud?")
async def ai_cmd(interaction: discord.Interaction, prompt: str, tts: bool = False):
    await interaction.response.defer()
    system_prompt = "You are 'Magical Maggie's Assistant'. You are super preppy, magic-themed, progressive, hilarious, and love shitposting. Keep responses short and chaotic."
    try:
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=200)
        )
        reply = response.text
    except Exception: reply = "crystals short-circuited 💀"
    await interaction.followup.send(content=reply, tts=tts)

@bot.tree.command(name="ermactually", description="nerd out and fact-check something with precision 🤓")
@app_commands.choices(source=[
    app_commands.Choice(name="AI Summary", value="ai"), app_commands.Choice(name="Google Search Link", value="google"),
    app_commands.Choice(name="Wikipedia Summary & Link", value="wikipedia"), app_commands.Choice(name="Dictionary Definition", value="dictionary"),
    app_commands.Choice(name="Urban Dictionary (AI Slang)", value="urban")
])
async def erm_actually_cmd(interaction: discord.Interaction, source: app_commands.Choice[str], query: str, tts: bool = False):
    await interaction.response.defer()
    source_type = source.value
    if source_type == "ai":
        try:
            res = await google_client.aio.models.generate_content(
                model="gemini-2.5-flash", contents=query,
                config=types.GenerateContentConfig(system_instruction="You are an obnoxious, preppy 'Erm, actually...' fact-checker.", max_output_tokens=250)
            )
            reply = f"✨ 🤓 **Erm, actually...** {res.text}"
        except Exception: reply = "brain shorted out 💀"
    elif source_type == "google":
        reply = f"✨ 🤓 **Erm, actually...** search it yourself: https://www.google.com/search?q={query.replace(' ', '+')} 💅"
    elif source_type == "wikipedia":
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://en.wikipedia.org/w/api.php?action=opensearch&search={query}&limit=1&format=json") as r:
                res = await r.json()
                reply = f"✨ 🤓 **Erm, actually...** wikipedia says:\n> {res[2][0]}\n{res[3][0]}" if len(res) > 2 and res[2] else "wikipedia has no record of this flop."
    elif source_type == "dictionary":
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{query}") as r:
                res = await r.json()
                reply = f"✨ 🤓 **Erm, actually...** definition: *\"{res[0]['meanings'][0]['definitions'][0]['definition']}\"*" if r.status == 200 else "not a real word bestie 💀"
    elif source_type == "urban":
        try:
            res = await google_client.aio.models.generate_content(
                model="gemini-2.5-flash", contents=query,
                config=types.GenerateContentConfig(system_instruction="Invent a fake Urban Dictionary entry using extreme zoomer slang.", max_output_tokens=250)
            )
            reply = f"✨ 🔮 **Urban Dictionary: Maggie Edition** 💅\n\n{res.text}"
        except Exception: reply = "slang engine broke 💀"
    await interaction.followup.send(content=reply, tts=tts)

@bot.tree.command(name="vibecheck", description="run an advanced psychic check on someone 🔮")
async def vibecheck_cmd(interaction: discord.Interaction, user: discord.Member = None):
    t = user or interaction.user
    score = random.randint(1, 10)
    comments = ["trash energy. 💀", "lacking sparkles. 💅", "filler episode. 🔮", "immaculate energy. ✨", "cosmic greatness!! 🌟"]
    c = comments[0] if score <= 3 else comments[1] if score <= 5 else comments[2] if score <= 7 else comments[3] if score <= 9 else comments[4]
    await interaction.response.send_message(f"🔮 **VIBE CHECK FOR {t.mention}:** {score}/10\n> {c}")

@bot.tree.command(name="aura", description="calculate shifts in aura points 📉📈")
async def aura_cmd(interaction: discord.Interaction, action: str, user: discord.Member = None):
    t = user or interaction.user
    p = random.choice([+500, +1000, +50000, -200, -1500, -1000000])
    await interaction.response.send_message(f"✨ **AURA REPORT** ✨\n{t.mention} updated for: *\"{action}\"*\n\n**Result:** `+{p:,}` points! 💅" if p > 0 else f"✨ **AURA REPORT** ✨\n{t.mention} updated for: *\"{action}\"*\n\n**Result:** `{p:,}` points! 💀")

@bot.tree.command(name="slaydar", description="scan to see if someone is slaying 🔎")
async def slaydar_cmd(interaction: discord.Interaction, user: discord.Member = None):
    t = user or interaction.user
    await interaction.response.send_message(f"🔎 **SLAY-DAR SCANNED {t.mention}:** {random.choice(['SLAYING 💅💖', 'A TOTAL FLOP 💀❌', 'BOBBY PIN ENERGY 🔮'])}")

@bot.tree.command(name="manifest", description="manifest your wildest desires into reality ✨")
async def manifest_cmd(interaction: discord.Interaction, desire: str):
    await interaction.response.defer()
    try:
        res = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash", contents=desire,
            config=types.GenerateContentConfig(system_instruction="Generate a hyper-preppy manifestation ritual.", max_output_tokens=200)
        )
        reply = res.text
    except Exception: reply = "universe is busy 💀"
    await interaction.followup.send(content=reply)

@bot.tree.command(name="crystals", description="pull a dynamic daily crystal reading 💎")
async def crystals_cmd(interaction: discord.Interaction):
    stones = ["Moldavite 🟢 (chaotic nuclear destruction incoming 💀)", "Rose Quartz 🌸 (immaculate matching energy 💅)", "Amethyst 🔮 (calm down, you're doing too much.)", "Clear Quartz ❄️ (vibe amplification active ✨)"]
    await interaction.response.send_message(f"💎 **your cosmic crystal today is:** {random.choice(stones)}")

@bot.tree.command(name="potion", description="brew an exotic magic potion 🧪")
async def potion_cmd(interaction: discord.Interaction):
    potions = ["✨ **Iced Matcha Elixir** - grants `+1,500` aura points.", "💀 **Liquid Cancellation** - drops to `0` aura.", "🔮 **Starbucks Psychic Brew** - track your crush ☕"]
    await interaction.response.send_message(f"🔮 **you brewed:** {random.choice(potions)}")

@bot.tree.command(name="bestiematch", description="scan soul alignment 🔎")
async def bestiematch_cmd(interaction: discord.Interaction, bestie: discord.Member):
    compat = random.randint(1, 100)
    v = "toxic biohazard 💀" if compat < 30 else "bobby pin energy 🔮" if compat < 65 else "literal twin flames 💖💅"
    await interaction.response.send_message(f"🔎 **BESTIE SCANNER:**\n🔥 {interaction.user.mention} x {bestie.mention} = **{compat}%**!\n> **Verdict:** {v}")

@bot.tree.command(name="manifestation_circle", description="open a manifestation vortex 🌀")
async def manifestation_circle_cmd(interaction: discord.Interaction, desire: str):
    await interaction.response.send_message(f"🌀 **VORTEX OPENED** 🌀\n{interaction.user.mention} is manifesting: **\"{desire}\"** ✨\n\nREACT WITH ✨ OR 🔮!")

@bot.tree.command(name="hex", description="cast a minor curse 🪄")
async def hex_cmd(interaction: discord.Interaction, enemy: discord.Member):
    curses = ["may their coffee taste like grass.", "may their phone charger only work at a 45-degree angle."]
    await interaction.response.send_message(f"🪄 **HEX CAST ON {enemy.mention}:**\n> \"{random.choice(curses)}\" 💅🔮")

@bot.tree.command(name="horoscope", description="fabricated preppy prediction 🌟")
@app_commands.choices(sign=[app_commands.Choice(name="Aries", value="aries"), app_commands.Choice(name="Taurus", value="taurus"), app_commands.Choice(name="Gemini", value="gemini"), app_commands.Choice(name="Cancer", value="cancer"), app_commands.Choice(name="Leo", value="leo"), app_commands.Choice(name="Virgo", value="virgo"), app_commands.Choice(name="Libra", value="libra"), app_commands.Choice(name="Scorpio", value="scorpio"), app_commands.Choice(name="Sagittarius", value="sagittarius"), app_commands.Choice(name="Capricorn", value="capricorn"), app_commands.Choice(name="Aquarius", value="aquarius"), app_commands.Choice(name="Pisces", value="pisces")])
async def horoscope_cmd(interaction: discord.Interaction, sign: app_commands.Choice[str]):
    await interaction.response.defer()
    try:
        res = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash", contents=sign.name,
            config=types.GenerateContentConfig(system_instruction="Generate a preppy horoscope.", max_output_tokens=200)
        )
        reply = res.text
    except Exception: reply = "stars are unaligned 🌟"
    await interaction.followup.send(content=f"🌟 **{sign.name.upper()} HOROSCOPE** 🔮\n\n{reply}")

@bot.tree.command(name="tarot", description="tarot vibe check 🔮")
async def tarot_cmd(interaction: discord.Interaction):
    cards = ["The Fool ✨ (main character energy)", "The Tower 💀 (vibe emergency)", "Death 💅 (slay! aesthetic reset)"]
    await interaction.response.send_message(f"🔮 **your magical card:** {random.choice(cards)}")

@bot.tree.command(name="fortune", description="predict future 🌟")
async def fortune_cmd(interaction: discord.Interaction):
    fortunes = ["expensive iced drink incoming. 🍵✨", "legendary meme day. 💀", "immaculate vibes. 💖"]
    await interaction.response.send_message(random.choice(fortunes))

# 💬 INTERACTIVE FILTERS & CHAT SHITPOSTING
@bot.event
async def on_message(message):
    if message.author == bot.user: return
    content = message.content.lower()
    
    # 🚨 DYNAMIC BAD-WORD OBLITERATOR FROM TEXT FILE
    banned_list = load_banned_words()
    if any(word in content for word in banned_list):
        try: await message.delete()
        except discord.Forbidden: pass
        await message.channel.send(f"🚨 **OMG CANCELLED?!** {message.author.mention} did you actually just say that? my psychic crystals are literally shattering from the toxic energy. reporting you to the higher astral plane immediately, BYE 🔮❌")
        return

    # 🗣️ PASSIVE TRIGGERS & REACTION SYSTEM
    if message.content.isupper() and len(message.content) > 12:
        if random.random() < 0.4:
            await message.channel.send("why are you literally screaming bestie? it's hurting my third eye and completely ruining the structural aesthetic of the chat. lower your frequency. 💀💅")
            return

    if "http" in content or "www." in content:
        if random.random() < 0.3:
            await message.channel.send("idk what this link is but the layout looks like an absolute flop from here 🔮❌")
            return

    if "i hate this" in content or "this sucks" in content:
        if random.random() < 0.5: await message.channel.send("omg stop being such a buzzkill, it's literally just a ✨vibe✨ issue, bestie. 💅")
    elif "magic" in content or "manifest" in content:
        if random.random() < 0.4: await message.channel.send("did someone say magic?! 🔮✨ manifest it queen!!")
    elif "school" in content or "exam" in content or "study" in content:
        if random.random() < 0.5: await message.channel.send("school is such a flop, come look into my crystal ball instead 🔮✨")
    elif "slay" in content:
        if random.random() < 0.4: await message.channel.send("purr, absolute main character energy right there 💖💅")
    elif "broke" in content or "no money" in content:
        if random.random() < 0.5: await message.channel.send("gofundme era? manifesting a sugar daddy or a lottery win for you immediately 💀🔮")

    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))