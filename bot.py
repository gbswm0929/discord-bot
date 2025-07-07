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
from datetime import datetime

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

db = client["test"]
collection = db["test"]

@bot.event
async def on_ready():
    await tree.sync()
    await bot.change_presence(activity=discord.Game("집 생각"))
    print("준비")
    bot.loop.create_task(start_web_server())
    bot.loop.create_task(ping_self())


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


@tree.command(name="학습보기", description="배움")
@app_commands.describe(title="말")
async def select(interaction: discord.Interaction, title: str):
    try:
        data = load_data()
        if title in data:
            await interaction.response.send_message(data[title])
        else:
            await interaction.response.send_message("이거는 안 배웠어요..")
    except Exception as e:
        await interaction.response.send_message("오류 발생")


@tree.command(name="학습전체보기", description="배움")
async def select(interaction: discord.Interaction):
    try:
        data = load_data()
        if data:
            result = '\n'.join([f'- {k}: {v}' for k, v in data.items()])
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
        today = datetime.now().strftime('%Y%m%d')
        url = f"https://open.neis.go.kr/hub/mealServiceDietInfo?ATPT_OFCDC_SC_CODE=R10&SD_SCHUL_CODE=8750829&MLSV_YMD={today}&Type=Json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    pretty = json.dumps(data, ensure_ascii=False, indent=2)
                    print(pretty["head"]["list_total_count"])
                    # if len(pretty) > 1900:
                    #     await interaction.response.send_message(f"```{pretty[:1900]}```")
                    # else:
                    #     await interaction.response.send_message(f"```{pretty}```")
                else:
                    await interaction.response.send_message(f"요청 실패 {response.status}")
    except Exception as e:
        await interaction.response.send_message(f"오류 발생 {e}", ephemeral=True)

bot.run(os.getenv("token"))
