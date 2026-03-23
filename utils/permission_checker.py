"""
Verificador de Permissões
"""

from typing import Union, Optional
import discord
from discord import app_commands

from core.config import Config


class PermissionChecker:
    """Verifica permissões de usuários para comandos."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def check_permissions(
        self,
        source: Union[discord.Interaction, discord.Message],
        admin_only: bool = False
    ) -> bool:
        """Verifica se o usuário tem permissão para usar um comando."""
        
        if isinstance(source, discord.Interaction):
            user = source.user
            guild_id = source.guild_id
            channel = source.channel
        else:
            user = source.author
            guild_id = source.guild.id if source.guild else None
            channel = source.channel
        
        user_id = user.id
        
        # Verificar se é dono do bot
        if self._is_bot_owner(user_id):
            return True
        
        # Obter roles do usuário
        user_roles = {r.id for r in getattr(user, "roles", [])}
        
        # Verificar permissões de admin
        admin_users = set(self.config._config_data.get("admin_permissions", {}).get("users", []))
        admin_roles = set(self.config._config_data.get("admin_permissions", {}).get("roles", []))
        
        is_admin = user_id in admin_users or bool(user_roles.intersection(admin_roles))
        
        if admin_only:
            return is_admin
        
        if is_admin:
            return True
        
        # Verificar permissões gerais
        perms = self.config._config_data.get("permissions", {}).copy()
        
        # Aplicar overrides do servidor
        if guild_id:
            guild_overrides = self.config._config_data.get("guild_overrides", {}).get(str(guild_id), {})
            if "permissions" in guild_overrides:
                perms.update(guild_overrides["permissions"])
        
        # Verificar bloqueios
        user_perms = perms.get("users", {})
        if user_id in user_perms.get("blocked_ids", []):
            return False
        
        role_perms = perms.get("roles", {})
        if user_roles.intersection(role_perms.get("blocked_ids", [])):
            return False
        
        chan_perms = perms.get("channels", {})
        if channel and channel.id in chan_perms.get("blocked_ids", []):
            return False
        
        # Verificar allowlists
        allowed_users = user_perms.get("allowed_ids", [])
        allowed_roles = role_perms.get("allowed_ids", [])
        allowed_channels = chan_perms.get("allowed_ids", [])
        
        # Se há allowlist, verificar se usuário está nela
        if allowed_users or allowed_roles:
            if user_id in allowed_users:
                return True
            if user_roles.intersection(allowed_roles):
                return True
            return False
        
        # Se há allowlist de canais, verificar
        if allowed_channels and channel:
            if channel.id not in allowed_channels:
                return False
        
        return True
    
    def _is_bot_owner(self, user_id: int) -> bool:
        """Verifica se o usuário é dono do bot."""
        # Isso será verificado dinamicamente quando o bot estiver pronto
        return False
    
    def is_admin(self, user: discord.User, guild: Optional[discord.Guild] = None) -> bool:
        """Verifica se o usuário é administrador."""
        # Verificar dono do bot
        # Verificar admins configurados
        admin_users = set(self.config._config_data.get("admin_permissions", {}).get("users", []))
        admin_roles = set(self.config._config_data.get("admin_permissions", {}).get("roles", []))
        
        if user.id in admin_users:
            return True
        
        if guild:
            member = guild.get_member(user.id)
            if member:
                user_roles = {r.id for r in member.roles}
                if user_roles.intersection(admin_roles):
                    return True
        
        return False


def permission_denied_message(locale: Optional[str] = None) -> str:
    """Retorna mensagem de permissão negada no idioma apropriado."""
    if locale and "pt" in locale.lower():
        return "❌ Você não tem permissão para usar este comando."
    if locale and "es" in locale.lower():
        return "❌ No tienes permiso para usar este comando."
    return "❌ You do not have permission to use this command."
