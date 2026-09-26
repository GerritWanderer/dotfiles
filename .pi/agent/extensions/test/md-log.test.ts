import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import * as fs from 'node:fs';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

function fixture(file?: string) {
  const entries: any[] = file ? [{ type: 'custom', customType: 'md-log', data: { file } }] : [];
  const handlers = new Map<string, Function>();
  const commands = new Map<string, Function>();
  const statuses: string[] = [];
  const notifications: string[] = [];
  const pi = {
    on: (name: string, handler: Function) => handlers.set(name, handler),
    registerCommand: (name: string, { handler }: { handler: Function }) => commands.set(name, handler),
    appendEntry: (customType: string, data: unknown) => entries.push({ type: 'custom', id: 'c'.repeat(8), customType, data }),
  };
  const ctx = {
    cwd: '/tmp/coding-repo', hasUI: true,
    ui: {
      theme: { fg: (_: string, value: string) => value },
      setStatus: (_: string, value: string) => statuses.push(value),
      notify: (text: string) => notifications.push(text),
    },
    sessionManager: { getEntries: () => entries, getBranch: () => entries },
  };
  const message = (id: string, role: string, text: string) => {
    entries.push({ type: 'message', id, message: { role, content: [{ type: 'text', text }] } });
  };
  return { pi, ctx, handlers, commands, entries, statuses, notifications, message };
}

test('normal-session md-log still mirrors user/assistant text and excludes ordinary tool output', async () => {
  delete process.env.PI_SUBAGENT_AGENT;
  const dir = mkdtempSync(join(tmpdir(), 'md-log-normal-'));
  const file = join(dir, 'normal.md');
  fs.writeFileSync(file, '');
  try {
    const { default: mdLog } = await import('../md-log.ts?normal');
    const f = fixture(file);
    f.message('11111111', 'user', 'Earlier message');
    mdLog(f.pi as any);
    await f.handlers.get('session_start')!({}, f.ctx);
    await f.handlers.get('message_end')!({ message: { role: 'user', content: [{ type: 'text', text: 'Normal learner input' }] } }, f.ctx);
    await f.handlers.get('message_end')!({ message: { role: 'assistant', content: [{ type: 'text', text: 'Normal assistant response' }] } }, f.ctx);
    await f.handlers.get('message_end')!({ message: { role: 'toolResult', toolName: 'bash', content: [{ type: 'text', text: 'SECRET OUTPUT' }] } }, f.ctx);
    const content = fs.readFileSync(file, 'utf8');
    assert.match(content, /Normal learner input/);
    assert.match(content, /Normal assistant response/);
    assert.doesNotMatch(content, /SECRET OUTPUT/);
    await f.commands.get('md-unlog')!('', f.ctx);
    assert.equal(f.statuses.at(-1), undefined);
    await f.handlers.get('session_shutdown')!({}, f.ctx);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('first pairing turn creates a separate titled note and logs only conversation text', async () => {
  const home = mkdtempSync(join(tmpdir(), 'md-log-first-'));
  const previousHome = process.env.HOME;
  process.env.HOME = home;
  process.env.PI_SUBAGENT_AGENT = 'tdd-partner';
  process.env.PI_SUBAGENT_NAME = 'Pairing demo';
  const parentNote = join(home, 'parent.md');
  fs.writeFileSync(parentNote, 'Parent session only');
  try {
    const { default: mdLog } = await import('../md-log.ts?first-pairing');
    const f = fixture();
    mdLog(f.pi as any);
    await f.handlers.get('session_start')!({}, f.ctx);
    const initial = { role: 'user', content: [{ type: 'text', text: 'parent kickoff wrapper' }] };
    f.message('11111111', 'user', 'parent kickoff wrapper');
    await f.handlers.get('message_end')!({ message: initial }, f.ctx);
    const inbox = join(home, 'Documents/notes/01-Inbox');
    const notes = fs.readdirSync(inbox);
    assert.equal(notes.length, 1);
    assert.match(notes[0], /pairing-coding-repo-pairing-demo/);
    const note = join(inbox, notes[0]);
    f.message('22222222', 'assistant', 'Dependencies:\n```mermaid\ngraph LR\nA --> B\n```');
    f.message('33333333', 'user', 'What does A import?');
    f.message('44444444', 'assistant', 'A imports B.');
    f.entries.push({ type: 'message', id: '55555555', message: { role: 'toolResult', toolName: 'read', content: [{ type: 'text', text: 'PRIVATE TOOL OUTPUT' }, { type: 'image', data: 'PNG_BYTES' }] } });
    await f.handlers.get('agent_end')!({}, f.ctx);
    const content = fs.readFileSync(note, 'utf8');
    assert.match(content, /```mermaid\ngraph LR\nA --> B\n```/);
    assert.match(content, /What does A import\?/);
    assert.match(content, /A imports B\./);
    assert.doesNotMatch(content, /parent kickoff wrapper|PRIVATE TOOL OUTPUT|PNG_BYTES/);
    assert.equal(fs.readFileSync(parentNote, 'utf8'), 'Parent session only');
    await f.handlers.get('session_shutdown')!({}, f.ctx);
  } finally {
    if (previousHome === undefined) delete process.env.HOME; else process.env.HOME = previousHome;
    delete process.env.PI_SUBAGENT_AGENT;
    delete process.env.PI_SUBAGENT_NAME;
    fs.rmSync(home, { recursive: true, force: true });
  }
});

test('pairing note creation failure is visible and does not claim a link', async () => {
  const home = mkdtempSync(join(tmpdir(), 'md-log-failure-'));
  const previousHome = process.env.HOME;
  process.env.HOME = home;
  process.env.PI_SUBAGENT_AGENT = 'tdd-partner';
  const notesDir = join(home, 'Documents/notes');
  fs.mkdirSync(notesDir, { recursive: true });
  fs.chmodSync(notesDir, 0o555);
  try {
    const { default: mdLog } = await import('../md-log.ts?creation-failure');
    const f = fixture();
    mdLog(f.pi as any);
    await f.handlers.get('session_start')!({}, f.ctx);
    await f.handlers.get('message_end')!({ message: { role: 'user', content: [{ type: 'text', text: 'bootstrap' }] } }, f.ctx);
    assert.ok(f.notifications.some((n) => n.includes('could not create log file')));
    assert.equal(f.entries.some((e) => e.customType === 'md-log' && e.data.file), false);
    await f.handlers.get('session_shutdown')!({}, f.ctx);
  } finally {
    fs.chmodSync(notesDir, 0o755);
    if (previousHome === undefined) delete process.env.HOME; else process.env.HOME = previousHome;
    delete process.env.PI_SUBAGENT_AGENT;
    fs.rmSync(home, { recursive: true, force: true });
  }
});

test('pairing reconciliation preserves private permissions and symlinked note targets', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'md-log-private-'));
  fs.chmodSync(dir, 0o755);
  const target = join(dir, 'private.md');
  const link = join(dir, 'linked.md');
  fs.writeFileSync(target, '');
  fs.chmodSync(target, 0o600);
  fs.symlinkSync(target, link);
  process.env.PI_SUBAGENT_AGENT = 'tdd-partner';
  const originalUmask = process.umask(0o022);
  try {
    const { default: mdLog } = await import('../md-log.ts?private-symlink');
    const f = fixture(link);
    f.message('11111111', 'user', 'parent bootstrap');
    f.message('22222222', 'assistant', 'First private response');
    mdLog(f.pi as any);
    await f.handlers.get('session_start')!({}, f.ctx);
    assert.ok(fs.lstatSync(link).isSymbolicLink());
    assert.equal(fs.statSync(target).mode & 0o777, 0o600);
    f.message('33333333', 'assistant', 'Second private response');
    await f.handlers.get('agent_end')!({}, f.ctx);
    assert.ok(fs.lstatSync(link).isSymbolicLink());
    assert.equal(fs.statSync(target).mode & 0o777, 0o600);
    const content = fs.readFileSync(target, 'utf8');
    assert.match(content, /First private response/);
    assert.match(content, /Second private response/);
    assert.doesNotMatch(content, /parent bootstrap/);
    await f.handlers.get('session_shutdown')!({}, f.ctx);
  } finally {
    process.umask(originalUmask);
    delete process.env.PI_SUBAGENT_AGENT;
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('restored pairing session replays missed exchanges exactly once', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'md-log-restart-'));
  const file = join(dir, 'pairing.md');
  fs.writeFileSync(file, '> [!abstract] PI\n\nInitial\n\n<!-- pi-md-log:22222222 -->\n');
  process.env.PI_SUBAGENT_AGENT = 'tdd-partner';
  try {
    const { default: mdLog } = await import('../md-log.ts?restart');
    const f = fixture(file);
    f.message('11111111', 'user', 'bootstrap');
    f.message('22222222', 'assistant', 'Initial');
    f.message('33333333', 'user', 'Missed while offline');
    f.message('44444444', 'assistant', 'Recovered answer');
    mdLog(f.pi as any);
    await f.handlers.get('session_start')!({}, f.ctx);
    const content = fs.readFileSync(file, 'utf8');
    assert.equal(content.match(/Initial/g)?.length, 1);
    assert.equal(content.match(/Missed while offline/g)?.length, 1);
    assert.equal(content.match(/Recovered answer/g)?.length, 1);
    await f.handlers.get('session_shutdown')!({}, f.ctx);
  } finally {
    delete process.env.PI_SUBAGENT_AGENT;
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('pairing log catches up after an unwritable note, without duplicates, and respects unlink', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'md-log-pairing-'));
  const file = join(dir, 'pairing.md');
  fs.writeFileSync(file, '');
  process.env.PI_SUBAGENT_AGENT = 'tdd-partner';
  try {
    const { default: mdLog } = await import('../md-log.ts?pairing');
    const f = fixture(file);
    mdLog(f.pi as any);
    f.message('11111111', 'user', 'parent launch wrapper');
    f.message('22222222', 'assistant', 'First briefing');
    await f.handlers.get('session_start')!({}, f.ctx);
    assert.match(fs.readFileSync(file, 'utf8'), /First briefing/);
    assert.doesNotMatch(fs.readFileSync(file, 'utf8'), /parent launch wrapper/);

    fs.chmodSync(file, 0o444);
    f.message('33333333', 'user', 'Please explain the type.');
    f.message('44444444', 'assistant', 'Type is number.');
    await f.handlers.get('agent_end')!({}, f.ctx);
    assert.match(f.statuses.at(-1)!, /INCOMPLETE/);
    assert.ok(f.notifications.some((n) => n.includes('note incomplete')));

    fs.chmodSync(file, 0o644);
    await f.handlers.get('agent_end')!({}, f.ctx);
    await f.handlers.get('agent_end')!({}, f.ctx);
    const content = fs.readFileSync(file, 'utf8');
    assert.equal(content.match(/Please explain the type/g)?.length, 1);
    assert.equal(content.match(/Type is number/g)?.length, 1);
    assert.match(f.statuses.at(-1)!, /pairing.md/);
    assert.doesNotMatch(f.statuses.at(-1)!, /INCOMPLETE/);
    assert.ok(f.entries.some((e) => e.customType === 'md-log-checkpoint' && e.data.lastEntryId === '44444444'));

    await f.commands.get('md-unlog')!('', f.ctx);
    f.message('55555555', 'user', 'Do not log this.');
    await f.handlers.get('agent_end')!({}, f.ctx);
    assert.equal(fs.readFileSync(file, 'utf8'), content);
    await f.handlers.get('session_shutdown')!({}, f.ctx);

    const restored = fixture(file);
    restored.entries.push({ type: 'custom', id: 'eeeeeeee', customType: 'md-log', data: { file: null } });
    mdLog(restored.pi as any);
    await restored.handlers.get('session_start')!({}, restored.ctx);
    restored.message('66666666', 'user', 'Still unlinked');
    await restored.handlers.get('agent_end')!({}, restored.ctx);
    assert.equal(fs.readFileSync(file, 'utf8'), content);
    await restored.handlers.get('session_shutdown')!({}, restored.ctx);
  } finally {
    delete process.env.PI_SUBAGENT_AGENT;
    fs.chmodSync(file, 0o644);
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
