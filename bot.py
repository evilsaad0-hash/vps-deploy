# ============================================================
#   ██╗   ██╗██████╗ ███████╗      ██████╗  ██████╗ ████████╗
#   ██║   ██║██╔══██╗██╔════╝      ██╔══██╗██╔═══██╗╚══██╔══╝
#   ██║   ██║██████╔╝███████╗      ██████╔╝██║   ██║   ██║   
#   ╚██╗ ██╔╝██╔═══╝ ╚════██║      ██╔══██╗██║   ██║   ██║   
#    ╚████╔╝ ██║     ███████║      ██████╔╝╚██████╔╝   ██║   
#     ╚═══╝  ╚═╝     ╚══════╝      ╚═════╝  ╚═════╝    ╚═╝   
#
#              ⚡ VPS-BOT ⚡  Made by EVILSAAD
# ============================================================

import discord
from discord.ext import commands
import os
import asyncio
import time
import random
import platform
import psutil
from datetime import datetime
from dotenv import load_dotenv

# ==================== LOAD ENV ====================
load_dotenv()

TOKEN           = os.getenv("DISCORD_TOKEN")
PREFIX          = os.getenv("PREFIX", "$")
BOT_NAME        = os.getenv("BOT_NAME", "VPS-BOT")
OWNER_IDS       = [int(x) for x in os.getenv("OWNER_IDS", "").split(",") if x.strip()]
ALLOWED_USERS   = [int(x) for x in os.getenv("ALLOWED_USERS", "").split(",") if x.strip()]
MAX_VPS_PER_USER= int(os.getenv("MAX_VPS_PER_USER", 3))
DEFAULT_SSH_PORT= int(os.getenv("DEFAULT_SSH_PORT", 22))
WATERMARK       = os.getenv("WATERMARK", "Made by EVILSAAD")

# ==================== BOT SETUP ====================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

VPS_DB = {}
START_TIME = time.time()

# ==================== COLORS & ANIMATIONS ====================
COLORS = {
    "success": 0x00FF7F,
    "error":   0xFF4444,
    "info":    0x00BFFF,
    "warn":    0xFFAA00,
    "vps":     0x9B59B6,
    "evil":    0x8A2BE2,
}

LOADING_FRAMES = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
ROCKET_FRAMES  = ["🚀","🛰️","✨","⚡","🔥"]


def progress_bar(percent: int, length: int = 15) -> str:
    filled = int(length * percent / 100)
    return f"[{'█'*filled}{'░'*(length-filled)}] {percent}%"


async def animate_loading(message: discord.Message, text: str, duration: float = 3.0):
    end = time.time() + duration
    i = 0
    while time.time() < end:
        frame = LOADING_FRAMES[i % len(LOADING_FRAMES)]
        try:
            await message.edit(content=f"{frame} {text}")
        except Exception:
            pass
        i += 1
        await asyncio.sleep(0.1)


async def animate_progress(message: discord.Message, title: str, duration: float = 4.0):
    steps = 20
    for s in range(steps + 1):
        percent = int((s / steps) * 100)
        try:
            await message.edit(content=f"**{title}**\n`{progress_bar(percent)}`")
        except Exception:
            pass
        await asyncio.sleep(duration / steps)


# ==================== EMBED BUILDER ====================
def main_embed(title, description="", color=COLORS["vps"]):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text=f"⚡ {BOT_NAME} • {WATERMARK}", icon_url=bot.user.avatar.url if bot.user and bot.user.avatar else None)
    return embed


def vps_embed(vps: dict, action: str = "info"):
    status_emoji = {
        "running":"🟢", "stopped":"🔴", "starting":"🟡",
        "stopping":"🟠", "restarting":"🔄", "reinstalling":"🔄",
        "suspended":"⛔"
    }
    emoji = status_emoji.get(vps.get("status","stopped"), "⚪")

    embed = discord.Embed(
        title=f"{emoji} VPS: `{vps['name']}`",
        color=COLORS["vps"] if vps.get("status")=="running" else COLORS["warn"],
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="🆔 VPS ID",     value=f"`{vps['id']}`", inline=True)
    embed.add_field(name="📊 Status",     value=f"`{vps.get('status','unknown').upper()}`", inline=True)
    embed.add_field(name="🌐 IP",         value=f"`{vps.get('ip','N/A')}`", inline=True)
    embed.add_field(name="🔌 SSH Port",   value=f"`{vps.get('port', DEFAULT_SSH_PORT)}`", inline=True)
    embed.add_field(name="👤 User",       value=f"`{vps.get('ssh_user','root')}`", inline=True)
    embed.add_field(name="💻 OS",         value=f"`{vps.get('os','Ubuntu 22.04')}`", inline=True)
    embed.add_field(name="🧠 RAM",        value=f"`{vps.get('ram','1GB')}`", inline=True)
    embed.add_field(name="💾 Disk",       value=f"`{vps.get('disk','10GB')}`", inline=True)
    embed.add_field(name="⚙️ CPU",        value=f"`{vps.get('cpu','1 vCPU')}`", inline=True)
    embed.add_field(name="📅 Created",    value=f"<t:{int(vps.get('created_at',time.time()))}:R>", inline=True)
    embed.add_field(name="⏱️ Uptime",     value=f"`{vps.get('uptime','N/A')}`", inline=True)
    embed.add_field(name="📦 Plan",       value=f"`{vps.get('plan','basic').upper()}`", inline=True)
    embed.set_footer(text=f"⚡ {BOT_NAME} • {WATERMARK}")
    return embed


# ==================== MOCK VPS MANAGER ====================
class VPSManager:
    """Yaha pe apna real VPS API (DigitalOcean / Vultr / AWS) integrate karo"""

    @staticmethod
    async def create_vps(user_id: int, name: str, plan: str = "basic") -> dict:
        plans = {
            "basic": {"ram":"1GB","disk":"10GB","cpu":"1 vCPU"},
            "pro":   {"ram":"2GB","disk":"25GB","cpu":"2 vCPU"},
            "ultra": {"ram":"4GB","disk":"50GB","cpu":"4 vCPU"},
        }
        p = plans.get(plan, plans["basic"])
        return {
            "id": f"vps-{random.randint(100000,999999)}",
            "name": name,
            "owner": user_id,
            "status": "running",
            "ip": f"{random.randint(10,200)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "port": DEFAULT_SSH_PORT,
            "ssh_user": "root",
            "ssh_password": f"pass_{random.randint(10000,99999)}",
            "os": "Ubuntu 22.04 LTS",
            "ram": p["ram"], "disk": p["disk"], "cpu": p["cpu"],
            "plan": plan,
            "created_at": time.time(),
            "uptime": "0m",
        }

    @staticmethod
    async def start_vps(vps):     await asyncio.sleep(1.0); vps["status"]="running"; return True
    @staticmethod
    async def stop_vps(vps):      await asyncio.sleep(1.0); vps["status"]="stopped"; return True
    @staticmethod
    async def restart_vps(vps):   vps["status"]="restarting"; await asyncio.sleep(1); vps["status"]="running"; return True
    @staticmethod
    async def reinstall_vps(vps, os_name):
        vps["status"]="reinstalling"; await asyncio.sleep(2)
        vps["os"]=os_name; vps["status"]="running"
        vps["ssh_password"]=f"pass_{random.randint(10000,99999)}"
        return True
    @staticmethod
    async def delete_vps(vps):    await asyncio.sleep(0.5); return True


vps_manager = VPSManager()


def get_user_vps(uid):       return VPS_DB.get(uid, [])
def is_owner(uid):           return uid in OWNER_IDS
def is_allowed(uid):         return (not ALLOWED_USERS) or uid in ALLOWED_USERS or is_owner(uid)


def find_vps(uid, query):
    for v in VPS_DB.get(uid, []):
        if v["id"] == query or v["name"].lower() == query.lower():
            return v
    return None


def find_any_vps(query):
    for lst in VPS_DB.values():
        for v in lst:
            if v["id"] == query or v["name"].lower() == query.lower():
                return v
    return None


def get_uptime():
    d = int(time.time() - START_TIME)
    h, r = divmod(d, 3600); m, s = divmod(r, 60)
    return f"{h}h {m}m {s}s"


# ==================== EVENTS ====================
@bot.event
async def on_ready():
    print(f"""
╔══════════════════════════════════════════════╗
║   ⚡ {BOT_NAME} IS ONLINE ⚡                  
║   Made by {WATERMARK}                        
║   User   : {bot.user}                        
║   ID     : {bot.user.id}                     
║   Guilds : {len(bot.guilds)}                 
║   Prefix : {PREFIX}                          
╚══════════════════════════════════════════════╝
    """)
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name=f"{PREFIX}help | {WATERMARK}"),
        status=discord.Status.online
    )
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Sync failed: {e}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(embed=main_embed("❌ Missing Argument", f"Use: `{PREFIX}help {ctx.command}`", COLORS["error"]))
    await ctx.send(embed=main_embed("❌ Error", f"```{error}```", COLORS["error"]))


# ==================== COMMANDS ====================

@bot.command(name="help", aliases=["h","menu","commands"])
async def help_cmd(ctx):
    embed = main_embed(
        f"⚡ {BOT_NAME} • Help Menu",
        f"**Prefix:** `{PREFIX}` • **Watermark:** `{WATERMARK}`\n\u200b"
    )
    embed.add_field(
        name="🚀 VPS Management",
        value=(
            f"`{PREFIX}deploy <name> [plan]` → Naya VPS banao\n"
            f"`{PREFIX}start <vps>` → Start karo\n"
            f"`{PREFIX}stop <vps>` → Stop karo\n"
            f"`{PREFIX}restart <vps>` → Restart karo\n"
            f"`{PREFIX}reinstall <vps> [os]` → OS reinstall\n"
            f"`{PREFIX}delete <vps>` → VPS delete\n"
            f"`{PREFIX}list` → Apne saare VPS\n"
            f"`{PREFIX}info <vps>` → Detail dekho\n"
            f"`{PREFIX}ssh <vps>` → SSH command"
        ),
        inline=False
    )
    embed.add_field(
        name="📊 System",
        value=(
            f"`{PREFIX}ping` → Latency\n"
            f"`{PREFIX}stats` → Bot stats\n"
            f"`{PREFIX}sysinfo` → Host machine info\n"
            f"`{PREFIX}uptime` → Bot uptime\n"
            f"`{PREFIX}invite` → Invite link\n"
            f"`{PREFIX}about` → About bot"
        ),
        inline=False
    )
    embed.add_field(
        name="👑 Owner Only",
        value=(
            f"`{PREFIX}allvps` → Sab ke VPS dekho\n"
            f"`{PREFIX}broadcast <msg>` → Broadcast\n"
            f"`{PREFIX}eval <code>` → Python eval"
        ),
        inline=False
    )
    await ctx.send(embed=embed)


# ============ DEPLOY ============
@bot.command(name="deploy", aliases=["create","new","dv"])
async def deploy_vps(ctx, name: str = None, plan: str = "basic"):
    if not is_allowed(ctx.author.id):
        return await ctx.send(embed=main_embed("⛔ Access Denied", "You are not allowed to use this bot.", COLORS["error"]))
    if not name:
        return await ctx.send(embed=main_embed("❌ Name Required", f"`{PREFIX}deploy <name> [basic|pro|ultra]`", COLORS["error"]))

    user_vps = get_user_vps(ctx.author.id)
    if len(user_vps) >= MAX_VPS_PER_USER and not is_owner(ctx.author.id):
        return await ctx.send(embed=main_embed("⚠️ Limit Reached", f"Max **{MAX_VPS_PER_USER}** VPS per user.", COLORS["warn"]))

    if plan.lower() not in ["basic","pro","ultra"]:
        return await ctx.send(embed=main_embed("❌ Invalid Plan", "Choose: `basic`, `pro`, `ultra`", COLORS["error"]))

    msg = await ctx.send(embed=main_embed("🚀 Deploying VPS...", "Initializing deployment pipeline...", COLORS["info"]))

    await animate_loading(msg, "Connecting to VPS provider...", 1.5)
    await animate_progress(msg, "Creating VPS instance", 2.0)
    await animate_loading(msg, "Configuring SSH access...", 1.5)
    await animate_loading(msg, "Installing OS & packages...", 1.5)
    await animate_progress(msg, "Finalizing deployment", 1.5)

    vps = await vps_manager.create_vps(ctx.author.id, name, plan.lower())
    VPS_DB.setdefault(ctx.author.id, []).append(vps)

    embed = vps_embed(vps, "deployed")
    embed.title = "✅ VPS Deployed Successfully!"
    embed.color = COLORS["success"]
    await msg.edit(content=None, embed=embed)
    await ctx.send(f"🎉 {ctx.author.mention} — **VPS ready!** Use `{PREFIX}ssh {vps['name']}` to connect.")


# ============ START ============
@bot.command(name="start", aliases=["boot","on"])
async def start_vps(ctx, *, vps_query: str = None):
    if not is_allowed(ctx.author.id):
        return await ctx.send(embed=main_embed("⛔ Access Denied", "Not allowed.", COLORS["error"]))
    if not vps_query:
        return await ctx.send(embed=main_embed("❌ Usage", f"`{PREFIX}start <vps>`", COLORS["error"]))

    vps = find_vps(ctx.author.id, vps_query) or (find_any_vps(vps_query) if is_owner(ctx.author.id) else None)
    if not vps:
        return await ctx.send(embed=main_embed("❌ VPS Not Found", f"No VPS named `{vps_query}`", COLORS["error"]))
    if vps["status"] == "running":
        return await ctx.send(embed=main_embed("⚠️ Already Running", f"VPS `{vps['name']}` already running.", COLORS["warn"]))

    msg = await ctx.send(embed=main_embed("🟡 Starting VPS...", f"Booting `{vps['name']}`...", COLORS["warn"]))
    await animate_loading(msg, "Powering on...", 1.2)
    await animate_progress(msg, "Starting services", 1.8)
    await vps_manager.start_vps(vps)

    embed = vps_embed(vps, "started")
    embed.color = COLORS["success"]
    await msg.edit(embed=embed)


# ============ STOP ============
@bot.command(name="stop", aliases=["shutdown","off"])
async def stop_vps(ctx, *, vps_query: str = None):
    if not is_allowed(ctx.author.id):
        return await ctx.send(embed=main_embed("⛔ Access Denied", "Not allowed.", COLORS["error"]))
    if not vps_query:
        return await ctx.send(embed=main_embed("❌ Usage", f"`{PREFIX}stop <vps>`", COLORS["error"]))

    vps = find_vps(ctx.author.id, vps_query)
    if not vps:
        return await ctx.send(embed=main_embed("❌ VPS Not Found", f"No VPS named `{vps_query}`", COLORS["error"]))
    if vps["status"] == "stopped":
        return await ctx.send(embed=main_embed("⚠️ Already Stopped", f"VPS `{vps['name']}` already stopped.", COLORS["warn"]))

    msg = await ctx.send(embed=main_embed("🟠 Stopping VPS...", f"Shutting down `{vps['name']}`...", COLORS["warn"]))
    await animate_loading(msg, "Sending shutdown signal...", 1.2)
    await animate_progress(msg, "Stopping services", 1.8)
    await vps_manager.stop_vps(vps)

    embed = vps_embed(vps, "stopped")
    embed.color = COLORS["warn"]
    await msg.edit(embed=embed)


# ============ RESTART ============
@bot.command(name="restart", aliases=["reboot","rb"])
async def restart_vps(ctx, *, vps_query: str = None):
    if not is_allowed(ctx.author.id):
        return await ctx.send(embed=main_embed("⛔ Access Denied", "Not allowed.", COLORS["error"]))
    if not vps_query:
        return await ctx.send(embed=main_embed("❌ Usage", f"`{PREFIX}restart <vps>`", COLORS["error"]))

    vps = find_vps(ctx.author.id, vps_query)
    if not vps:
        return await ctx.send(embed=main_embed("❌ VPS Not Found", f"No VPS named `{vps_query}`", COLORS["error"]))

    msg = await ctx.send(embed=main_embed("🔄 Restarting VPS...", f"Rebooting `{vps['name']}`...", COLORS["info"]))
    await animate_loading(msg, "Sending reboot command...", 1.2)
    await animate_progress(msg, "Rebooting OS", 2.0)
    await animate_loading(msg, "Waiting for SSH daemon...", 1.2)
    await vps_manager.restart_vps(vps)

    embed = vps_embed(vps, "restarted")
    embed.color = COLORS["success"]
    await msg.edit(embed=embed)


# ============ REINSTALL ============
@bot.command(name="reinstall", aliases=["reinstallos","os"])
async def reinstall_vps(ctx, vps_query: str = None, *, os_name: str = "Ubuntu 22.04"):
    if not is_allowed(ctx.author.id):
        return await ctx.send(embed=main_embed("⛔ Access Denied", "Not allowed.", COLORS["error"]))
    if not vps_query:
        return await ctx.send(embed=main_embed(
            "❌ Usage",
            f"`{PREFIX}reinstall <vps> [OS]`\n\n**Available OS:**\n"
            "Ubuntu 22.04 / Ubuntu 20.04 / Debian 12 / Debian 11 / "
            "CentOS 9 / AlmaLinux 9 / Rocky Linux 9 / Windows Server 2022",
            COLORS["error"]
        ))

    vps = find_vps(ctx.author.id, vps_query)
    if not vps:
        return await ctx.send(embed=main_embed("❌ VPS Not Found", f"No VPS named `{vps_query}`", COLORS["error"]))

    msg = await ctx.send(embed=main_embed("🔄 Reinstalling OS...", f"**VPS:** `{vps['name']}`\n**OS:** `{os_name}`", COLORS["info"]))
    await animate_loading(msg, "Creating snapshot backup...", 1.2)
    await animate_progress(msg, "Wiping disk", 1.8)
    await animate_loading(msg, "Downloading OS image...", 1.8)
    await animate_progress(msg, "Installing OS", 2.5)
    await animate_loading(msg, "Configuring SSH...", 1.2)
    await vps_manager.reinstall_vps(vps, os_name)

    embed = vps_embed(vps, "reinstalled")
    embed.color = COLORS["success"]
    embed.add_field(name="🆕 New OS",        value=f"`{os_name}`", inline=False)
    embed.add_field(name="🔐 New Password",  value=f"```{vps['ssh_password']}```", inline=False)
    await msg.edit(content=None, embed=embed)


# ============ DELETE ============
@bot.command(name="delete", aliases=["destroy","rm"])
async def delete_vps(ctx, *, vps_query: str = None):
    if not is_allowed(ctx.author.id):
        return await ctx.send(embed=main_embed("⛔ Access Denied", "Not allowed.", COLORS["error"]))
    if not vps_query:
        return await ctx.send(embed=main_embed("❌ Usage", f"`{PREFIX}delete <vps>`", COLORS["error"]))

    vps = find_vps(ctx.author.id, vps_query)
    if not vps:
        return await ctx.send(embed=main_embed("❌ VPS Not Found", f"No VPS named `{vps_query}`", COLORS["error"]))

    confirm = await ctx.send(embed=main_embed(
        "⚠️ Confirm Deletion",
        f"Delete VPS `{vps['name']}`? **Cannot be undone!**\n\nReact ✅ = Confirm | ❌ = Cancel (30s)",
        COLORS["warn"]
    ))
    await confirm.add_reaction("✅"); await confirm.add_reaction("❌")

    def check(r, u):
        return u == ctx.author and str(r.emoji) in ["✅","❌"] and r.message.id == confirm.id

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=30.0, check=check)
    except asyncio.TimeoutError:
        return await confirm.edit(embed=main_embed("⌛ Timed Out", "Deletion cancelled.", COLORS["warn"]))

    if str(reaction.emoji) == "❌":
        return await confirm.edit(embed=main_embed("✅ Cancelled", f"VPS `{vps['name']}` is safe.", COLORS["success"]))

    msg = await confirm.edit(embed=main_embed("🗑️ Deleting VPS...", f"Removing `{vps['name']}`...", COLORS["error"]))
    await animate_progress(msg, "Deleting VPS", 1.8)
    await vps_manager.delete_vps(vps)

    VPS_DB[ctx.author.id].remove(vps)
    await msg.edit(embed=main_embed("🗑️ VPS Deleted", f"VPS `{vps['name']}` has been deleted.", COLORS["success"]))


# ============ LIST ============
@bot.command(name="list", aliases=["ls","myvps","vpslist"])
async def list_vps(ctx):
    vps_list = get_user_vps(ctx.author.id)
    if not vps_list:
        return await ctx.send(embed=main_embed("📭 No VPS", f"You don't have any VPS.\nUse `{PREFIX}deploy <name>` to create one!", COLORS["info"]))

    embed = main_embed(f"📋 Your VPS ({len(vps_list)})", f"Total: **{len(vps_list)}** VPS", COLORS["vps"])
    for v in vps_list:
        emoji = {"running":"🟢","stopped":"🔴","starting":"🟡","stopping":"🟠","reinstalling":"🔄","restarting":"🔄"}.get(v["status"],"⚪")
        embed.add_field(
            name=f"{emoji} {v['name']}",
            value=f"**ID:** `{v['id']}`\n**IP:** `{v['ip']}:{v['port']}`\n**OS:** `{v['os']}`\n**Plan:** `{v['plan'].upper()}`",
            inline=True
        )
    await ctx.send(embed=embed)


# ============ INFO ============
@bot.command(name="info", aliases=["vpsinfo","i"])
async def info_vps(ctx, *, vps_query: str = None):
    if not vps_query:
        return await ctx.send(embed=main_embed("❌ Usage", f"`{PREFIX}info <vps>`", COLORS["error"]))
    vps = find_vps(ctx.author.id, vps_query)
    if not vps:
        return await ctx.send(embed=main_embed("❌ VPS Not Found", f"No VPS named `{vps_query}`", COLORS["error"]))
    await ctx.send(embed=vps_embed(vps, "info"))


# ============ SSH ============
@bot.command(name="ssh", aliases=["connect","sshx"])
async def ssh_vps(ctx, *, vps_query: str = None):
    if not is_allowed(ctx.author.id):
        return await ctx.send(embed=main_embed("⛔ Access Denied", "Not allowed.", COLORS["error"]))
    if not vps_query:
        return await ctx.send(embed=main_embed("❌ Usage", f"`{PREFIX}ssh <vps>`", COLORS["error"]))
    vps = find_vps(ctx.author.id, vps_query)
    if not vps:
        return await ctx.send(embed=main_embed("❌ VPS Not Found", f"No VPS named `{vps_query}`", COLORS["error"]))
    if vps["status"] != "running":
        return await ctx.send(embed=main_embed("⚠️ VPS Not Running", f"Start it first: `{PREFIX}start {vps['name']}`", COLORS["warn"]))

    embed = main_embed("🔐 SSH Credentials", f"VPS: `{vps['name']}`", COLORS["success"])
    embed.add_field(name="🌐 Host",     value=f"`{vps['ip']}`", inline=True)
    embed.add_field(name="🔌 Port",     value=f"`{vps['port']}`", inline=True)
    embed.add_field(name="👤 User",     value=f"`{vps['ssh_user']}`", inline=True)
    embed.add_field(name="🔑 Password", value=f"`{vps['ssh_password']}`", inline=True)
    embed.add_field(
        name="💻 Terminal Command",
        value=f"```bash\nssh {vps['ssh_user']}@{vps['ip']} -p {vps['port']}\n```",
        inline=False
    )
    embed.add_field(
        name="📱 Termux (Mobile SSH)",
        value=f"```bash\npkg install openssh\nssh {vps['ssh_user']}@{vps['ip']} -p {vps['port']}\n```",
        inline=False
    )
    embed.set_footer(text=f"⚠️ Delete this message after saving! | {WATERMARK}")

    try:
        await ctx.author.send(embed=embed)
        await ctx.send(embed=main_embed("📩 Sent!", "SSH credentials sent to your DM.", COLORS["success"]))
    except Exception:
        await ctx.send(embed=embed)


# ============ PING ============
@bot.command(name="ping", aliases=["latency"])
async def ping_cmd(ctx):
    msg = await ctx.send(embed=main_embed("🏓 Pinging...", "Calculating latency...", COLORS["info"]))
    await animate_loading(msg, "Measuring...", 1.0)
    latency = round(bot.latency * 1000)
    await msg.edit(embed=main_embed("🏓 Pong!", f"**Latency:** `{latency}ms`", COLORS["success"]))


# ============ STATS ============
@bot.command(name="stats", aliases=["botinfo","bi"])
async def stats_cmd(ctx):
    total_vps = sum(len(v) for v in VPS_DB.values())
    running   = sum(1 for lst in VPS_DB.values() for v in lst if v["status"]=="running")
    embed = main_embed(f"📊 {BOT_NAME} Statistics", "", COLORS["info"])
    embed.add_field(name="🏠 Servers",   value=f"`{len(bot.guilds)}`", inline=True)
    embed.add_field(name="👥 Users",     value=f"`{sum(g.member_count for g in bot.guilds)}`", inline=True)
    embed.add_field(name="📡 Latency",   value=f"`{round(bot.latency*1000)}ms`", inline=True)
    embed.add_field(name="🖥️ Total VPS", value=f"`{total_vps}`", inline=True)
    embed.add_field(name="🟢 Running",   value=f"`{running}`", inline=True)
    embed.add_field(name="🔴 Stopped",   value=f"`{total_vps-running}`", inline=True)
    embed.add_field(name="🐍 Python",    value=f"`{platform.python_version()}`", inline=True)
    embed.add_field(name="📚 discord.py",value=f"`{discord.__version__}`", inline=True)
    embed.add_field(name="⏱️ Uptime",    value=f"`{get_uptime()}`", inline=True)
    await ctx.send(embed=embed)


# ============ UPTIME ============
@bot.command(name="uptime")
async def uptime_cmd(ctx):
    await ctx.send(embed=main_embed("⏱️ Uptime", f"Bot has been online for: `{get_uptime()}`", COLORS["info"]))


# ============ SYSINFO ============
@bot.command(name="sysinfo", aliases=["system"])
async def sysinfo_cmd(ctx):
    cpu  = psutil.cpu_percent(interval=0.5)
    ram  = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    embed = main_embed("💻 System Information", "Host machine stats", COLORS["info"])
    embed.add_field(name="🖥️ OS",     value=f"`{platform.system()} {platform.release()}`", inline=True)
    embed.add_field(name="🐍 Python", value=f"`{platform.python_version()}`", inline=True)
    embed.add_field(name="⚙️ CPU",    value=f"`{cpu}%`", inline=True)
    embed.add_field(name="🧠 RAM",    value=f"`{ram.percent}% ({ram.used//(1024**2)}/{ram.total//(1024**2)} MB)`", inline=True)
    embed.add_field(name="💾 Disk",   value=f"`{disk.percent}% ({disk.used//(1024**3)}/{disk.total//(1024**3)} GB)`", inline=True)
    embed.add_field(name="🏗️ Arch",   value=f"`{platform.machine()}`", inline=True)
    await ctx.send(embed=embed)


# ============ INVITE ============
@bot.command(name="invite", aliases=["inv"])
async def invite_cmd(ctx):
    link = discord.utils.oauth_url(bot.user.id, permissions=discord.Permissions(administrator=True))
   