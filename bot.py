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

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

uri = os.getenv("uri")

client = MongoClient(uri)

async def ping_self():
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            async with aiohttp.ClientSession() as s:
                await s.get(os.environ["https://mute-gianina-gbswst0929-dd427436.koyeb.app"])
        except:
            pass
        await asyncio.sleep(1200)

db = client["test"]
collection = db["test"]

@bot.event
async def on_ready():
    await tree.sync()
    print("준비")
    client.loop.create_task(start_web_server())
    client.loop.create_task(ping_self())


@tree.command(name="청소", description="메시지 삭제")
@app_commands.describe(count="삭제할 메시지 갯수")
async def clean(interaction: discord.Interaction, count: app_commands.Range[int, 1]):
    if interaction.user.guild_permissions.manage_messages:
        await interaction.channel.purge(limit=count)
    else:
        await interaction.response.send_message("메시지 관리 권한이 없습니다.", ephemeral=True)


@tree.command(name="리스트추가", description="목록 추가")
@app_commands.describe(content="내용", user="완료")
async def insert(interaction: discord.Interaction, content: str, user: str = ""):
    collection.insert_one({"name": interaction.user.name, "content" : content, "user" : user})
    await interaction.response.send_message("리스트 추가 완료", ephemeral=True)


@tree.command(name="리스트", description="목록")
async def list(interaction: discord.Interaction):
    messages = collection.find().sort("_id", -1)
    embed = discord.Embed(title="타이틀", description="설명", color=0x00ff00)
    embed.set_footer(text="made by abc")
    
    count = 0
    for msg in messages:
        content = msg.get("content")
        name = msg.get("name")
        user = msg.get("user")
        id = msg.get("_id")
        embed.add_field(name= f"{content} ({name})" if user == "" else f"{content} ({name}) ({user})", value= id if user == "" else f"~~{id}~~", inline=False)
        count += 1
    if count == 0:
        await interaction.response.send_message("리스트가 없습니다.", ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="리스트삭제", description="목록 삭제")
@app_commands.describe(id="목록 아이디")
async def delete(interaction: discord.Interaction, id: str):
    adminid = 1315621638733172808
    if interaction.user.id == adminid:
        try:
            result = collection.delete_one({"_id" : ObjectId(id)})
            if result.deleted_count == 1:
                await interaction.response.send_message("목록 삭제 완료", ephemeral=True)
            else:
                await interaction.response.send_message("목록 아이디를 찾을 수 없습니다.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("오류 발생", ephemeral=True)
    else:
        await interaction.response.send_message("삭제 권한이 없습니다.", ephemeral=True)
        return


@tree.command(name="리스트수정", description="목록 수정")
@app_commands.describe(id="목록 아이디", content="내용", user="완료")
async def update(interaction: discord.Interaction, id: str, content: str = "", user: str = ""):
    if content == "" and user == "":
        await interaction.response.send_message("아무 것도 입력하지 않았습니다.", ephemeral=True)
    else:
        message = collection.find_one({"_id": ObjectId(id)})
        if message:
            if content == "":
                content = message.get("content")
            result = collection.update_one({"_id" : ObjectId(id)}, {"$set" : {"content" : content, "user" : user}})
            if result.matched_count == 1:
                await interaction.response.send_message("목록 수정 완료", ephemeral=True)
        else:
            await interaction.response.send_message("목록 아이디를 찾을 수 없습니다.", ephemeral=True)


@tree.command(name="선택", description="선택")
@app_commands.describe(user="선택")
async def select(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.send_message(f"{user.name}선택")


bot.run(os.getenv("token"))
