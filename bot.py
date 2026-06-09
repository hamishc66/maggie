import os
import random
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from datetime import date
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("🚨 container alert: missing GOOGLE_API_KEY or GEMINI_API_KEY variable!")

google_client = genai.Client(api_key=api_key)

# --- CONFIGURATION FOR BILL GUARD SYSTEM ---
DAILY_LIMIT = 10
EXEMPT_USER_ID = 765028951541940225
AI_USAGE = {}  # structure: {user_id: {"count": int, "date": date}}

def check_allowance(user_id: int):
    """tracks, increments, and checks a user's daily credit pool"""
    if user_id == EXEMPT_USER_ID:
        return True, 999, ""
        
    today = date.today()
    if user_id not in AI_USAGE or AI_USAGE[user_id]["date"] != today:
        AI_USAGE[user_id] = {"count": 0, "date": today}
        
    user_data = AI_USAGE[user_id]
    if user_data["count"] >= DAILY_LIMIT:
        return False, 0, ""
        
    user_data["count"] += 1
    remaining = DAILY_LIMIT - user_data["count"]
    
    warning = ""
    if remaining <= 2 and remaining > 0:
        warning = f"⚠️ token warning: only {remaining} cosmic credits left today bestie!"
    elif remaining == 0:
        warning = "🚨 budget alert: that was your last cosmic credit today! see you tomorrow 💀"
        
    return True, remaining, warning

def load_banned_words():
    if os.path.exists("bad.txt"):
        with open("bad.txt", "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if line.strip()]
    return []

def make_maggie_embed(title: str, description: str):
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.from_rgb(255, 105, 180)
    )

class MagicalBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("✨ registered all application commands globally! ✨")

bot = MagicalBot()

@bot.event
async def on_guild_join(guild):
    owner = guild.owner or await bot.fetch_user(guild.owner_id)
    if not owner:
        return
    try:
        embed = discord.Embed(
            title="🔮 MAGICAL MAGGIE'S ASSISTANT — DEPLOYMENT PROTOCOL 🔮",
            description=(
                "oK BESITE IM SETTING UP MY TAAROT CARDS, YOU WILL RECIEVE A TUTORIAL IN THE SEVRER SOON ✨\n\n"
                "thank you for authorizing the core system link. maggie's assistant is now running backgrounds "
                "on your local guild infrastructure to manage chaos metrics, filter bad frequencies, and deliver cosmic intelligence."
            ),
            color=discord.Color.from_rgb(255, 105, 180)
        )
        embed.add_field(
            name="📈 administrative metrics", 
            value=f"• **Target Guild:** {guild.name}\n• **Total Souls Tracked:** {guild.member_count}\n• **Gateway Protocol:** Slash Commands (`/`) Enabled Natively", 
            inline=False
        )
        embed.add_field(
            name="🛡️ automated defense configuration", 
            value="the `bad.txt` data loop is monitoring chat. any flagged terms or toxic frequencies will be instantly vaporized, messages deleted, and target profiles hit with public astral cancellations.", 
            inline=False
        )
        embed.add_field(
            name="💅 deployment matrix (all systems nominal)", 
            value="• **Social Engineering:** `/cancel`, `/gaslight`, `/gatekeep`, `/girlboss` \n• **Esoteric Matrix:** `/starbucks_order`, `/coachella_lineup`, `/spiritual_gossip`, `/realign_chakras` \n• **Core Processing:** `/ai`, `/ermactually`, `/allowance`, `/vibecheck`, `/aura`, `/slaydar`, `/manifest`, `/crystals`, `/potion`", 
            inline=False
        )
        embed.set_footer(text="system build v2.4.2 • initializing immaculate server vibe stabilization 💖")
        await owner.send(embed=embed)
    except Exception as e:
        print(f"could not trigger onboarding: {e}")

@bot.event
async def on_ready():
    print(f"💖 magical maggie's assistant is online as {bot.user}!")

# --- 🔮 ACCOUNT ALLOWANCE METER COMMAND ---

@bot.tree.command(name="allowance", description="check your remaining daily cosmic ai tokens 🔮")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def allowance_cmd(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id == EXEMPT_USER_ID:
        embed = make_maggie_embed("🔮 your cosmic budget status", "omg you are the literal owner of the matrix. your energy is unlimited, infinite, and un-cancellable. slay! 💅🌟")
        await interaction.response.send_message(embed=embed)
        return
        
    today = date.today()
    if user_id not in AI_USAGE or AI_USAGE[user_id]["date"] != today:
        AI_USAGE[user_id] = {"count": 0, "date": today}
        
    used = AI_USAGE[user_id]["count"]
    remaining = DAILY_LIMIT - used
    
    embed = make_maggie_embed("🔮 your daily cosmic allowance", f"you have used **{used}/{DAILY_LIMIT}** of your daily ai credits.\n\nSlots Remaining: **{remaining}** 💅")
    if remaining == 0:
        embed.set_footer(text="💀 out of energy! go drink an iced matcha and wait for a calendar reset.")
    else:
        embed.set_footer(text="✨ use your manifestation powers wisely.")
    await interaction.response.send_message(embed=embed)

# --- 🧠 AI DRIVEN SLIDER COMMAND MAP (WITH BUDGET CHECKING) ---

@bot.tree.command(name="ai", description="chat with the preppy magical assistant 💅")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(prompt="what do you want to tell maggie?", tts="should maggie speak this out loud?")
async def ai_cmd(interaction: discord.Interaction, prompt: str, tts: bool = False):
    allowed, remaining, warning = check_allowance(interaction.user.id)
    if not allowed:
        embed = make_maggie_embed("🚨 OUT OF ENERGY 💀", "omg bestie, you completely exhausted your daily cosmic ai slots! my psychic waves cost money 😭 check `/allowance` profile.")
        await interaction.response.send_message(embed=embed)
        return

    await interaction.response.defer()
    system_prompt = "You are 'Magical Maggie's Assistant'. You are super preppy, magic-themed, progressive, hilarious, and love shitposting. Do not use introductory filler text. Jump right into the chaotic response."
    try:
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash", contents=prompt,
            config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=800)
        )
        embed = make_maggie_embed("🔮 maggie pops off:", response.text)
        if warning: embed.set_footer(text=warning)
    except Exception:
        embed = make_maggie_embed("🚨 vibe block", "omg bestie, that prompt triggered a total spiritual block in my safety mainframe 💀")
    await interaction.followup.send(embed=embed, tts=tts)

@bot.tree.command(name="ermactually", description="nerd out and fact-check something with precision 🤓")
@app_commands.choices(source=[
    app_commands.Choice(name="AI Summary", value="ai"), app_commands.Choice(name="Google Search Link", value="google"),
    app_commands.Choice(name="Wikipedia Summary & Link", value="wikipedia"), app_commands.Choice(name="Dictionary Definition", value="dictionary"),
    app_commands.Choice(name="Urban Dictionary (AI Slang)", value="urban")
])
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def erm_actually_cmd(interaction: discord.Interaction, source: app_commands.Choice[str], query: str, tts: bool = False):
    await interaction.response.defer()
    source_type = source.value
    
    if source_type == "ai":
        allowed, remaining, warning = check_allowance(interaction.user.id)
        if not allowed:
            embed = make_maggie_embed("🚨 ALLOWANCE LIMIT 💀", "bestie, you've exhausted your daily cosmic slots for AI data summaries. look it up via the google mode instead!")
            await interaction.followup.send(embed=embed)
            return
        try:
            res = await google_client.aio.models.generate_content(
                model="gemini-2.5-flash", contents=query,
                config=types.GenerateContentConfig(system_instruction="You are an obnoxious, preppy 'Erm, actually...' fact-checker. No filler intros.", max_output_tokens=800)
            )
            embed = make_maggie_embed("✨ 🤓 Erm, actually...", res.text)
            footer_text = f"🔮 data via google gemini. | {warning}" if warning else "🔮 data via google gemini."
            embed.set_footer(text=footer_text)
        except Exception: embed = make_maggie_embed("🚨 filter emergency", "omg that topic is too cursed or unaligned for my system to process 💀")
        
    elif source_type == "google":
        embed = make_maggie_embed("✨ 🤓 Erm, actually...", f"search it yourself, bestie: https://www.google.com/search?q={query.replace(' ', '+')} 💅")
        embed.set_footer(text="🔎 search indexes generated and delivered via google network architecture.")
        
    elif source_type == "wikipedia":
        headers = {"User-Agent": "MagicalMaggieAssistant/1.0 (DiscordBot)"}
        encoded_title = query.replace(" ", "_")
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
        async with aiohttp.ClientSession() as s:
            try:
                async with s.get(wiki_url, headers=headers) as r:
                    if r.status == 200:
                        res = await r.json()
                        extract = res.get("extract", "No extract found.")
                        page_url = res.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{encoded_title}")
                        embed = make_maggie_embed("✨ 🤓 Erm, actually... according to wiki:", f"> {extract}\n\nread more: {page_url} 💅")
                    else: embed = make_maggie_embed("✨ 🤓 Erm, actually...", "wikipedia doesn't even know what that is. a total flop.")
                embed.set_footer(text="📖 factual logs compiled and structured by the wikipedia open database community.")
            except Exception: embed = make_maggie_embed("💀 error", "wikipedia rejected my vibes entirely")
                
    elif source_type == "dictionary":
        async with aiohttp.ClientSession() as s:
            try:
                async with s.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{query}") as r:
                    res = await r.json()
                    embed = make_maggie_embed("✨ 🤓 Erm, actually...", f"definition: *\"{res[0]['meanings'][0]['definitions'][0]['definition']}\"*" if r.status == 200 else "not a real word bestie 💀")
                embed.set_footer(text="📚 lexical entries verified via the public open-source free dictionary API.")
            except Exception: embed = make_maggie_embed("💀 error", "dictionary data system lag")
            
    elif source_type == "urban":
        allowed, remaining, warning = check_allowance(interaction.user.id)
        if not allowed:
            embed = make_maggie_embed("🚨 ALLOWANCE LIMIT 💀", "bestie, you've exhausted your daily cosmic slots for generating urban slang records!")
            await interaction.followup.send(embed=embed)
            return
        try:
            res = await google_client.aio.models.generate_content(
                model="gemini-2.5-flash", contents=query,
                config=types.GenerateContentConfig(system_instruction="Invent a fake Urban Dictionary entry using extreme zoomer slang. No intro filler.", max_output_tokens=800)
            )
            embed = make_maggie_embed("✨ 🔮 Urban Dictionary: Maggie Edition 💅", res.text)
            footer_text = f"🔮 definitions via google gemini. | {warning}" if warning else "🔮 definitions via google gemini."
            embed.set_footer(text=footer_text)
        except Exception: embed = make_maggie_embed("🚨 filter emergency", "omg my slang generator completely choked 💀")
        
    await interaction.followup.send(embed=embed, tts=tts)

@bot.tree.command(name="cancel", description="generate a massive public call-out thread or notes app apology 📉")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def cancel_cmd(interaction: discord.Interaction, user: discord.User, reason: str):
    allowed, remaining, warning = check_allowance(interaction.user.id)
    if not allowed:
        await interaction.response.send_message(embed=make_maggie_embed("🚨 COGNITIVE RESET", "out of credits today bestie 💀"))
        return
        
    await interaction.response.defer()
    system_prompt = "Generate a dramatic, multi-paragraph, hyper-preppy 'Notes App Apology' or a public call-out on behalf of the user. Use heavy zoomer slang. No filler introductions."
    try:
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash", contents=f"cancel {user.display_name} because {reason}",
            config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=800)
        )
        embed = make_maggie_embed(f"📢 PUBLIC STATEMENT REGARDING {user.display_name}:", response.text)
        if warning: embed.set_footer(text=warning)
    except Exception: embed = make_maggie_embed("🚨 drama block", "omg that drama is too toxic to write down 💀")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="gaslight", description="completely deny reality on behalf of a situation 🌀")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def gaslight_cmd(interaction: discord.Interaction, user: discord.User, statement: str):
    allowed, remaining, warning = check_allowance(interaction.user.id)
    if not allowed:
        await interaction.response.send_message(embed=make_maggie_embed("🚨 COGNITIVE RESET", "out of credits today bestie 💀"))
        return
        
    await interaction.response.defer()
    system_prompt = "Write a short, highly manipulative but hilarious reply telling the target user that they are entirely crazy, imagining things. No intros."
    try:
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash", contents=f"gaslight {user.display_name} about {statement}",
            config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=600)
        )
        embed = make_maggie_embed("🌀 altering reality:", f"{user.mention} {response.text}")
        if warning: embed.set_footer(text=warning)
    except Exception: embed = make_maggie_embed("🚨 loop block", "my reality machine jammed 💀")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="gatekeep", description="explain why someone isn't cool enough for a topic ❌")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def gatekeep_cmd(interaction: discord.Interaction, topic: str):
    allowed, remaining, warning = check_allowance(interaction.user.id)
    if not allowed:
        await interaction.response.send_message(embed=make_maggie_embed("🚨 COGNITIVE RESET", "out of credits today bestie 💀"))
        return
        
    await interaction.response.defer()
    system_prompt = "Write a preppy, sardonically snobby speech explaining why the person asking is banned from enjoying or talking about the specified topic. No intros."
    try:
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash", contents=f"gatekeep {topic}",
            config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=800)
        )
        embed = make_maggie_embed(f"❌ URGENT NOTICE REGARDING {topic.upper()}:", response.text)
        if warning: embed.set_footer(text=warning)
    except Exception: embed = make_maggie_embed("🚨 system block", "code filter triggered 💀")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="girlboss", description="generate an unhinged daily rise-and-grind routine 💅")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def girlboss_cmd(interaction: discord.Interaction):
    allowed, remaining, warning = check_allowance(interaction.user.id)
    if not allowed:
        await interaction.response.send_message(embed=make_maggie_embed("🚨 COGNITIVE RESET", "out of credits today bestie 💀"))
        return
        
    await interaction.response.defer()
    system_prompt = "Generate a funny, progressive, totally chaotic daily schedule for a 'girlboss' with bullet points. Start directly with the schedule."
    try:
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash", contents="daily routine",
            config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=800)
        )
        embed = make_maggie_embed("💅 DAILY ACCELERATION ROUTINE 📈", response.text)
        if warning: embed.set_footer(text=warning)
    except Exception: embed = make_maggie_embed("💀 error", "grind loop interrupted")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="starbucks_order", description="brew a chaotic 15-ingredient magical drink order ☕")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def starbucks_cmd(interaction: discord.Interaction):
    allowed, remaining, warning = check_allowance(interaction.user.id)
    if not allowed:
        await interaction.response.send_message(embed=make_maggie_embed("🚨 COGNITIVE RESET", "out of credits today bestie 💀"))
        return
        
    await interaction.response.defer()
    system_prompt = "Invent a hyper-complicated, completely ridiculous 15-ingredient custom Starbucks order. Start directly with the specs."
    try:
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash", contents="overcomplicated order",
            config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=800)
        )
        embed = make_maggie_embed("🍵 YOUR SPIRITUAL CONCOCTION:", response.text)
        if warning: embed.set_footer(text=warning)
    except Exception: embed = make_maggie_embed("💀 error", "barista crashed")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="spiritual_gossip", description="spill some fake astronomical tea about the solar system 🌟")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def gossip_cmd(interaction: discord.Interaction):
    allowed, remaining, warning = check_allowance(interaction.user.id)
    if not allowed:
        await interaction.response.send_message(embed=make_maggie_embed("🚨 COGNITIVE RESET", "out of credits today bestie 💀"))
        return
        
    await interaction.response.defer()
    system_prompt = "Write a quick piece of gossip talking about planets and stars as if they are high school drama characters. Use massive preppy slang. No intros."
    try:
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash", contents="space tea",
            config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=600)
        )
        embed = make_maggie_embed("🔮 THE ASTRAL TEA IS SPLASHING:", response.text)
        if warning: embed.set_footer(text=warning)
    except Exception: embed = make_maggie_embed("💀 error", "space is silent")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="manifest", description="manifest your wildest desires into reality ✨")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def manifest_cmd(interaction: discord.Interaction, desire: str):
    allowed, remaining, warning = check_allowance(interaction.user.id)
    if not allowed:
        await interaction.response.send_message(embed=make_maggie_embed("🚨 COGNITIVE RESET", "out of credits today bestie 💀"))
        return
        
    await interaction.response.defer()
    try:
        res = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash", contents=desire,
            config=types.GenerateContentConfig(system_instruction="Generate a hyper-preppy manifestation ritual. No filler intros.", max_output_tokens=600)
        )
        embed = make_maggie_embed("✨ MANIFESTATION MATRIX LOADED", res.text)
        if warning: embed.set_footer(text=warning)
    except Exception: embed = make_maggie_embed("💀 error", "universe busy")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="horoscope", description="fabricated preppy prediction 🌟")
@app_commands.choices(sign=[app_commands.Choice(name="Aries", value="aries"), app_commands.Choice(name="Taurus", value="taurus"), app_commands.Choice(name="Gemini", value="gemini"), app_commands.Choice(name="Cancer", value="cancer"), app_commands.Choice(name="Leo", value="leo"), app_commands.Choice(name="Virgo", value="virgo"), app_commands.Choice(name="Libra", value="libra"), app_commands.Choice(name="Scorpio", value="scorpio"), app_commands.Choice(name="Sagittarius", value="sagittarius"), app_commands.Choice(name="Capricorn", value="capricorn"), app_commands.Choice(name="Aquarius", value="aquarius"), app_commands.Choice(name="Pisces", value="pisces")])
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def horoscope_cmd(interaction: discord.Interaction, sign: app_commands.Choice[str]):
    allowed, remaining, warning = check_allowance(interaction.user.id)
    if not allowed:
        await interaction.response.send_message(embed=make_maggie_embed("🚨 COGNITIVE RESET", "out of credits today bestie 💀"))
        return
        
    await interaction.response.defer()
    try:
        res = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash", contents=sign.name,
            config=types.GenerateContentConfig(system_instruction="Generate a preppy horoscope. No filler intros.", max_output_tokens=600)
        )
        embed = make_maggie_embed(f"🌟 {sign.name.upper()} HOROSCOPE 🔮", res.text)
        if warning: embed.set_footer(text=warning)
    except Exception: embed = make_maggie_embed("💀 error", "stars blocked")
    await interaction.followup.send(embed=embed)

# --- 📦 RANDOM / FREE STATIC CHANNELS (NOT DEDUCTED FROM BILL POOL) ---

@bot.tree.command(name="coachella_lineup", description="generate a chaotic music festival poster featuring server members 🎪")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def coachella_cmd(interaction: discord.Interaction):
    members = [m.display_name for m in interaction.guild.members] if interaction.guild else ["Bestie Clone A", "Matcha Monster", "Aura Void"]
    head1 = random.choice(members)
    head2 = random.choice(members)
    reply = (
        f"🔥 **MAIN HEADLINERS:**\n• **{head1}** (*'vibe check emergency'*)\n• **{head2}** (*notes-app apology set*)\n\n"
        f"🎵 **SUB-STAGE ACTS:**\nProgressive Tax Evasion, Slowed+Reverb Astral Crying, Iced Chai Metalcore, and The Matcha Manifestation Project. 💅"
    )
    await interaction.response.send_message(embed=make_maggie_embed("🎪 COACHELLA: MAGICAL BESTIES EDITION 🎪", reply))

@bot.tree.command(name="realign_chakras", description="force a passive-aggressive wellness check on someone 🧘")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def realign_cmd(interaction: discord.Interaction, user: discord.User):
    reply = f"hey {user.mention}, your current outputs have been flagged as a total spiritual hazard. please take a deep breath, go order an expensive iced tea, and stop projecting your internal un-alignment onto the chat. 🔮💅"
    await interaction.response.send_message(embed=make_maggie_embed("🧘 CHAKRA EMERGENCY DETECTION 🧘", reply))

@bot.tree.command(name="vibecheck", description="run an advanced psychic check on someone 🔮")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def vibecheck_cmd(interaction: discord.Interaction, user: discord.User = None):
    t = user or interaction.user
    score = random.randint(1, 10)
    comments = ["trash energy. 💀", "lacking sparkles. 💅", "filler episode. 🔮", "immaculate energy. ✨", "cosmic greatness!! 🌟"]
    c = comments[0] if score <= 3 else comments[1] if score <= 5 else comments[2] if score <= 7 else comments[3] if score <= 9 else comments[4]
    await interaction.response.send_message(embed=make_maggie_embed(f"🔮 VIBE CHECK FOR {t.display_name}:", f"Score: **{score}/10**\n\n> {c}"))

@bot.tree.command(name="aura", description="calculate shifts in aura points 📉📈")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def aura_cmd(interaction: discord.Interaction, action: str, user: discord.User = None):
    t = user or interaction.user
    p = random.choice([+500, +1000, +50000, -200, -1500, -1000000])
    emoji = "💅" if p > 0 else "💀"
    await interaction.response.send_message(embed=make_maggie_embed("✨ AURA REPORT ✨", f"{t.mention} updated for: *\"{action}\"*\n\n**Result:** `{p:,}` points! {emoji}"))

@bot.tree.command(name="slaydar", description="scan to see if someone is slaying 🔎")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def slaydar_cmd(interaction: discord.Interaction, user: discord.User = None):
    t = user or interaction.user
    status = random.choice(['SLAYING 💅💖', 'A TOTAL FLOP 💀❌', 'BOBBY PIN ENERGY 🔮'])
    await interaction.response.send_message(embed=make_maggie_embed("🔎 SLAY-DAR STATUS", f"scanned {t.mention}: **{status}**"))

@bot.tree.command(name="crystals", description="pull a dynamic daily crystal reading 💎")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def crystals_cmd(interaction: discord.Interaction):
    stones = ["Moldavite 🟢 (chaotic nuclear destruction incoming 💀)", "Rose Quartz 🌸 (immaculate matching energy 💅)", "Amethyst 🔮 (calm down, you're doing too much.)", "Clear Quartz ❄️ (vibe amplification active ✨)"]
    await interaction.response.send_message(embed=make_maggie_embed("💎 COSMIC CRYSTAL MATRIX", f"your stone today is: **{random.choice(stones)}**"))

@bot.tree.command(name="potion", description="brew an exotic magic potion 🧪")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def potion_cmd(interaction: discord.Interaction):
    potions = ["✨ **Iced Matcha Elixir** - grants `+1,500` aura points.", "💀 **Liquid Cancellation** - drops to `0` aura.", "🔮 **Starbucks Psychic Brew** - track your crush ☕"]
    await interaction.response.send_message(embed=make_maggie_embed("🔮 YOU BREWED A CONCOCTION", random.choice(potions)))

@bot.tree.command(name="bestiematch", description="scan soul alignment 🔎")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def bestiematch_cmd(interaction: discord.Interaction, bestie: discord.User):
    compat = random.randint(1, 100)
    v = "toxic biohazard 💀" if compat < 30 else "bobby pin energy 🔮" if compat < 65 else "literal twin flames 💖💅"
    await interaction.response.send_message(embed=make_maggie_embed("🔎 BESTIE ALIGNMENT RADAR", f"🔥 {interaction.user.mention} x {bestie.mention} = **{compat}%**!\n\n> **Verdict:** {v}"))

@bot.tree.command(name="manifestation_circle", description="open a manifestation vortex 🌀")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def manifestation_circle_cmd(interaction: discord.Interaction, desire: str):
    await interaction.response.send_message(embed=make_maggie_embed("🌀 VORTEX OPENED 🌀", f"{interaction.user.mention} is forcing: **\"{desire}\"** ✨\n\nREACT WITH ✨ OR 🔮 TO POWER IT!"))

@bot.tree.command(name="hex", description="cast a minor curse 🪄")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def hex_cmd(interaction: discord.Interaction, enemy: discord.User):
    curses = ["may their coffee taste like grass.", "may their phone charger only work at a 45-degree angle."]
    await interaction.response.send_message(embed=make_maggie_embed("🪄 PETTY CURSE HEX DEPLOYED", f"cast on {enemy.mention}:\n\n> \"{random.choice(curses)}\" 💅🔮"))

@bot.tree.command(name="tarot", description="tarot vibe check 🔮")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def tarot_cmd(interaction: discord.Interaction):
    cards = ["The Fool ✨ (main character energy)", "The Tower 💀 (vibe emergency)", "Death 💅 (slay! aesthetic reset)"]
    await interaction.response.send_message(embed=make_maggie_embed("🔮 DRAWING FATE...", f"your card: **{random.choice(cards)}**"))

@bot.tree.command(name="fortune", description="predict future 🌟")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def fortune_cmd(interaction: discord.Interaction):
    fortunes = ["expensive iced drink incoming. 🍵✨", "legendary meme day. 💀", "immaculate vibes. 💖"]
    await interaction.response.send_message(embed=make_maggie_embed("🌟 FORECASTING FUTURE MATRIX", random.choice(fortunes)))

# --- 💬 INTERACTIVE CONTROLS & CHAT PASSIVES ---

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    content = message.content.lower()
    
    banned_list = load_banned_words()
    if any(word in content for word in banned_list):
        try: await message.delete()
        except discord.Forbidden: pass
        await message.channel.send(embed=make_maggie_embed("🚨 OMG CANCELLED?! 🔮❌", f"{message.author.mention} did you actually just say that? my psychic crystals are shattering. BYE."))
        return

    if message.content.isupper() and len(message.content) > 12:
        if random.random() < 0.4:
            await message.channel.send(embed=make_maggie_embed("🗣️ FREQUENCY EMERGENCY 💀💅", "why are you screaming bestie? it's ruining the structural aesthetic of the chat. lower your frequency."))
            return

    if "http" in content or "www." in content:
        if random.random() < 0.3:
            await message.channel.send(embed=make_maggie_embed("🔮 VIBE FILTER TRIGGERED ❌", "idk what this link is but the layout looks like an absolute flop from here."))
            return

    if "i hate this" in content or "this sucks" in content:
        if random.random() < 0.5: await message.channel.send(embed=make_maggie_embed("💅 vibe update", "omg stop being such a buzzkill, it's literally just a ✨vibe✨ issue, bestie."))
    elif "magic" in content or "manifest" in content:
        if random.random() < 0.4: await message.channel.send(embed=make_maggie_embed("🔮 manifestation trigger", "did someone say magic?! 🔮✨ manifest it queen!!"))
    elif "school" in content or "exam" in content or "study" in content:
        if random.random() < 0.5: await message.channel.send(embed=make_maggie_embed("✨ crystal ball check", "school is such a flop, come look into my crystal ball instead 🔮✨"))
    elif "slay" in content:
        if random.random() < 0.4: await message.channel.send(embed=make_maggie_embed("💖 identity log", "purr, absolute main character energy right there 💖💅"))
    elif "broke" in content or "no money" in content:
        if random.random() < 0.5: await message.channel.send(embed=make_maggie_embed("💀 timeline update", "gofundme era? manifesting a sugar daddy or a lottery win for you immediately 💀🔮"))

    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))
