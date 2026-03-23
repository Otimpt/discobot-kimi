"""
Formatador para Discord
Converte e corrige formatação para o Discord
"""

import re
import logging
from typing import Optional, Dict, Any

import discord

logger = logging.getLogger("discord-bot")


class DiscordFormatter:
    """Formata texto para o Discord corretamente."""
    
    # Limites do Discord
    MAX_MESSAGE_LENGTH = 2000
    MAX_EMBED_TITLE = 256
    MAX_EMBED_DESCRIPTION = 4096
    MAX_EMBED_FIELDS = 25
    MAX_EMBED_FIELD_NAME = 256
    MAX_EMBED_FIELD_VALUE = 1024
    MAX_EMBED_FOOTER = 2048
    MAX_EMBED_AUTHOR = 256
    MAX_EMBED_TOTAL = 6000
    
    def __init__(self):
        # Mapeamento de formatações comuns para Discord markdown
        self.format_mappings = {
            # Markdown padrão para Discord
            '**': '**',      # Negrito
            '*': '*',        # Itálico
            '__': '__',      # Sublinhado
            '~~': '~~',      # Tachado
            '`': '`',        # Código inline
            '```': '```',    # Bloco de código
            '> ': '> ',      # Citação
            '# ': '## ',     # Cabeçalho (Discord usa ##)
            '## ': '### ',   # Cabeçalho 2
            '### ': '#### ', # Cabeçalho 3
        }
    
    def format_text(self, text: str) -> str:
        """
        Formata texto para o Discord.
        
        Args:
            text: Texto a ser formatado
            
        Returns:
            Texto formatado
        """
        if not text:
            return ""
        
        # Corrigir formatações problemáticas
        text = self._fix_bold_formatting(text)
        text = self._fix_italic_formatting(text)
        text = self._fix_code_blocks(text)
        text = self._fix_lists(text)
        text = self._fix_links(text)
        text = self._fix_mentions(text)
        
        # Limpar espaços excessivos
        text = self._clean_whitespace(text)
        
        return text
    
    def _fix_bold_formatting(self, text: str) -> str:
        """Corrige formatação em negrito."""
        # Corrigir **** (negrito vazio)
        text = re.sub(r'\*\*\*\*', '', text)
        
        # Corrigir espaços entre asteriscos
        text = re.sub(r'\*\*\s+\*\*', '', text)
        
        # Garantir que ** está balanceado
        bold_count = text.count('**')
        if bold_count % 2 != 0:
            # Adicionar ** no final se necessário
            text = text + '**'
        
        return text
    
    def _fix_italic_formatting(self, text: str) -> str:
        """Corrige formatação em itálico."""
        # Corrigir * * (itálico vazio)
        text = re.sub(r'\*\s+\*', '', text)
        
        # Não interferir com ** (negrito)
        # Apenas corrigir * soltos que não fazem parte de **
        
        return text
    
    def _fix_code_blocks(self, text: str) -> str:
        """Corrige blocos de código."""
        # Corrigir `````` (bloco vazio)
        text = re.sub(r'```\s*```', '', text)
        
        # Garantir que ``` está balanceado
        code_block_count = text.count('```')
        if code_block_count % 2 != 0:
            text = text + '\n```'
        
        # Corrigir linguagem especificada incorretamente
        text = re.sub(r'```(\w+)\n?', r'```\1\n', text)
        
        return text
    
    def _fix_lists(self, text: str) -> str:
        """Corrige listas."""
        # Converter - para • se necessário (Discord aceita ambos)
        # Mas manter consistência
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Detectar itens de lista
            if re.match(r'^\s*[-•]\s', line):
                # Padronizar para -
                line = re.sub(r'^\s*[-•]\s', '- ', line)
            
            # Detectar listas numeradas
            if re.match(r'^\s*\d+[.\)]\s', line):
                # Padronizar para 1. formato
                line = re.sub(r'^(\s*)\d+[.\)]\s', r'\g<1>1. ', line)
            
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _fix_links(self, text: str) -> str:
        """Corrige links."""
        # Converter [texto](url) malformado
        text = re.sub(r'\[([^\]]+)\]\s*\(([^)]+)\)', r'[\1](\2)', text)
        
        # Remover links quebrados
        text = re.sub(r'\[([^\]]*)\]\(\s*\)', r'\1', text)
        
        return text
    
    def _fix_mentions(self, text: str) -> str:
        """Corrige menções."""
        # Não permitir menções @everyone/@here maliciosas
        # (o Discord já tem proteção, mas por segurança)
        
        # Corrigir menções de usuário malformadas
        text = re.sub(r'<@\s*(\d+)>', r'<@\1>', text)
        text = re.sub(r'<@!\s*(\d+)>', r'<@!\1>', text)
        
        # Corrigir menções de canal
        text = re.sub(r'<#\s*(\d+)>', r'<#\1>', text)
        
        # Corrigir menções de cargo
        text = re.sub(r'<@&\s*(\d+)>', r'<@&\1>', text)
        
        return text
    
    def _clean_whitespace(self, text: str) -> str:
        """Limpa espaços em branco excessivos."""
        # Remover espaços no início/fim de linhas
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]
        
        # Remover linhas vazias excessivas
        cleaned_lines = []
        empty_count = 0
        
        for line in lines:
            if not line.strip():
                empty_count += 1
                if empty_count <= 2:  # Máximo 2 linhas vazias seguidas
                    cleaned_lines.append(line)
            else:
                empty_count = 0
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Remover espaços no início/fim
        text = text.strip()
        
        return text
    
    def truncate_text(self, text: str, max_length: int = MAX_MESSAGE_LENGTH) -> str:
        """Trunca texto para caber no limite."""
        if len(text) <= max_length:
            return text
        
        # Tentar truncar em uma quebra de linha
        truncated = text[:max_length - 3]
        last_newline = truncated.rfind('\n')
        
        if last_newline > max_length * 0.7:  # Se tiver newline nos últimos 30%
            truncated = truncated[:last_newline]
        
        return truncated + "..."
    
    def create_embed(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: discord.Color = discord.Color.blue(),
        fields: Optional[list] = None,
        footer: Optional[str] = None,
        image_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        author_name: Optional[str] = None,
        author_icon: Optional[str] = None
    ) -> discord.Embed:
        """
        Cria um embed formatado corretamente.
        
        Args:
            title: Título do embed
            description: Descrição
            color: Cor do embed
            fields: Lista de campos (dict com name, value, inline)
            footer: Texto do rodapé
            image_url: URL da imagem
            thumbnail_url: URL do thumbnail
            author_name: Nome do autor
            author_icon: Ícone do autor
            
        Returns:
            discord.Embed formatado
        """
        embed = discord.Embed(color=color)
        
        # Título
        if title:
            title = self.format_text(title)
            embed.title = self.truncate_text(title, self.MAX_EMBED_TITLE)
        
        # Descrição
        if description:
            description = self.format_text(description)
            embed.description = self.truncate_text(description, self.MAX_EMBED_DESCRIPTION)
        
        # Campos
        if fields:
            for field in fields[:self.MAX_EMBED_FIELDS]:
                name = self.format_text(field.get('name', ''))
                value = self.format_text(field.get('value', ''))
                inline = field.get('inline', False)
                
                embed.add_field(
                    name=self.truncate_text(name, self.MAX_EMBED_FIELD_NAME),
                    value=self.truncate_text(value, self.MAX_EMBED_FIELD_VALUE),
                    inline=inline
                )
        
        # Footer
        if footer:
            footer = self.format_text(footer)
            embed.set_footer(text=self.truncate_text(footer, self.MAX_EMBED_FOOTER))
        
        # Imagem
        if image_url:
            embed.set_image(url=image_url)
        
        # Thumbnail
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
        
        # Autor
        if author_name:
            author_name = self.format_text(author_name)
            embed.set_author(
                name=self.truncate_text(author_name, self.MAX_EMBED_AUTHOR),
                icon_url=author_icon
            )
        
        return embed
    
    def split_long_message(self, text: str, max_length: int = MAX_MESSAGE_LENGTH) -> list:
        """
        Divide uma mensagem longa em partes.
        
        Args:
            text: Texto longo
            max_length: Tamanho máximo de cada parte
            
        Returns:
            Lista de partes
        """
        if len(text) <= max_length:
            return [text]
        
        parts = []
        current_part = ""
        
        # Tentar dividir por parágrafos
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            if len(current_part) + len(paragraph) + 2 <= max_length:
                current_part += paragraph + '\n\n'
            else:
                if current_part:
                    parts.append(current_part.strip())
                
                # Se o parágrafo for maior que o limite, dividir por frases
                if len(paragraph) > max_length:
                    sentences = paragraph.split('. ')
                    current_part = ""
                    
                    for sentence in sentences:
                        if len(current_part) + len(sentence) + 2 <= max_length:
                            current_part += sentence + '. '
                        else:
                            if current_part:
                                parts.append(current_part.strip())
                            current_part = sentence + '. '
                else:
                    current_part = paragraph + '\n\n'
        
        if current_part:
            parts.append(current_part.strip())
        
        return parts
    
    def escape_markdown(self, text: str) -> str:
        """Escapa caracteres markdown."""
        escape_chars = ['*', '_', '~', '`', '>', '|', '\\']
        
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    def unescape_markdown(self, text: str) -> str:
        """Remove escape de caracteres markdown."""
        escape_chars = ['*', '_', '~', '`', '>', '|', '\\']
        
        for char in escape_chars:
            text = text.replace(f'\\{char}', char)
        
        return text
    
    def format_code(self, code: str, language: str = "") -> str:
        """Formata código para Discord."""
        # Escapar backticks dentro do código
        code = code.replace('```', '`\u200b``')
        
        # Criar bloco de código
        return f"```{language}\n{code}\n```"
    
    def format_quote(self, text: str, author: Optional[str] = None) -> str:
        """Formata uma citação."""
        lines = text.split('\n')
        quoted_lines = [f"> {line}" for line in lines]
        
        if author:
            quoted_lines.append(f"> \n> — *{author}*")
        
        return '\n'.join(quoted_lines)
    
    def format_spoiler(self, text: str) -> str:
        """Formata texto como spoiler."""
        return f"||{text}||"
    
    def format_timestamp(self, timestamp: int, style: str = 'f') -> str:
        """
        Formata um timestamp para Discord.
        
        Styles:
            t: Short Time (16:20)
            T: Long Time (16:20:30)
            d: Short Date (20/04/2024)
            D: Long Date (20 de abril de 2024)
            f: Short Date/Time (20 de abril de 2024 16:20)
            F: Long Date/Time (sábado, 20 de abril de 2024 16:20)
            R: Relative Time (há 2 horas)
        """
        return f"<t:{timestamp}:{style}>"


# Instância global
formatter = DiscordFormatter()
