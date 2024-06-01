import logging
import tempfile

import discord
from discord.commands import slash_command
from discord.ext import commands

from db.package.crud import participant as participant_crud
from db.package.session import get_db


class PersonalInfoInputModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="氏名", placeholder="山田太郎"))
        self.add_item(discord.ui.InputText(label="所属学校名", placeholder="〇〇大学"))

    async def callback(self, interaction: discord.Interaction):
        fullname = self.children[0].value
        univ_name = self.children[1].value

        with get_db() as db:
            participant_crud.create(db, fullname=fullname, univ_name=univ_name, discord_account_id=interaction.user.id)

        # ephemeralでresponse
        await interaction.response.send_message("参加者情報を登録しました！", ephemeral=True)


class AddRoleModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(
            style=discord.InputTextStyle.long,
            label="対象ロールCSV",
            placeholder="userID,roleID"
        ))

    async def callback(self, interaction: discord.Interaction):
        csv_data = self.children[0].value
        csv_data = csv_data.split("\n")
        csv_data = [line.split(",") for line in csv_data]

        errors = []

        for user_id, role_id in csv_data:
            try:
                user_id = int(user_id.strip())
                role_id = int(role_id.strip())
            except ValueError:
                errors.append(f"不正な値：{user_id}, {role_id}")
                continue

            user = interaction.guild.get_member(user_id)
            role = interaction.guild.get_role(role_id)

            if user is None:
                try:
                    user = await interaction.guild.fetch_member(user_id)
                except discord.NotFound:
                    user = None

            if user is None or role is None:
                errors.append(f"不明：{user_id}, {role_id}")
                continue

            await user.add_roles(role)

        if len(errors) > 0:
            msg = '\n'.join(errors)
            await interaction.response.send_message(f"一部の値でエラーが発生しました。\n```\n{msg}\n```", ephemeral=True)

        else:
            await interaction.response.send_message("ロールを追加しました！", ephemeral=True)


class PersonalInfoAcquireView(discord.ui.View):
    def __init__(self):
        # disable timeout for persistent view
        super().__init__(timeout=None)

        # set logger
        self.logger = logging.getLogger(type(self).__name__)

    @discord.ui.button(label="参加者情報を入力する",
                       style=discord.ButtonStyle.primary, custom_id="personal_info_acquire_start")
    async def acquire_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(PersonalInfoInputModal(title="参加者情報入力"))


class PersonalInfoAcquirer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(PersonalInfoAcquireView())

    @slash_command(name="create_personal_info_button", description="参加者情報入力パネルを生成")
    @commands.has_permissions(administrator=True)
    async def create_personal_info_button(self, ctx: discord.commands.context.ApplicationContext):
        await ctx.respond("参加者情報の入力・更新は以下のボタンから行ってください。", view=PersonalInfoAcquireView())

    @slash_command(name="list_participants", description="参加者情報をCSVで出力")
    @commands.has_permissions(administrator=True)
    async def list_participants(self, ctx: discord.commands.context.ApplicationContext):
        with get_db() as db:
            participants = participant_crud.get_all(db)

        csv_data = "氏名,所属学校名,DiscordID,discord表示名,discordユーザ名\n"
        for participant in participants:

            csv_data += f"{participant.fullname},{participant.univ_name},"

            user: discord.Member | None = ctx.guild.get_member(participant.discord_account_id)
            if user is None:
                try:
                    user = await ctx.guild.fetch_member(participant.discord_account_id)
                except discord.NotFound:
                    user = None

            if user is None:
                csv_data += f"{participant.discord_account_id},不明,不明\n"
            else:
                csv_data += f"{participant.discord_account_id},{user.nick},{user.name}\n"

        with tempfile.TemporaryFile("w", encoding="utf-8") as f:
            f.write(csv_data)
            f.seek(0)
            await ctx.respond(file=discord.File(f.name, filename="participants.csv"))

    @slash_command(name="add_role", description="ユーザにロールを追加")
    @commands.has_permissions(administrator=True)
    async def add_role(self, ctx: discord.commands.context.ApplicationContext):
        await ctx.send_modal(AddRoleModal(title="ロール追加"))


def setup(bot):
    return bot.add_cog(PersonalInfoAcquirer(bot))
