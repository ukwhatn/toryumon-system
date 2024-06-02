import logging
import re

import discord
from discord.commands import slash_command
from discord.ext import commands

from db.package.crud import progress_ask as progress_ask_crud
from db.package.session import get_db

INDEXED_REACTIONS = [
    "0️⃣",
    "1️⃣",
    "2️⃣",
    "3️⃣",
    "4️⃣",
    "5️⃣",
    "6️⃣",
    "7️⃣",
    "8️⃣",
    "9️⃣",
    "🔟"
]


class ProgressAskUtil:
    @staticmethod
    async def get_or_fetch_guild(bot: discord.Client, guild_id: int) -> discord.Guild | None:
        guild = bot.get_guild(guild_id)
        if guild is None:
            try:
                guild = await bot.fetch_guild(guild_id)
            except discord.NotFound:
                return None
        return guild

    @staticmethod
    async def get_or_fetch_channel(guild: discord.Guild, channel_id: int) -> discord.TextChannel | None:
        channel = guild.get_channel(channel_id)
        if channel is None:
            try:
                channel = await guild.fetch_channel(channel_id)
            except discord.NotFound:
                return None
        return channel

    @staticmethod
    async def get_or_fetch_message(channel: discord.TextChannel, message_id: int) -> discord.Message | None:
        try:
            return await channel.fetch_message(message_id)
        except discord.NotFound:
            return None

    @staticmethod
    async def create_progress_summary_embed(
            guild: discord.Guild,
            role_ids: list[int],
            reactions: list[discord.Reaction],
            progress_cnt: int
    ) -> discord.Embed:
        roles: list[discord.Role] = [guild.get_role(role_id) for role_id in role_ids]

        progress_data: dict[str, dict[str, list[int]]] = {
            role.name: {
                member.nick if member.nick is not None else member.name: []
                for member in role.members
            } for role in roles
        }

        # リアクション種別ごとにfor文を回す
        for reaction in reactions:
            # リアクションが進捗確認のものでない場合はスキップ
            if not ProgressAskUtil.is_indexed_reaction(reaction.emoji):
                continue

            # リアクションのindexを取得
            index = ProgressAskUtil.get_index(reaction.emoji)
            # リアクションを付けたユーザを取得してflatten
            users = await reaction.users().flatten()
            members = [await guild.fetch_member(user.id) for user in users if not user.bot]

            # ユーザごとにfor文を回す
            for member in members:
                # 対象ロールごとに回す
                for role in roles:
                    # ユーザが対象ロールに所属している場合
                    if role in member.roles:
                        name = member.nick if member.nick is not None else member.name
                        if name not in progress_data[role.name]:
                            progress_data[role.name][name] = []
                        progress_data[role.name][name].append(index)

        # indexを昇順にソート
        for role in progress_data:
            for member in progress_data[role]:
                progress_data[role][member].sort()

        # 進捗確認のEmbedを作成
        embed = discord.Embed(
            title="進捗確認"
        )

        # ロールごとに進捗確認を追加
        for role_name, user_data in progress_data.items():
            embed.add_field(
                name=f"**【{role_name}】**",
                value="\n".join([
                    f"**{user}**\n{' '.join([ProgressAskUtil.get_reaction(i) if i in indexes else '❌' for i in range(progress_cnt)])}\n"
                    for user, indexes in user_data.items()
                ]),
                inline=True
            )

        return embed

    @staticmethod
    def get_reaction(index: int):
        return INDEXED_REACTIONS[index]

    @staticmethod
    def get_index(reaction: str):
        return INDEXED_REACTIONS.index(reaction)

    @staticmethod
    def is_indexed_reaction(reaction: str):
        return reaction in INDEXED_REACTIONS


class ProgressAskCreateModal(discord.ui.Modal):
    def __init__(self) -> None:
        super().__init__(title="進捗確認の作成")
        self.add_item(discord.ui.InputText(
            style=discord.InputTextStyle.short,
            label="タイトル",
            placeholder="〇〇をやろう！"
        ))
        self.add_item(discord.ui.InputText(
            style=discord.InputTextStyle.long,
            label="手順",
            placeholder="１行に１つずつ手順を記入してください。"
        ))

    async def callback(self, interaction: discord.Interaction):
        # ベースメッセージを取得
        base_message = interaction.message

        # 情報取得
        ask_channel_id = int(re.search(r"<#(\d+)>", base_message.embeds[0].fields[0].value).group(1))
        role_ids = [int(role_id) for role_id in re.findall(r"\d+", base_message.embeds[0].fields[1].value)]
        title = self.children[0].value
        contents = self.children[1].value.split("\n")

        if len(contents) > 10:
            await interaction.response.send_message("進捗確認の手順は10個までしか登録できません。", ephemeral=True)
            return

        ask_channel = interaction.guild.get_channel(ask_channel_id)

        # 進捗確認を作成
        ask_contents = [
            f"{ProgressAskUtil.get_reaction(index)} {content}"
            for index, content in enumerate(contents)
        ]
        ask_message = await ask_channel.send(
            content="進捗確認を作成中......",
        )
        summary_message = await interaction.channel.send(
            content="進捗確認を作成中......",
        )
        await interaction.response.send_message("進捗確認を作成します", ephemeral=True)

        # 進捗確認を作成
        with get_db() as db:
            progress_ask_crud.create(
                db,
                guild_id=interaction.guild.id,
                ask_channel_id=ask_message.channel.id,
                ask_message_id=ask_message.id,
                summary_channel_id=summary_message.channel.id,
                summary_message_id=summary_message.id,
                role_ids=role_ids,
                contents=contents
            )

        await ask_message.edit(
            content="## 【進捗確認】",
            embed=discord.Embed(
                title=title,
            ).add_field(
                name="手順",
                value="\n".join(ask_contents),
                inline=False
            )
        )

        await summary_message.edit(
            content="## 【進捗チェック】",
            embeds=[
                discord.Embed(
                    title=title,
                ).add_field(
                    name="手順",
                    value="\n".join(ask_contents),
                    inline=False
                ),
                await ProgressAskUtil.create_progress_summary_embed(
                    interaction.guild,
                    role_ids,
                    [],
                    len(contents)
                )
            ]
        )

        for index in range(len(contents)):
            await ask_message.add_reaction(ProgressAskUtil.get_reaction(index))


class ProgressAskBaseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="進捗確認を作成する", style=discord.ButtonStyle.primary, custom_id="progress_ask:create")
    async def create_progress_ask(self, _: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(modal=ProgressAskCreateModal())


class ProgressAsk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(type(self).__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(ProgressAskBaseView())

    @slash_command(name="create_progress_ask_base", description="進捗確認のベースを作成")
    @commands.has_permissions(administrator=True)
    async def create_progress_ask_base(
            self,
            ctx: discord.commands.context.ApplicationContext,
            ask_channel: discord.Option(discord.TextChannel, "進捗確認を行うチャンネル"),
            roles: discord.Option(str, "まとめるロールを全てメンション", required=True),
    ):
        await ctx.respond(
            content="## 【システム】",
            embed=discord.Embed(
                title="進捗確認",
                description="進捗確認を行います。"
            ).add_field(
                name="進捗確認を行うチャンネル",
                value=ask_channel.mention,
                inline=False
            ).add_field(
                name="対象者のロール",
                value=roles,
                inline=False
            ),
            view=ProgressAskBaseView()
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.reaction_handler(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.reaction_handler(payload)

    async def reaction_handler(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        if not ProgressAskUtil.is_indexed_reaction(payload.emoji.name):
            return

        with get_db() as db:
            progress_ask = progress_ask_crud.get(db, payload.guild_id, payload.message_id)
            if progress_ask is None:
                return

            ask_contents_len = len(progress_ask.contents)

            # 対象ギルド取得
            guild = await ProgressAskUtil.get_or_fetch_guild(self.bot, payload.guild_id)

            # 進捗確認のメッセージ取得
            ask_channel = await ProgressAskUtil.get_or_fetch_channel(guild, progress_ask.ask_channel_id)
            ask_message = await ProgressAskUtil.get_or_fetch_message(ask_channel, progress_ask.ask_message_id)

            # 進捗確認のサマリー取得
            summary_channel = await ProgressAskUtil.get_or_fetch_channel(guild, progress_ask.summary_channel_id)
            summary_message = await ProgressAskUtil.get_or_fetch_message(summary_channel,
                                                                         progress_ask.summary_message_id)

            summary_embeds = summary_message.embeds
            summary_embeds[1] = await ProgressAskUtil.create_progress_summary_embed(
                guild,
                [role.role_id for role in progress_ask.roles],
                ask_message.reactions,
                ask_contents_len
            )

        await summary_message.edit(
            content="## 【進捗チェック】",
            embeds=summary_embeds
        )


def setup(bot):
    return bot.add_cog(ProgressAsk(bot))
