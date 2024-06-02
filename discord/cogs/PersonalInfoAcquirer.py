import tempfile

import discord
from discord.commands import slash_command
from discord.ext import commands

from db.package.crud import participant as participant_crud
from db.package.models import Participant
from db.package.session import get_db


class PersonalInfoInputModal(discord.ui.Modal):
    """
    参加者情報入力モーダル

    PersonalInfoAcquireViewのButtonのcallbackとして呼び出され、利用者の情報を収集する
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="氏名", placeholder="山田太郎"))
        self.add_item(discord.ui.InputText(label="所属学校名", placeholder="〇〇大学"))

    async def callback(self, interaction: discord.Interaction):
        # 入力された情報を取得
        fullname: str | None = self.children[0].value
        univ_name: str | None = self.children[1].value

        if fullname is None or univ_name is None:
            await interaction.response.send_message("入力された情報が不正です。", ephemeral=True)
            return

        # 取得した情報をDBに登録
        # 空白除去等はCRUD側で実施 ／ エラーハンドリングはlistenerで実施する
        with get_db() as db:
            # 既に登録されている場合は更新、されていない場合は新規登録
            # バリデーションエラーが発生した場合はエラーメッセージを表示
            if participant_crud.create_or_update(db, fullname, univ_name, interaction.user.id) is None:
                await interaction.response.send_message("情報の登録に失敗しました。", ephemeral=True)
                return

        # ephemeralでresponse
        await interaction.response.send_message("参加者情報を登録しました！", ephemeral=True)


class AddRoleModal(discord.ui.Modal):
    """
    ロール追加モーダル

    PersonalInfoAcquireViewのButtonのcallbackとして呼び出され、CSV形式でユーザIDとロールIDを受け取り、
    ユーザにロールを追加する
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(
            style=discord.InputTextStyle.long,
            label="対象ロールCSV",
            placeholder="userID,roleID"
        ))

    async def callback(self, interaction: discord.Interaction):
        # csv形式のデータをパース
        raw_csv_data: str | None = self.children[0].value

        if raw_csv_data is None:
            await interaction.response.send_message("入力された情報が不正です。", ephemeral=True)
            return

        csv_data: list[list[str]] = [line.split(",") for line in raw_csv_data.split("\n")]

        errors: list[str] = []

        # csvを元にユーザにロールを追加
        for d in csv_data:
            # データバリデーション
            if len(d) != 2:
                errors.append(f"不正な行：{d}")
                continue

            try:
                user_id: int = int(d[0].strip())
                role_id: int = int(d[1].strip())
            except ValueError:
                errors.append(f"不正な値：{d}")
                continue

            # user_idとrole_idからユーザとロールを取得
            user: discord.Member | None = interaction.guild.get_member(user_id)
            role: discord.Role | None = interaction.guild.get_role(role_id)

            # ユーザが見つからない場合はfetchしてみて、それでも見つからない場合はNone
            if user is None:
                try:
                    user = await interaction.guild.fetch_member(user_id)
                except discord.NotFound:
                    user = None

            # ユーザまたはロールが見つからない場合はエラーとする
            if user is None or role is None:
                errors.append(f"不明：{user_id}, {role_id}")
                continue

            # ユーザにロールを追加
            await user.add_roles(role)

        # エラーがある場合はエラーメッセージを表示
        if len(errors) > 0:
            msg: str = '\n'.join(errors)
            await interaction.response.send_message(f"一部の値でエラーが発生しました。\n```\n{msg}\n```", ephemeral=True)

        # エラーがない場合は成功メッセージを表示
        else:
            await interaction.response.send_message("ロールを追加しました！", ephemeral=True)


class PersonalInfoAcquireView(discord.ui.View):
    """
    参加者情報入力ボタンを表示するView

    スラコマから呼び出される
    """

    def __init__(self):
        # view永続化
        super().__init__(timeout=None)

    @discord.ui.button(label="参加者情報を入力する",
                       style=discord.ButtonStyle.primary, custom_id="personal_info_acquire:start")
    async def acquire_button_callback(self, _: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(PersonalInfoInputModal(title="参加者情報入力"))


class PersonalInfoAcquirer(commands.Cog):
    """
    参加者情報を取得するためのCog

    参加者情報の入力・更新、参加者情報のCSV出力、ユーザにロールを追加する機能を提供
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # view永続化
        self.bot.add_view(PersonalInfoAcquireView())

    @slash_command(name="create_personal_info_button", description="参加者情報入力パネルを生成")
    @commands.has_permissions(administrator=True)
    async def create_personal_info_button(self, ctx: discord.commands.context.ApplicationContext):
        """
        参加者情報入力ボタンを生成する
        """
        await ctx.respond("参加者情報の入力・更新は以下のボタンから行ってください。", view=PersonalInfoAcquireView())

    @slash_command(name="list_participants", description="参加者情報をCSVで出力")
    @commands.has_permissions(administrator=True)
    async def list_participants(self, ctx: discord.commands.context.ApplicationContext):
        """
        参加者情報をCSV形式で出力する
        """
        with get_db() as db:
            participants: list[Participant] = participant_crud.get_all(db)

        csv_data: str = "氏名,所属学校名,DiscordID,discord表示名,discordユーザ名\n"
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
        """
        ユーザにロールを追加する
        """
        await ctx.send_modal(AddRoleModal(title="ロール追加"))

    @slash_command(name="list_unregistered_users", description="未登録ユーザを表示")
    @commands.has_permissions(administrator=True)
    async def list_unregistered_users(self,
                                      ctx: discord.commands.context.ApplicationContext,
                                      mode: discord.Option(str, "モード", choices=["csv", "mentions"], default="csv")
                                      ):
        """
        未登録ユーザを表示する
        """
        with get_db() as db:
            participants: list[Participant] = participant_crud.get_all(db)

        registered_user_ids: list[int] = [p.discord_account_id for p in participants]
        unregistered_users: list[discord.Member] = [user
                                                    for user in ctx.guild.members
                                                    if user.id not in registered_user_ids]

        if mode == "csv":
            # csvで出力
            csv_data: str = "DiscordID,discord表示名,discordユーザ名\n"
            for user in unregistered_users:
                csv_data += f"{user.id},{user.nick},{user.name}\n"

            with tempfile.TemporaryFile("w", encoding="utf-8") as f:
                f.write(csv_data)
                f.seek(0)
                await ctx.respond(file=discord.File(f.name, filename="unregistered_users.csv"))

        elif mode == "mentions":
            # メンションで出力
            msg: str = " ".join([user.mention for user in unregistered_users])
            await ctx.respond(f"```\n{msg}\n```")

        else:
            await ctx.respond("不正なモードです。", ephemeral=True)


def setup(bot):
    return bot.add_cog(PersonalInfoAcquirer(bot))
