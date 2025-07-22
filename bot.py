import aiohttp
from aiohttp import web
async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
import discord
import asyncio
from discord import app_commands
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
import pytz
import re
# import time

load_dotenv()
DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

uri = os.getenv("uri")

client = MongoClient(uri)

async def ping_self():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            async with aiohttp.ClientSession() as s:
                await s.get(os.getenv("url"))
        except:
            pass
        await asyncio.sleep(1200)

async def wait():
    seoul = pytz.timezone("Asia/Seoul")
    now = datetime.now(seoul)
    nowtime = now.replace(hour=7, minute=0, second=0, microsecond=0)
    if now < nowtime:
        delta = nowtime - now
    else:
        nexttime = nowtime + timedelta(days=1)
        delta = nexttime - now
    return delta.total_seconds()

async def lunch():
    channel = bot.get_channel(int(os.getenv("channel")))
    if channel:
        try:
            seoul = pytz.timezone("Asia/Seoul")
            weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
            while not bot.is_closed():
                now = datetime.now(seoul)
                if now.hour == 7:
                    today_weekday_index = 4 - now.weekday()
                    if today_weekday_index < 5:
                        text = ""
                        if today_weekday_index == 0:
                            text += "## D - Day\n"
                        elif today_weekday_index > 0:
                            text += f"## D - {today_weekday_index}\n"
                        today = now.strftime('%Y%m%d')
                        text += f"### {today[:4]}/{today[4:6]}/{today[6:]}\n\n"
                        url = f"https://open.neis.go.kr/hub/mealServiceDietInfo?ATPT_OFCDC_SC_CODE={os.getenv("ATPT_OFCDC_SC_CODE")}&SD_SCHUL_CODE={os.getenv("SD_SCHUL_CODE")}&MLSV_YMD={today}&Type=Json"
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    pretty = json.dumps(data, ensure_ascii=False, indent=2)
                                    if "mealServiceDietInfo" in data:
                                        count = data["mealServiceDietInfo"][0]["head"][0]["list_total_count"]
                                        for i in range(0, count):
                                            type1 = clean_text(data["mealServiceDietInfo"][1]["row"][i]["MMEAL_SC_NM"])
                                            text1 = clean_text(data["mealServiceDietInfo"][1]["row"][i]["DDISH_NM"])
                                            text += f'**{type1}**```{text1}```\n'
                                        await channel.send(text)
                                    else:
                                        await channel.send(f"{text} 내용이 없어요.")
                                else:
                                    await channel.send(f"요청 실패 {response.status}")
                sleep_time = await wait()
                await asyncio.sleep(sleep_time)
        except Exception as e:
            await channel.send(f"급식 오류 발생 {e}")

async def hello():
    channel = bot.get_channel(int(os.getenv("channel")))
    if channel:
        await channel.send("집가고싶다.")

db = client["test"]
collection = db["test"]

def clean_text(text):
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    return text

@bot.event
async def on_ready():
    await tree.sync()
    await bot.change_presence(activity=discord.Game("집 생각"))
    print("준비")
    bot.loop.create_task(start_web_server())
    bot.loop.create_task(ping_self())
    bot.loop.create_task(lunch())
    bot.loop.create_task(hello())


@tree.command(name="청소", description="메시지 삭제")
@app_commands.describe(count="삭제할 메시지 갯수")
async def clean(interaction: discord.Interaction, count: app_commands.Range[int, 1]):
    try:
        if interaction.user.guild_permissions.manage_messages:
            await interaction.channel.purge(limit=count)
        else:
            await interaction.response.send_message("메시지 관리 권한이 없습니다.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message("삭제 오류 발생")


@tree.command(name="리스트추가", description="목록 추가")
@app_commands.describe(content="내용", user="완료")
async def insert(interaction: discord.Interaction, content: str, user: str = ""):
    try:
        collection.insert_one({"name": interaction.user.name, "content" : content, "user" : user})
        await interaction.response.send_message("리스트 추가 완료", ephemeral=True)
    except Exception as e:
            await interaction.response.send_message("리스트 추가 오류 발생")


@tree.command(name="리스트", description="목록")
async def list(interaction: discord.Interaction):
    try:
        messages = collection.find().sort("_id", -1)
        embed = discord.Embed(title="할일", description="해야할 일", color=0x00ff00)
        embed.set_footer(text="made by")
        
        count = 0
        for msg in messages:
            content = msg.get("content")
            name = msg.get("name")
            user = msg.get("user")
            id = msg.get("_id")
            embed.add_field(name= f"{name} ({id})" if user == "" else f"{name} ({user}) ~~({id})~~", value= content, inline=False)
            count += 1
        if count == 0:
            await interaction.response.send_message("리스트가 없습니다.", ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message("리스트 오류 발생")


@tree.command(name="리스트삭제", description="목록 삭제")
@app_commands.describe(id="목록 아이디")
async def delete(interaction: discord.Interaction, id: str):
    adminid = int(os.getenv("admin"))
    adminid2 = int(os.getenv("admin2"))
    if interaction.user.id == adminid or interaction.user.id == adminid2:
        try:
            result = collection.delete_one({"_id" : ObjectId(id)})
            if result.deleted_count == 1:
                await interaction.response.send_message("목록 삭제 완료", ephemeral=True)
            else:
                await interaction.response.send_message("목록 아이디를 찾을 수 없습니다.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("리스트 삭제 오류 발생")
    else:
        await interaction.response.send_message("삭제 권한이 없습니다.", ephemeral=True)
        return


@tree.command(name="리스트수정", description="목록 수정")
@app_commands.describe(id="목록 아이디", content="내용", user="완료")
async def update(interaction: discord.Interaction, id: str, content: str = "", user: str = ""):
    try:
        message = collection.find_one({"_id": ObjectId(id)})
        if message:
            if content == "":
                content = message.get("content")
            result = collection.update_one({"_id" : ObjectId(id)}, {"$set" : {"content" : content, "user" : user}})
            if result.matched_count == 1:
                await interaction.response.send_message("목록 수정 완료", ephemeral=True)
        else:
            await interaction.response.send_message("목록 아이디를 찾을 수 없습니다.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message("리스트 수정 오류 발생")


@tree.command(name="선택", description="선택")
@app_commands.describe(user="선택")
async def select(interaction: discord.Interaction, user: discord.Member):
    try:
        await interaction.response.send_message(f"{user.name}선택")
    except Exception as e:
        await interaction.response.send_message("선택 오류 발생")


@tree.command(name="집", description="집")
async def select(interaction: discord.Interaction):
    try:
        await interaction.response.send_message("가고 싶다")
    except Exception as e:
        await interaction.response.send_message("오류 발생")


@tree.command(name="말", description="horse")
@app_commands.describe(content="내용")
async def select(interaction: discord.Interaction, content: str):
    try:
        await interaction.response.send_message(content)
    except Exception as e:
        await interaction.response.send_message("오류 발생")


@tree.command(name="학습", description="배움")
@app_commands.describe(title="말", content="내용")
async def select(interaction: discord.Interaction, title: str, content: str):
    try:
        data = load_data()
        data[title] = content
        save_data(data)
        await interaction.response.send_message("학습 완료")
    except Exception as e:
        await interaction.response.send_message("오류 발생")


@bot.event
async def on_message(message):
    try:
        if message.author == bot.user:
            return
        title = message.content
        data = load_data()
        if title in data:
            await message.channel.send(data[title])
    except Exception as e:
        await message.channel.send("오류 발생")


@tree.command(name="학습전체보기", description="배움")
async def select(interaction: discord.Interaction):
    try:
        data = load_data()
        if data:
            result = '\n'.join([f'{k}: {v}' for k, v in data.items()])
            await interaction.response.send_message(result)
        else:
            await interaction.response.send_message("배운적이 없어요..")
    except Exception as e:
        await interaction.response.send_message("오류 발생")


@tree.command(name="학습삭제", description="배움")
@app_commands.describe(title="말")
async def select(interaction: discord.Interaction, title: str):
    try:
        data = load_data()
        if title in data:
            del data[title]
            save_data(data)
            await interaction.response.send_message("기억속에서 지웠어요.")
        else:
            await interaction.response.send_message("배운적이 없어요..")
    except Exception as e:
        await interaction.response.send_message("오류 발생")


@tree.command(name="급식", description="급식")
async def select(interaction: discord.Interaction):
    try:
        seoul = pytz.timezone("Asia/Seoul")
        today = datetime.now(seoul).strftime('%Y%m%d')
        url = f"https://open.neis.go.kr/hub/mealServiceDietInfo?ATPT_OFCDC_SC_CODE={os.getenv("ATPT_OFCDC_SC_CODE")}&SD_SCHUL_CODE={os.getenv("SD_SCHUL_CODE")}&MLSV_YMD={today}&Type=Json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    pretty = json.dumps(data, ensure_ascii=False, indent=2)
                    if "mealServiceDietInfo" in data:
                        count = data["mealServiceDietInfo"][0]["head"][0]["list_total_count"]
                        text = ""
                        for i in range(0, count):
                            type1 = clean_text(data["mealServiceDietInfo"][1]["row"][i]["MMEAL_SC_NM"])
                            text1 = clean_text(data["mealServiceDietInfo"][1]["row"][i]["DDISH_NM"])
                            text += f'**{type1}**```{text1}```\n'
                        await interaction.response.send_message(text)
                    else:
                        await interaction.response.send_message("내용이 없어요.")
                else:
                    await interaction.response.send_message(f"요청 실패 {response.status}")
    except Exception as e:
        await interaction.response.send_message(f"오류 발생 {e}", ephemeral=True)


@tree.command(name="닉네임변경", description="닉네임 변경")
@app_commands.describe(nick="닉네임")
async def nickname(interaction: discord.Interaction, nick: str):
    # member = interaction.user
    # bot_member = interaction.guild.me  # 봇의 GuildMember 객체

    # # 권한 체크: 봇이 닉네임 관리 권한을 가지고 있는가?
    # has_permission = bot_member.guild_permissions.manage_nicknames

    # # 역할 계층 체크: 봇의 역할이 대상 유저보다 높은가?
    # bot_top_role = bot_member.top_role
    # user_top_role = member.top_role
    # is_higher = bot_top_role > user_top_role

    # if not has_permission:
    #     await interaction.response.send_message("❌ 닉네임을 변경할 권한이 없어요 (Manage Nicknames)", ephemeral=True)
    #     return

    # if not is_higher and member != bot_member:
    #     await interaction.response.send_message("❌ 역할 순위 때문에 해당 사용자의 닉네임을 변경할 수 없어요.", ephemeral=True)
    #     return

    # try:
    #     await member.edit(nick=이름)
    #     await interaction.response.send_message(f"✅ {member.mention}님의 닉네임이 **{이름}**(으)로 변경되었어요!", ephemeral=True)
    # except Exception as e:
    #     await interaction.response.send_message(f"⚠️ 오류 발생: {str(e)}", ephemeral=True)
    try:
        member = interaction.user
        await member.edit(nick=nick)
        await interaction.response.send_message("닉네임 변경을 완료했어요.")
    except discord.Forbidden:
        await interaction.response.send_message("권한이 없어요.")
    except Exception as e:
        await interaction.response.send_message("오류 발생")


@tree.command(name="인증", description="인증")
@app_commands.describe(oauth="인증번호")
async def nickname(interaction: discord.Interaction, oauth: str):
    try:
        url=f"{os.getenv("url2")}{oauth}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    embed = discord.Embed(title = "유저정보", description="유저 정보", color=0x00ff00)
                    embed.add_field(name="이름", value=data["username"])
                    embed.add_field(name="아이디", value=data["userid"])
                    embed.add_field(name="링크", value=f"[바로가기](https://www.roblox.com/ko/users/{data["userid"]})")
                    member = interaction.user
                    await member.edit(nick=data["username"])
                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.response.send_message(f"요청 실패 {response.status}")
    except Exception as e:
        await interaction.response.send_message("오류 발생")

bot.run(os.getenv("token"))
