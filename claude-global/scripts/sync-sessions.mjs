#!/usr/bin/env node

/**
 * Claude Code Session Sync Script
 *
 * Scans all Claude Code session JSONL files and syncs them to Supabase.
 * Filters out noise (progress, file-history-snapshot, turn_duration, etc.)
 * Preserves: user text, tool_use, tool_result, thinking, assistant text.
 *
 * Usage: node sync-sessions.mjs [--full] [--dry-run]
 *   --full: Re-sync all sessions (ignore existing)
 *   --dry-run: Parse and show stats without uploading
 */

import { readFileSync, readdirSync, existsSync, statSync } from 'fs';
import { join, resolve } from 'path';
import { homedir } from 'os';

const SUPABASE_URL = 'https://ebgmmkaxuhawfrwryzia.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImViZ21ta2F4dWhhd2Zyd3J5emlhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg1NjYxNjAsImV4cCI6MjA4NDE0MjE2MH0.TZJAZBJLWL0rkhn3vfAkxPhkpnfXKpaGhZruvysugho';
const CLAUDE_DIR = join(homedir(), '.claude', 'projects');

const args = process.argv.slice(2);
const FULL_SYNC = args.includes('--full');
const DRY_RUN = args.includes('--dry-run');

// --- Supabase helpers ---

async function supabaseQuery(table, method, body, query = '', prefer = '') {
  const url = `${SUPABASE_URL}/rest/v1/${table}${query}`;
  const defaultPrefer = method === 'POST' ? 'return=minimal' : 'return=minimal';
  const headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': `Bearer ${SUPABASE_KEY}`,
    'Content-Type': 'application/json',
    'Prefer': prefer || defaultPrefer,
  };

  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(url, opts);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Supabase ${method} ${table}: ${res.status} ${text}`);
  }
  if (method === 'GET') return res.json();
  return null;
}

async function getExistingSessions() {
  const url = `${SUPABASE_URL}/rest/v1/agent_sessions?select=session_id,message_count`;
  const res = await fetch(url, {
    headers: {
      'apikey': SUPABASE_KEY,
      'Authorization': `Bearer ${SUPABASE_KEY}`,
    },
  });
  if (!res.ok) throw new Error(`Failed to fetch existing sessions: ${res.status}`);
  const data = await res.json();
  return new Map(data.map(s => [s.session_id, s.message_count]));
}

// --- JSONL parsing ---

function parseSessionFile(filePath) {
  const content = readFileSync(filePath, 'utf-8');
  const lines = content.trim().split('\n');
  const messages = [];
  let sessionMeta = {};

  for (const line of lines) {
    if (!line.trim()) continue;
    try {
      const obj = JSON.parse(line);
      messages.push(obj);

      // Extract session-level meta from first message
      if (!sessionMeta.session_id && obj.sessionId) {
        sessionMeta = {
          session_id: obj.sessionId,
          project_path: obj.cwd || null,
          git_branch: obj.gitBranch || null,
          version: obj.version || null,
        };
      }
    } catch (e) {
      // Skip malformed lines
    }
  }

  return { messages, sessionMeta };
}

function isNoise(msg) {
  const type = msg.type;

  // Skip progress messages
  if (type === 'progress') return true;

  // Skip file-history-snapshot
  if (type === 'file-history-snapshot') return true;

  // Skip system messages that are noise
  if (type === 'system') {
    const subtype = msg.subtype;
    if (subtype === 'turn_duration') return true;
    if (subtype === 'local_command') return true;
  }

  return false;
}

function extractMessage(msg, seq) {
  const type = msg.type; // user / assistant / system
  const message = msg.message || {};
  const role = message.role || type;
  const model = message.model || null;
  const content = message.content || msg.content || null;
  const timestamp = msg.timestamp || null;

  // Extract tool names from content
  const toolsUsed = [];
  if (Array.isArray(content)) {
    for (const block of content) {
      if (block && block.type === 'tool_use' && block.name) {
        toolsUsed.push(block.name);
      }
    }
  }

  // Clean content: remove system-reminder noise from user text blocks
  let cleanContent = content;
  if (Array.isArray(content)) {
    cleanContent = content.map(block => {
      if (block && block.type === 'text' && typeof block.text === 'string') {
        // Remove <system-reminder>...</system-reminder> blocks
        const cleaned = block.text.replace(/<system-reminder>[\s\S]*?<\/system-reminder>\s*/g, '').trim();
        if (!cleaned) return null; // Empty after cleaning
        return { ...block, text: cleaned };
      }
      return block;
    }).filter(Boolean);
  } else if (typeof content === 'string') {
    cleanContent = content.replace(/<system-reminder>[\s\S]*?<\/system-reminder>\s*/g, '').trim() || null;
  }

  return {
    seq,
    type,
    role,
    model,
    content: cleanContent,
    tools_used: toolsUsed.length > 0 ? toolsUsed : null,
    timestamp: timestamp ? new Date(timestamp).toISOString() : null,
  };
}

function processSession(filePath, indexEntry) {
  const { messages, sessionMeta } = parseSessionFile(filePath);

  // Filter noise and extract meaningful messages
  const filtered = [];
  let seq = 0;
  let firstPrompt = null;
  let model = null;
  let startedAt = null;
  let endedAt = null;

  for (const msg of messages) {
    if (isNoise(msg)) continue;

    const extracted = extractMessage(msg, seq);

    // Skip if content is empty/null after cleaning
    if (!extracted.content || (Array.isArray(extracted.content) && extracted.content.length === 0)) {
      continue;
    }

    // Track metadata
    if (!startedAt && extracted.timestamp) startedAt = extracted.timestamp;
    if (extracted.timestamp) endedAt = extracted.timestamp;
    if (!model && extracted.model) model = extracted.model;

    // First user text as first_prompt
    if (!firstPrompt && extracted.type === 'user') {
      if (typeof extracted.content === 'string') {
        firstPrompt = extracted.content.slice(0, 500);
      } else if (Array.isArray(extracted.content)) {
        const textBlock = extracted.content.find(b => b && b.type === 'text');
        if (textBlock) firstPrompt = textBlock.text.slice(0, 500);
      }
    }

    filtered.push(extracted);
    seq++;
  }

  const session = {
    session_id: sessionMeta.session_id || indexEntry?.sessionId,
    project_path: sessionMeta.project_path || indexEntry?.projectPath,
    git_branch: sessionMeta.git_branch || indexEntry?.gitBranch,
    model,
    first_prompt: firstPrompt || indexEntry?.firstPrompt,
    message_count: filtered.length,
    started_at: startedAt || (indexEntry?.created ? new Date(indexEntry.created).toISOString() : null),
    ended_at: endedAt || (indexEntry?.modified ? new Date(indexEntry.modified).toISOString() : null),
  };

  return { session, messages: filtered };
}

// --- Main ---

async function findAllSessions() {
  const sessions = [];
  const seenSessionIds = new Set();

  if (!existsSync(CLAUDE_DIR)) {
    console.error(`Claude projects dir not found: ${CLAUDE_DIR}`);
    process.exit(1);
  }

  const projectDirs = readdirSync(CLAUDE_DIR);

  for (const dir of projectDirs) {
    const projectDir = join(CLAUDE_DIR, dir);
    if (!statSync(projectDir).isDirectory()) continue;

    // Method 1: Read from sessions-index.json (for indexed sessions)
    const indexFile = join(projectDir, 'sessions-index.json');
    if (existsSync(indexFile)) {
      try {
        const index = JSON.parse(readFileSync(indexFile, 'utf-8'));
        const entries = index.entries || [];

        for (const entry of entries) {
          const filePath = entry.fullPath || join(projectDir, `${entry.sessionId}.jsonl`);
          if (!existsSync(filePath)) continue;

          seenSessionIds.add(entry.sessionId);
          sessions.push({
            filePath,
            indexEntry: entry,
            sessionId: entry.sessionId,
            messageCount: entry.messageCount || 0,
          });
        }
      } catch (e) {
        // Skip malformed index files
      }
    }

    // Method 2: Scan for .jsonl files not in the index (active/unindexed sessions)
    try {
      const files = readdirSync(projectDir);
      for (const file of files) {
        if (!file.endsWith('.jsonl')) continue;
        const sessionId = file.replace('.jsonl', '');
        if (seenSessionIds.has(sessionId)) continue; // Already found via index

        const filePath = join(projectDir, file);
        const stat = statSync(filePath);
        if (stat.size < 50) continue; // Skip tiny/empty files

        seenSessionIds.add(sessionId);
        sessions.push({
          filePath,
          indexEntry: null, // No index entry available
          sessionId,
          messageCount: 0, // Unknown, will be determined by parsing
        });
      }
    } catch (e) {
      // Skip unreadable directories
    }
  }

  return sessions;
}

async function main() {
  console.log('🔍 Scanning Claude Code sessions...');

  const allSessions = await findAllSessions();
  console.log(`   Found ${allSessions.length} sessions total`);

  // Get existing sessions from Supabase
  let existing = new Map();
  if (!FULL_SYNC && !DRY_RUN) {
    existing = await getExistingSessions();
    console.log(`   ${existing.size} sessions already in database`);
  }

  // Filter to sessions that need syncing
  const toSync = allSessions.filter(s => {
    if (FULL_SYNC) return true;
    const existingCount = existing.get(s.sessionId);
    if (existingCount === undefined) return true; // New session
    if (s.messageCount === 0) return true; // Unindexed session (active/unknown count), always re-check
    if (s.messageCount > existingCount) return true; // Updated session
    return false;
  });

  console.log(`   ${toSync.length} sessions to sync\n`);

  if (toSync.length === 0) {
    console.log('✅ Everything up to date!');
    return;
  }

  let synced = 0;
  let errors = 0;

  for (const sessionInfo of toSync) {
    try {
      const { session, messages } = processSession(sessionInfo.filePath, sessionInfo.indexEntry);

      if (!session.session_id) {
        console.log(`   ⚠️  Skip: no session_id in ${sessionInfo.filePath}`);
        continue;
      }

      if (messages.length === 0) {
        continue; // Skip empty sessions
      }

      if (DRY_RUN) {
        console.log(`   📋 ${session.session_id.slice(0, 8)}... | ${messages.length} msgs | ${session.project_path || 'unknown'}`);
        console.log(`      first: "${(session.first_prompt || '').slice(0, 60)}"`);
        const tools = [...new Set(messages.flatMap(m => m.tools_used || []))];
        if (tools.length) console.log(`      tools: ${tools.join(', ')}`);
        console.log();
        synced++;
        continue;
      }

      // Upsert session (on conflict session_id, update fields)
      await supabaseQuery(
        'agent_sessions', 'POST', session,
        '?on_conflict=session_id',
        'resolution=merge-duplicates,return=minimal'
      );

      // Delete existing messages for this session (for re-sync)
      await supabaseQuery('agent_messages', 'DELETE', null, `?session_id=eq.${session.session_id}`);

      // Insert messages in batches of 50
      for (let i = 0; i < messages.length; i += 50) {
        const batch = messages.slice(i, i + 50).map(m => ({
          ...m,
          session_id: session.session_id,
        }));
        await supabaseQuery('agent_messages', 'POST', batch, '', 'return=minimal');
      }

      synced++;
      console.log(`   ✅ ${session.session_id.slice(0, 8)}... | ${messages.length} msgs | ${(session.first_prompt || '').slice(0, 50)}`);
    } catch (e) {
      errors++;
      console.error(`   ❌ ${sessionInfo.sessionId.slice(0, 8)}...: ${e.message}`);
    }
  }

  console.log(`\n🎉 Done! Synced: ${synced}, Errors: ${errors}`);
}

main().catch(e => {
  console.error('Fatal error:', e);
  process.exit(1);
});
