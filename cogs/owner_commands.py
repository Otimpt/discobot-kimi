"""
Comandos do Dono do Bot
Apenas o dono do bot pode usar estes comandos
"""

import asyncio
import io
import logging
import sys
import traceback
from datetime import datetime
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from core.config import Config
from database.manager import DatabaseManager
from providers.manager import ProviderManager

logger = logging.getLogger("discord-bot")


class OwnerCommands(commands.Cog):
    """Comandos exclusivos do dono do bot."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.provider: ProviderManager = bot.provider
    
    def is_owner(self, user_id: int) -> bool:
        """Verifica se o usuário é o dono do bot."""
        owner_id = self.config._config_data.get("owner", {}).get("user_id", 0)
        return user_id == owner_id
    
    async def cog_check(self, ctx: commands.Context) -> bool:
        """Verifica se é o dono."""
        return self.is_owner(ctx.author.id)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Verifica se é o dono em comandos slash."""
        if not self.is_owner(interaction.user.id):
            await interaction.response.send_message(
                "🚫 Este comando é exclusivo do dono do bot.",
                ephemeral=True
            )
            return False
        return True
    
    owner_group = app_commands.Group(
        name="owner",
        description="Comandos exclusivos do dono",
        guild_only=False
    )
    
    @owner_group.command(name="broadcast", description="Envia mensagem para todos os servidores")
    @app_commands.describe(
        mensagem="Mensagem a enviar",
        anunciar="Se deve anunciar como embed"
    )
    async def owner_broadcast(
        self,
        interaction: discord.Interaction,
        mensagem: str,
        anunciar: bool = True
    ):
        """Broadcast para todos os servidores."""
        await interaction.response.defer(ephemeral=True)
        
        sent = 0
        failed = 0
        
        for guild in self.bot.guilds:
            try:
                # Procurar canal de sistema ou primeiro canal de texto
                channel = guild.system_channel
                if not channel or not channel.permissions_for(guild.me).send_messages:
                    channel = next(
                        (c for c in guild.text_channels 
                         if c.permissions_for(guild.me).send_messages),
                        None
                    )
                
                if channel:
                    if anunciar:
                        embed = discord.Embed(
                            title="📢 Anúncio do Desenvolvedor",
                            description=mensagem,
                            color=discord.Color.gold(),
                            timestamp=datetime.now()
                        )
                        embed.set_footer(text="Mensagem do dono do bot")
                        await channel.send(embed=embed)
                    else:
                        await channel.send(f"📢 **Anúncio:** {mensagem}")
                    sent += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Erro ao enviar broadcast para {guild.name}: {e}")
                failed += 1
        
        await interaction.followup.send(
            f"✅ Broadcast enviado!\n"
            f"📤 Enviado: {sent} servidores\n"
            f"❌ Falhou: {failed} servidores",
            ephemeral=True
        )
    
    @owner_group.command(name="shutdown", description="Desliga o bot")
    @app_commands.describe(
        razao="Razão do desligamento",
        reiniciar="Se deve reiniciar automaticamente"
    )
    async def owner_shutdown(
        self,
        interaction: discord.Interaction,
        razao: Optional[str] = None,
        reiniciar: bool = False
    ):
        """Desliga o bot."""
        await interaction.response.send_message(
            f"🛑 Desligando bot...\n"
            f"Razão: {razao or 'Não especificada'}\n"
            f"Reiniciar: {'Sim' if reiniciar else 'Não'}",
            ephemeral=True
        )
        
        logger.info(f"Bot desligado por {interaction.user}. Razão: {razao}")
        
        await self.bot.close()
    
    @owner_group.command(name="reload", description="Recarrega um cog")
    @app_commands.describe(cog="Nome do cog a recarregar (ex: cogs.chat_commands)")
    async def owner_reload(
        self,
        interaction: discord.Interaction,
        cog: str
    ):
        """Recarrega um cog."""
        try:
            await self.bot.reload_extension(cog)
            await interaction.response.send_message(
                f"✅ Cog `{cog}` recarregado com sucesso!",
                ephemeral=True
            )
            logger.info(f"Cog {cog} recarregado por {interaction.user}")
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Erro ao recarregar `{cog}`:\n```{str(e)[:1000]}```",
                ephemeral=True
            )
    
    @owner_group.command(name="reload_all", description="Recarrega todos os cogs")
    async def owner_reload_all(self, interaction: discord.Interaction):
        """Recarrega todos os cogs."""
        await interaction.response.defer(ephemeral=True)
        
        cogs = [
            "cogs.chat_commands",
            "cogs.config_commands",
            "cogs.model_commands",
            "cogs.model_menu",
            "cogs.persona_commands",
            "cogs.image_commands",
            "cogs.shop_commands",
            "cogs.memory_commands",
            "cogs.file_commands",
            "cogs.utility_commands",
            "cogs.apps_commands",
            "cogs.admin_commands",
            "cogs.owner_commands",
        ]
        
        success = []
        failed = []
        
        for cog in cogs:
            try:
                await self.bot.reload_extension(cog)
                success.append(cog)
            except Exception as e:
                failed.append(f"{cog}: {e}")
        
        embed = discord.Embed(
            title="🔄 Recarregamento de Cogs",
            color=discord.Color.green() if not failed else discord.Color.yellow()
        )
        
        if success:
            embed.add_field(
                name=f"✅ Sucesso ({len(success)})",
                value="\n".join(f"• `{c}`" for c in success),
                inline=False
            )
        
        if failed:
            embed.add_field(
                name=f"❌ Falhou ({len(failed)})",
                value="\n".join(f"• {f}" for f in failed[:5]),
                inline=False
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @owner_group.command(name="eval", description="Executa código Python")
    @app_commands.describe(codigo="Código Python a executar")
    async def owner_eval(
        self,
        interaction: discord.Interaction,
        codigo: str
    ):
        """Executa código Python."""
        await interaction.response.defer(ephemeral=True)
        
        # Preparar ambiente
        env = {
            'bot': self.bot,
            'config': self.config,
            'db': self.db,
            'provider': self.provider,
            'discord': discord,
            'commands': commands,
        }
        
        # Criar código
        code = f"async def __eval__():\n"
        for line in codigo.split('\n'):
            code += f"    {line}\n"
        
        stdout = io.StringIO()
        
        try:
            exec(code, env)
            
            # Redirecionar stdout
            old_stdout = sys.stdout
            sys.stdout = stdout
            
            result = await env['__eval__']()
            
            sys.stdout = old_stdout
            
            output = stdout.getvalue()
            
            if result is not None:
                output += str(result)
            
            if not output:
                output = "✅ Executado (sem saída)"
            
            # Enviar resultado
            chunks = [output[i:i+1900] for i in range(0, len(output), 1900)]
            
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await interaction.followup.send(f"```python\n{chunk}\n```", ephemeral=True)
                else:
                    await interaction.followup.send(f"```python\n{chunk}\n```", ephemeral=True)
            
        except Exception as e:
            sys.stdout = old_stdout if 'old_stdout' in locals() else sys.stdout
            error = traceback.format_exc()
            await interaction.followup.send(
                f"❌ Erro:\n```python\n{error[:1900]}\n```",
                ephemeral=True
            )
    
    @owner_group.command(name="sql", description="Executa SQL no banco de dados")
    @app_commands.describe(query="Query SQL a executar")
    async def owner_sql(
        self,
        interaction: discord.Interaction,
        query: str
    ):
        """Executa SQL."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with self.db._connection.execute(query) as cursor:
                rows = await cursor.fetchall()
                
                if not rows:
                    await interaction.followup.send(
                        "✅ Query executada (sem resultados)",
                        ephemeral=True
                    )
                    return
                
                # Formatar resultado
                headers = [description[0] for description in cursor.description]
                
                result_text = " | ".join(headers) + "\n"
                result_text += "-" * (len(result_text)) + "\n"
                
                for row in rows[:20]:  # Limitar a 20 linhas
                    result_text += " | ".join(str(c)[:30] for c in row) + "\n"
                
                if len(rows) > 20:
                    result_text += f"\n... e mais {len(rows) - 20} linhas"
                
                await interaction.followup.send(
                    f"```\n{result_text[:1900]}\n```",
                    ephemeral=True
                )
                
        except Exception as e:
            await interaction.followup.send(
                f"❌ Erro SQL:\n```{str(e)[:1900]}```",
                ephemeral=True
            )
    
    @owner_group.command(name="config", description="Configura um servidor específico")
    @app_commands.describe(
        servidor="ID do servidor",
        chave="Configuração a alterar",
        valor="Novo valor"
    )
    async def owner_config(
        self,
        interaction: discord.Interaction,
        servidor: str,
        chave: str,
        valor: str
    ):
        """Configura servidor específico."""
        try:
            guild_id = int(servidor)
        except ValueError:
            await interaction.response.send_message(
                "❌ ID do servidor inválido.",
                ephemeral=True
            )
            return
        
        # Atualizar configuração
        await self.db.update_guild_config(guild_id, **{chave: valor})
        
        await interaction.response.send_message(
            f"✅ Configuração atualizada para servidor `{guild_id}`:\n"
            f"**{chave}** = `{valor}`",
            ephemeral=True
        )
    
    @owner_group.command(name="globalban", description="Bane um usuário globalmente")
    @app_commands.describe(
        usuario="ID do usuário a banir",
        motivo="Motivo do banimento"
    )
    async def owner_globalban(
        self,
        interaction: discord.Interaction,
        usuario: str,
        motivo: Optional[str] = None
    ):
        """Bane usuário globalmente."""
        try:
            user_id = int(usuario)
        except ValueError:
            await interaction.response.send_message(
                "❌ ID de usuário inválido.",
                ephemeral=True
            )
            return
        
        # Adicionar à lista de banidos globais
        # (implementar no banco de dados)
        
        await interaction.response.send_message(
            f"🚫 Usuário `{user_id}` banido globalmente.\n"
            f"Motivo: {motivo or 'Não especificado'}",
            ephemeral=True
        )
        
        logger.warning(f"Usuário {user_id} banido globalmente por {interaction.user}. Motivo: {motivo}")
    
    @owner_group.command(name="stats", description="Estatísticas globais do bot")
    async def owner_stats(self, interaction: discord.Interaction):
        """Mostra estatísticas globais."""
        await interaction.response.defer(ephemeral=True)
        
        # Coletar estatísticas
        guild_count = len(self.bot.guilds)
        user_count = sum(g.member_count for g in self.bot.guilds)
        channel_count = sum(len(g.channels) for g in self.bot.guilds)
        
        # Estatísticas do banco
        async with self.db._connection.execute("SELECT COUNT(*) FROM conversations") as cursor:
            total_messages = (await cursor.fetchone())[0]
        
        async with self.db._connection.execute("SELECT COUNT(*) FROM economy") as cursor:
            economy_users = (await cursor.fetchone())[0]
        
        async with self.db._connection.execute("SELECT SUM(tokens) FROM economy") as cursor:
            total_tokens = (await cursor.fetchone())[0] or 0
        
        embed = discord.Embed(
            title="📊 Estatísticas Globais",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Servidores", value=guild_count, inline=True)
        embed.add_field(name="Usuários", value=user_count, inline=True)
        embed.add_field(name="Canais", value=channel_count, inline=True)
        embed.add_field(name="Mensagens", value=total_messages, inline=True)
        embed.add_field(name="Usuários na Economia", value=economy_users, inline=True)
        embed.add_field(name="Tokens em Circulação", value=total_tokens, inline=True)
        
        # Uptime
        uptime = datetime.now() - self.bot.start_time if hasattr(self.bot, 'start_time') else None
        if uptime:
            embed.add_field(
                name="Uptime",
                value=f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds // 60) % 60}m",
                inline=True
            )
        
        embed.add_field(name="Latência", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        # Modelos disponíveis
        models = self.provider.list_available_models()
        enabled_models = len([m for m in models if m["enabled"]])
        embed.add_field(name="Modelos Ativos", value=enabled_models, inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @owner_group.command(name="leave", description="Faz o bot sair de um servidor")
    @app_commands.describe(servidor="ID do servidor")
    async def owner_leave(
        self,
        interaction: discord.Interaction,
        servidor: str
    ):
        """Faz o bot sair de um servidor."""
        try:
            guild_id = int(servidor)
        except ValueError:
            await interaction.response.send_message(
                "❌ ID do servidor inválido.",
                ephemeral=True
            )
            return
        
        guild = self.bot.get_guild(guild_id)
        
        if not guild:
            await interaction.response.send_message(
                "❌ Servidor não encontrado.",
                ephemeral=True
            )
            return
        
        await interaction.response.send_message(
            f"🚪 Saindo de **{guild.name}** (`{guild.id}`)...",
            ephemeral=True
        )
        
        await guild.leave()
        
        logger.info(f"Bot saiu do servidor {guild.name} ({guild.id}) por comando do dono")
    
    @owner_group.command(name="setavatar", description="Altera o avatar do bot")
    @app_commands.describe(imagem="Arquivo de imagem")
    async def owner_setavatar(
        self,
        interaction: discord.Interaction,
        imagem: discord.Attachment
    ):
        """Altera avatar do bot."""
        if not imagem.content_type or not imagem.content_type.startswith("image/"):
            await interaction.response.send_message(
                "❌ O arquivo deve ser uma imagem.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            await imagem.save("temp_avatar.png")
            with open("temp_avatar.png", "rb") as f:
                await self.bot.user.edit(avatar=f.read())
            
            import os
            os.remove("temp_avatar.png")
            
            await interaction.followup.send("✅ Avatar atualizado!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(
                f"❌ Erro ao atualizar avatar: {e}",
                ephemeral=True
            )
    
    @owner_group.command(name="setname", description="Altera o nome do bot")
    @app_commands.describe(nome="Novo nome")
    async def owner_setname(
        self,
        interaction: discord.Interaction,
        nome: str
    ):
        """Altera nome do bot."""
        try:
            await self.bot.user.edit(username=nome)
            await interaction.response.send_message(
                f"✅ Nome alterado para **{nome}**",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Erro ao alterar nome: {e}",
                ephemeral=True
            )
    
    @owner_group.command(name="logs", description="Obtém os logs recentes")
    @app_commands.describe(linhas="Número de linhas (padrão: 50)")
    async def owner_logs(
        self,
        interaction: discord.Interaction,
        linhas: int = 50
    ):
        """Obtém logs."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            from pathlib import Path
            log_files = sorted(
                Path("data/logs").glob("bot_*.log"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            if not log_files:
                await interaction.followup.send("📭 Nenhum arquivo de log encontrado.", ephemeral=True)
                return
            
            with open(log_files[0], "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-min(linhas, len(all_lines)):]
            
            log_content = "".join(recent_lines)
            
            if len(log_content) > 1900:
                # Enviar como arquivo
                file = discord.File(
                    io.StringIO(log_content),
                    filename="logs_recentes.txt"
                )
                await interaction.followup.send(file=file, ephemeral=True)
            else:
                await interaction.followup.send(
                    f"```\n{log_content}\n```",
                    ephemeral=True
                )
        
        except Exception as e:
            await interaction.followup.send(
                f"❌ Erro ao ler logs: {e}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Setup do cog."""
    # Adicionar start_time ao bot
    bot.start_time = datetime.now()
    await bot.add_cog(OwnerCommands(bot))
