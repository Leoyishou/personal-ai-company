#!/bin/bash

# Personal AI Company - Claude Code Configuration Installer
# This script sets up symlinks and configurations for Claude Code

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "================================================"
echo "Personal AI Company - Claude Code Setup"
echo "================================================"
echo ""

# Check if Claude Code is installed
if ! command -v claude &> /dev/null; then
    echo "Warning: Claude Code CLI not found. Please install it first:"
    echo "  https://docs.anthropic.com/en/docs/claude-code"
    echo ""
fi

# Create ~/.claude directory if it doesn't exist
if [ ! -d "$CLAUDE_DIR" ]; then
    echo "Creating ~/.claude directory..."
    mkdir -p "$CLAUDE_DIR"
fi

# Backup existing configurations
backup_if_exists() {
    local target="$1"
    if [ -e "$target" ] && [ ! -L "$target" ]; then
        local backup="${target}.backup.$(date +%Y%m%d_%H%M%S)"
        echo "Backing up existing $target to $backup"
        mv "$target" "$backup"
    elif [ -L "$target" ]; then
        echo "Removing existing symlink: $target"
        rm "$target"
    fi
}

# Create symlinks
echo ""
echo "Setting up symlinks..."

# Skills
backup_if_exists "$CLAUDE_DIR/skills"
ln -sf "$SCRIPT_DIR/.claude/skills" "$CLAUDE_DIR/skills"
echo "  ✓ Skills -> $CLAUDE_DIR/skills"

# Agents
backup_if_exists "$CLAUDE_DIR/agents"
ln -sf "$SCRIPT_DIR/.claude/agents" "$CLAUDE_DIR/agents"
echo "  ✓ Agents -> $CLAUDE_DIR/agents"

# Rules
backup_if_exists "$CLAUDE_DIR/rules"
ln -sf "$SCRIPT_DIR/.claude/rules" "$CLAUDE_DIR/rules"
echo "  ✓ Rules -> $CLAUDE_DIR/rules"

# Create secrets.env if it doesn't exist
if [ ! -f "$CLAUDE_DIR/secrets.env" ]; then
    echo ""
    echo "Creating secrets.env template..."
    cp "$SCRIPT_DIR/.env.example" "$CLAUDE_DIR/secrets.env"
    echo "  ✓ Created $CLAUDE_DIR/secrets.env"
    echo "  ! Please edit this file and add your API keys"
else
    echo ""
    echo "secrets.env already exists, skipping..."
fi

# Copy CLAUDE.md template if not exists
if [ ! -f "$CLAUDE_DIR/CLAUDE.md" ]; then
    echo ""
    echo "Creating CLAUDE.md from template..."
    cp "$SCRIPT_DIR/.claude/CLAUDE.md.template" "$CLAUDE_DIR/CLAUDE.md"
    echo "  ✓ Created $CLAUDE_DIR/CLAUDE.md"
    echo "  ! Please customize this file with your personal settings"
else
    echo ""
    echo "CLAUDE.md already exists, skipping..."
fi

# Setup BU directories
echo ""
echo "Setting up Business Unit directories..."

PAC_DIR="$HOME/usr/pac"
if [ ! -d "$PAC_DIR" ]; then
    mkdir -p "$PAC_DIR"
fi

for bu in product-bu content-bu investment-bu; do
    bu_dir="$PAC_DIR/$bu"
    if [ ! -d "$bu_dir/.claude" ]; then
        mkdir -p "$bu_dir/.claude"
        cp "$SCRIPT_DIR/pac/$bu/.claude/CLAUDE.md" "$bu_dir/.claude/CLAUDE.md"
        echo "  ✓ Created $bu_dir/.claude/CLAUDE.md"
    else
        echo "  - $bu already configured, skipping..."
    fi
done

echo ""
echo "================================================"
echo "Installation complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Edit ~/.claude/secrets.env and add your API keys"
echo "2. Edit ~/.claude/CLAUDE.md to customize your profile"
echo "3. Start Claude Code in a BU directory:"
echo "   cd ~/usr/pac/product-bu && claude"
echo ""
echo "Available BUs:"
echo "  - ~/usr/pac/product-bu   (Code products)"
echo "  - ~/usr/pac/content-bu   (Social media content)"
echo "  - ~/usr/pac/investment-bu (Investment analysis)"
echo ""
