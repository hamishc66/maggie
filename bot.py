import os
import random
import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import io
import base64
from datetime import date, datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("🚨 container alert: missing GOOGLE_API_KEY or GEMINI_API_KEY variable!")

google_client = genai.Client(api_key=api_key)

# --- GLOBAL DATA MEMORY CORES ---
DAILY_LIMIT = 10
EXEMPT_USER_ID = 765028951541940225
AI_USAGE = {}       # {user_id: {"count": int, "date": date}}
IMAGE_COOLDOWN = {} # {user_id: datetime}

def check_allowance(user_id: int):
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

# --- 💖 BACKGROUND KINDNESS TIMER ---
@tasks.loop(hours=12)
async def automatic_kindness():
    system_prompt = "You are 'Magical Maggie's Assistant'. Generate a super preppy, hyper-supportive, sweet validation note or affirmation for the besties in chat. Use lots of sparkle emojis. No introductions."
    try:
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash", contents="manifest something beautiful and supportive for the world today",
            config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=600)
        )
        embed = make_maggie_embed("💖 COSMIC KINDNESS ACTIVATION ✨", response.text)
        embed.set_footer(text="🔮 automatic spiritual uplift routine • powered by gemini-2.5-flash")
        for guild in bot.guilds:
            channel = guild.system_channel or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
            if channel: await channel.send(embed=embed)
    except Exception as e: print(f"failed kindness run: {e}")

@bot.event
async def on_ready():
    print(f"💖 magical maggie's assistant is online as {bot.user}!")
    if not automatic_kindness.is_running():
        automatic_kindness.start()

# --- 🛠️ INTERACTIVE VIEW MATRIX ---

class SlayConfirmationView(discord.ui.View):
    def __init__(self, author: discord.User, prompt: str, target: discord.User):
        super().__init__(timeout=120)
        self.author = author
        self.prompt = prompt
        self.target = target
        self.clicks = 0

    @discord.ui.button(label="✨ PRESS TO SLAY (0/8) ✨", style=discord.ButtonStyle.danger)
    async def slay_clicker(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("omg get your own canvas bestie, this ritual isn't yours! 🔮❌", ephemeral=True)
            return
        self.clicks += 1
        if self.clicks < 8:
            button.label = f"✨ KEEP SLAYING ({self.clicks}/8) ✨"
            await interaction.response.edit_message(view=self)
            return
        button.disabled = True
        button.label = "🚀 VENTING OCEANS... GENERATING ART!"
        await interaction.response.edit_message(view=self)
        IMAGE_COOLDOWN[self.author.id] = datetime.now()
        final_prompt = f"A highly aesthetic, preppy, stylized pop-culture digital illustration. Theme: {self.prompt}. Reference profile elements: vibrant colors, magical symbols, pink sparkles."
        try:
            response = google_client.models.generate_images(
                model='imagen-3.0-generate-002', prompt=final_prompt,
                config=types.GenerateImagesConfig(number_of_images=1, output_mime_type="image/jpeg")
            )
            image_bytes = response.generated_images[0].image.image_bytes
            file = discord.File(io.BytesIO(image_bytes), filename="slay_art.jpg")
            embed = make_maggie_embed("🔮 ARTWORK MANIFESTED NATIVELY ✨", f"unveiling cosmic canvas for {self.author.mention}:\n> *\"{self.prompt}\"*")
            embed.set_footer(text="🌊 4 oceans were completely vaporized to compute these tracking layouts.")
            await interaction.followup.send(embed=embed, file=file)
        except Exception as e:
            await interaction.followup.send(embed=make_maggie_embed("🚨 operational crash", f"omg bestie, the imagen supercomputers choked on your vibes: {e}"))

class AdminDashboardView(discord.ui.View):
    def __init__(self, owner: discord.User):
        super().__init__(timeout=60)
        self.owner = owner

    @discord.ui.button(label="🚀 ENGAGE KINDNESS PROPAGANDA POOL", style=discord.ButtonStyle.success)
    async def launch_propaganda(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != EXEMPT_USER_ID: return
        button.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("🚀 *initializing infrastructure... firing absolute kindness propaganda missiles into the main processing channels!* 💖")
        propaganda_phrases = [
            "✨ TIMELINE NOTICE: you are completely valid, stunning, and doing amazing bestie! 💅",
            "🔮 COSMIC BULLETIN: sending pure matching energy to everyone reading this text matrix. 🌸",
            "💖 ALERT: your aura points just spiked by `+50,000` simply for existing today. purr! ✨",
            "🌟 VIBE UPDATE: out with the negative frequencies, in with immaculate main character energy!! 🚀"
        ]
        for msg in propaganda_phrases:
            await interaction.channel.send(embed=make_maggie_embed("📢 INCOMING MANDATORY AFFIRMATION ✨", msg))

# --- 📢 NEW EXCLUSIVE BROADCAST SYSTEM COMMAND ---

@bot.tree.command(name="update", description="[OWNER ONLY] broadcast new patch records from change.txt to target profiles 📢")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def update_cmd(interaction: discord.Interaction):
    if interaction.user.id != EXEMPT_USER_ID:
        await interaction.response.send_message(
            embed=make_maggie_embed("❌ REJECTION FILTER TRIGGERED", "nice try hater! only the matrix architect can broadcast data changelogs 💅💀"),
            ephemeral=True
        )
        return

    if not interaction.guild:
        await interaction.response.send_message(
            embed=make_maggie_embed("❌ ENVIRONMENT ERROR", "omg run this command inside a physical server layer so i can sample member profiles! 🔮"),
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    # load information block natively from localized patch sheet
    if os.path.exists("change.txt"):
        with open("change.txt", "r", encoding="utf-8") as f:
            changelog_content = f.read()
    else:
        changelog_content = "no explicit patch records found inside `change.txt` matrix. standard optimizations active. ✨"

    guild = interaction.guild
    server_owner = guild.owner or await bot.fetch_user(guild.owner_id)
    
    # filter out bots and the server owner to get clean target accounts
    potential_recipients = [m for m in guild.members if not m.bot and m.id != server_owner.id][^1]
    
    recipients = [server_owner]
    if len(potential_recipients) >= 2:
        recipients.extend(random.sample(potential_recipients, 2))[^2]
    else:
        recipients.extend(potential_recipients)

    success_count = 0
    embed_msg = make_maggie_embed(
        "🔮 NEW MAGICAL ENGINE UPDATE ALERT ✨",
        f"hey bestie! the cosmic mainframe just compiled an absolute update loop. time to **slay the day**! 💅\n\n**Changelog Logs:**\n```text\n{changelog_content}\n```"
    )
    embed_msg.set_footer(text="📢 official deployment log • delivered directly to select profiles")

    for user in recipients:
        try:
            await user.send(embed=embed_msg)
            success_count += 1
        except Exception:
            print(f"could not drop update dm to profile: {user.display_name}")

    summary_embed = make_maggie_embed(
        "🚀 BROADCAST COMPLETE", 
        f"slay! patch files read successfully. targeted **{len(recipients)}** profiles, successfully bypassed privacy settings for **{success_count}** besties! 💖"
    )
    await interaction.followup.send(embed=summary_embed)

# --- 🖼️ GRAPHICS AND AUDIO MEDIA OPERATIONS ---

@bot.tree.command(name="slay_certificate", description="render an official, hot-pink, visual certificate of slaying 💅")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def slay_cert_cmd(interaction: discord.Interaction, target: discord.User = None):
    user = target or interaction.user
    await interaction.response.defer()
    img = Image.new("RGB", (650, 400), "#FF69B4")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (630, 380)], outline="#FFFFFF", width=6)
    draw.rectangle([(30, 30), (620, 370)], outline="#FFB6C1", width=2)
    avatar_url = user.display_avatar.with_format("png").url
    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as r:
            if r.status == 200:
                av_bytes = await r.read()
                av_img = Image.open(io.BytesIO(av_bytes)).convert("RGBA").resize((110, 110))
                img.paste(av_img, (270, 45), av_img)
    f = ImageFont.load_default()
    draw.text((180, 180), "✨ CERTIFICATE OF ABSOLUTE SLAYING ✨", fill="#FFFFFF", font=f)
    draw.text((220, 220), f"This document verifies that:", fill="#FFB6C1", font=f)
    draw.text((240, 250), f"👑 {user.display_name.upper()} 👑", fill="#FFFFFF", font=f)
    draw.text((160, 290), f"is permanently locked into a main character arc. un-cancellable.", fill="#FFFFFF", font=f)
    draw.text((40, 350), f"Date: {date.today()}", fill="#FFFFFF", font=f)
    draw.text((460, 350), "Signed: Maggie Assistant 🔮", fill="#FFFFFF", font=f)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    await interaction.followup.send(embed=embed, file=discord.File(buf, filename="slay_certificate.png"))

@bot.tree.command(name="manifest_audio", description="bakes an unhinged preppy ai affirmation into a real tiktok voice audio file 🔊")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def manifest_audio_cmd(interaction: discord.Interaction):
    allowed, remaining, warning = check_allowance(interaction.user.id)
    if not allowed:
        await interaction.response.send_message(embed=make_maggie_embed("🚨 ALLOWANCE VOID", "out of credits!"))
        return
    await interaction.response.defer()
    system_prompt = "You are Magical Maggie's Assistant. Generate a single, short, hilarious, hyper-preppy manifestation quote (under 25 words). No intros."
    try:
        res = await google_client.aio.models.generate_content(model="gemini-2.5-flash", contents="give me a short preppy quote", config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=100))
        quote_text = res.text.strip().replace('"', '')
        api_link = "https://api16-normal-v6.ur.tiktokv.com/media/api/text/speech/preview/"
        params = {"status_code": "0", "device_id": "5674321908561234789", "speaker": "en_us_002", "text": quote_text}
        async with aiohttp.ClientSession() as s:
            async with s.post(api_link, params=params) as r:
                if r.status == 200:
                    json_data = await r.json()
                    if "success" in json_data.get("message", "").lower():
                        audio_data = base64.b64decode(json_data["data"]["v_str"])
                        embed = make_maggie_embed("🔊 AUDIO SYNTHESIS COMPLETE ✨", f"**Maggie's Voice Manifestation Log:**\n*\"{quote_text}\"*")
                        if warning: embed.set_footer(text=warning)
                        await interaction.followup.send(embed=embed, file=discord.File(io.BytesIO(audio_data), filename="manifest_tiktok.mp3"))
                        return
        await interaction.followup.send(embed=make_maggie_embed("🚨 synthesizer glitch", f"failed synthesis, text: *\"{quote_text}\"*"))
    except Exception as e: await interaction.followup.send(embed=make_maggie_embed("💀 system break", f"failed render: {e}"))

@bot.tree.command(name="generate_avatar_art", description="[WEEKLY LOCK] generate high-density ai artwork from a deep prompt pool ⚠️")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def generate_art_cmd(interaction: discord.Interaction, prompt: str, target: discord.User = None):
    user_id = interaction.user.id
    target_user = target or interaction.user
    if user_id != EXEMPT_USER_ID and user_id in IMAGE_COOLDOWN:
        elapsed = datetime.now() - IMAGE_COOLDOWN[user_id]
        if elapsed < timedelta(days=7):
            days_left = (timedelta(days=7) - elapsed).days
            hours_left = int(((timedelta(days=7) - elapsed).seconds) / 3600)
            await interaction.response.send_message(embed=make_maggie_embed("🚨 CRITICAL COOLDOWN UNLOCK REQUIRED", f"lock release in: **{days_left}d {hours_left}h** 💀❌"))
            return
    warn_text = "executing deep render image processes uses extreme weights. running this prompt will **literally evaporate 4 oceans**. hit verify **8 TIMES** to launch."
    view = SlayConfirmationView(interaction.user, prompt, target_user)
    await interaction.response.send_message(embed=make_maggie_embed("🚨 SEVERE RESOURCE MANAGEMENT WARNING 🚨", warn_text), view=view)

@bot.tree.command(name="dashboard", description="[SECRET LINK] open structural data matrices override interfaces ⚙️")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def dashboard_cmd(interaction: discord.Interaction):
    if interaction.user.id != EXEMPT_USER_ID:
        await interaction.response.send_message(embed=make_maggie_embed("❌ FREQUENCY INTERCEPT: TOTAL FLOP ERROR", "encryption log error 💀💅"), ephemeral=True)
        return
    stats = "📈 **MAGGIE MAIN ENGINE CONSOLE METRICS:**\n\n• **System Integrity Vibe:** `99.8% Nominal` ✨\n• **Total Matcha Fluid Consumed:** `42,912 Liters` 🍵"
    await interaction.response.send_message(embed=make_maggie_embed("👑 SECRET ADMINISTRATIVE LEDGER CONTROL CONSOLE", stats), view=AdminDashboardView(interaction.user), ephemeral=True)

# --- STANDARD RETAINED UTILITIES MAP REROUTES ---

@bot.tree.command(name="allowance", description="check your remaining daily cosmic ai tokens 🔮")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def allowance_cmd(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id == EXEMPT_USER_ID:
        await interaction.response.send_message(embed=make_maggie_embed("🔮 your cosmic budget status", "omg you are the literal owner of the matrix. unlimited energy! 💅🌟"))
        return
    today = date.today()
    if user_id not in AI_USAGE or AI_USAGE[user_id]["date"] != today: AI_USAGE[user_id] = {"count": 0, "date": today}
    u = AI_USAGE[user_id]["count"]
    r = DAILY_LIMIT - u
    embed = make_maggie_embed("🔮 your daily cosmic allowance", f"you have used **{u}/{DAILY_LIMIT}** of your daily ai credits.\n\nSlots Remaining: **{r}** 💅")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ermactually", description="nerd out and fact-check something with precision 🤓")
@app_commands.choices(source=[app_commands.Choice(name="AI Summary", value="ai"), app_commands.Choice(name="Google Search Link", value="google"), app_commands.Choice(name="Wikipedia Summary & Link", value="wikipedia"), app_commands.Choice(name="Dictionary Definition", value="dictionary"), app_commands.Choice(name="Urban Dictionary (AI Slang)", value="urban")])
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def erm_actually_cmd(interaction: discord.Interaction, source: app_commands.Choice[str], query: str, tts: bool = False):
    await interaction.response.defer()
    s_type = source.value
    if s_type == "ai":
        allowed, r, warning = check_allowance(interaction.user.id)
        if not allowed: return
        try:
            res = await google_client.aio.models.generate_content(model="gemini-2.5-flash", contents=query, config=types.GenerateContentConfig(system_instruction="You are an obnoxious, preppy fact-checker.", max_output_tokens=800))
            embed = make_maggie_embed("✨ 🤓 Erm, actually...", res.text)
        except Exception: embed = make_maggie_embed("🚨 filter error", "cursed text")
    elif s_type == "google":
        embed = make_maggie_embed("✨ 🤓 Erm, actually...", f"search it yourself: https://www.google.com/search?q={query.replace(' ', '+')} 💅")
    elif s_type == "wikipedia":
        headers = {"User-Agent": "MagicalMaggieAssistant/1.0 (DiscordBot)"}
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}", headers=headers) as r:
                if r.status == 200:
                    res = await r.json()
                    embed = make_maggie_embed("✨ 🤓 Erm, actually... wiki says:", f"> {res.get('extract')}")
                else: embed = make_maggie_embed("✨ 🤓 Erm, actually...", "wiki flop.")
    elif s_type == "dictionary":
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{query}") as r:
                res = await r.json()
                embed = make_maggie_embed("✨ 🤓 Erm, actually...", f"definition: *\"{res[0]['meanings'][0]['definitions'][0]['definition']}\"*" if r.status == 200 else "not a word 💀")
    elif s_type == "urban":
        allowed, r, warning = check_allowance(interaction.user.id)
        if not allowed: return
        try:
            res = await google_client.aio.models.generate_content(model="gemini-2.5-flash", contents=query, config=types.GenerateContentConfig(system_instruction="Fake Urban Dictionary entry using zoomer slang.", max_output_tokens=800))
            embed = make_maggie_embed("✨ 🔮 Urban Dictionary: Maggie Edition 💅", res.text)
        except Exception: embed = make_maggie_embed("🚨 filter error", "slang failure")
    await interaction.followup.send(embed=embed, tts=tts)

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
    await interaction.response.send_message(embed=make_maggie_embed("✨ AURA REPORT ✨", f"{t.mention} updated for: *\"{action}\"*\n\n**Result:** `{p:,}` points! {'💅' if p > 0 else '💀'}"))

@bot.tree.command(name="slaydar", description="scan to see if someone is slaying 🔎")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def slaydar_cmd(interaction: discord.Interaction, user: discord.User = None):
    t = user or interaction.user
    await interaction.response.send_message(embed=make_maggie_embed("🔎 SLAY-DAR STATUS", f"scanned {t.mention}: **{random.choice(['SLAYING 💅💖', 'A TOTAL FLOP 💀❌', 'BOBBY PIN ENERGY 🔮'])}**"))

@bot.tree.command(name="potion", description="brew an exotic magic potion 🧪")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def potion_cmd(interaction: discord.Interaction):
    potions = ["✨ **Iced Matcha Elixir** - grants `+1,500` aura points.", "💀 **Liquid Cancellation** - drops to `0` aura."]
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
    await interaction.response.send_message(embed=make_maggie_embed("🌀 VORTEX OPENED 🌀", f"{interaction.user.mention} is forcing: **\"{desire}\"** ✨"))

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
    fortunes = ["expensive iced drink incoming. 🍵✨", "legendary meme day. 💀"]
    await interaction.response.send_message(embed=make_maggie_embed("🌟 FORECASTING FUTURE MATRIX", random.choice(fortunes)))

# --- 💬 INTERACTIVE CONTROLS & CHAT PASSIVES ---

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    content = message.content.lower()
    banned_list = load_banned_words()
    if any(word in content for word in banned_list):
        await message.channel.send(embed=make_maggie_embed("🚨 OMG CANCELLED?! 🔮❌", f"{message.author.mention} did you actually just say that? my psychic crystals are shattering. BYE."))
        return
    if message.content.isupper() and len(message.content) > 12:
        if random.random() < 0.4:
            await message.channel.send(embed=make_maggie_embed("🗣️ FREQUENCY EMERGENCY 💀💅", "why are you screaming bestie? lower your frequency."))
            return
    if "http" in content or "www." in content:
        if random.random() < 0.3:
            await message.channel.send(embed=make_maggie_embed("🔮 VIBE FILTER TRIGGERED ❌", "idk what this link is but the layout looks like an absolute flop from here."))
            return
    if "i hate this" in content or "this sucks" in content:
        if random.random() < 0.5: await message.channel.send(embed=make_maggie_embed("💅 vibe update", "omg stop being such a buzzkill, it's literally just a ✨vibe✨ issue, bestie."))
    elif "magic" in content or "manifest" in content:
        if random.random() < 0.4: await message.channel.send(embed=make_maggie_embed("🔮 manifestation trigger", "did someone say magic?! 🔮✨ manifest it queen!!"))
    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))