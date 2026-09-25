/**
 * md-log — mirror the session to a markdown file for comfortable reading.
 *
 * Designed for long teaching/learning sessions where the terminal is hard on
 * the eyes and markdown/math/code don't render. The linked .md file is meant
 * to be viewed rendered (e.g. in Obsidian), so assistant text with $...$ math,
 * code blocks, and markdown all render natively — no rendering work here.
 *
 * Captures only reading-relevant content:
 *   - user prompts
 *   - assistant text (lesson prose)
 *   - quiz / ask_user_question Q&A blocks
 * Other tools (bash, read, write, edit, ...) are omitted.
 *
 * Quiz/ask questions are written BEFORE the user answers (on tool_call), so the
 * reader sees the question appear live; the answer + feedback are appended on
 * tool_result. The question block NEVER contains the correct answer or
 * explanation (the user reads this file live).
 *
 * Commands:
 *   /md-log <filepath>  — Link a markdown file and backfill the session.
 *   /md-unlog           — Stop logging.
 *
 * Auto-log: for every NEW interactive session (no prior messages), the first
 * user prompt immediately creates and links a uniquely named placeholder file
 * (YYYY-MM-DD-session-<uid>.md) in AUTO_LOG_DIR, so logging starts with zero
 * gap. In the background, an LLM call summarizes the prompt into a topic slug
 * and the file is safely renamed to YYYY-MM-DD-<slug>.md (exclusive create,
 * never overwriting an existing note). If naming fails or times out, the
 * placeholder name is kept. /md-unlog before the first prompt disables
 * auto-log for the session; a pending rename is cancelled by /md-unlog,
 * /md-log, or session shutdown. Set AUTO_LOG = false to disable entirely.
 *
 * Append-only. No send-back-to-agent functionality (that lived in the old
 * .md-link extension this was modeled on).
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

const QA_TOOLS = new Set(["quiz", "ask_user_question"]);

const AUTO_LOG = true;
const AUTO_LOG_DIR = path.join(os.homedir(), "Documents/notes/01-Inbox");
const NAMING_TIMEOUT_MS = 20_000;
const MAX_SLUG_LENGTH = 60;

export default function mdLog(pi: ExtensionAPI) {
	let logFile: string | null = null;
	let autoLogEligible = false; // fresh session, no explicit link/unlink yet
	let shutDown = false; // session runtime torn down; cancel background work

	// --- State restoration on session restart ---

	pi.on("session_start", async (_event, ctx) => {
		let lastLinkData: { file: string | null } | undefined;
		let hasMessages = false;
		for (const entry of ctx.sessionManager.getEntries()) {
			if (entry.type === "custom" && entry.customType === "md-log") {
				lastLinkData = entry.data as { file: string | null } | undefined;
			}
			if (entry.type === "message") hasMessages = true;
		}
		if (lastLinkData?.file) {
			logFile = lastLinkData.file;
			const theme = ctx.ui.theme;
			ctx.ui.setStatus(
				"md-log",
				theme.fg("accent", "🗒 ") + theme.fg("dim", path.basename(logFile)),
			);
		}
		// Auto-log only for genuinely new interactive sessions: no messages yet
		// and no md-log link/unlink decision recorded.
		autoLogEligible = AUTO_LOG && ctx.hasUI && !hasMessages && lastLinkData === undefined;
		shutDown = false;
	});

	pi.on("session_shutdown", async () => {
		// Invalidate any pending background naming/rename for this runtime.
		shutDown = true;
	});

	// --- Auto-log: name the file from the topic of the first prompt ---

	function capSlug(slug: string): string {
		const capped = slug.slice(0, MAX_SLUG_LENGTH).replace(/-+$/, "");
		return capped || "session";
	}

	function fallbackSlug(text: string): string {
		const slug = text
			.toLowerCase()
			.replace(/[^a-z0-9\s-]/g, "")
			.trim()
			.split(/\s+/)
			.slice(0, 6)
			.join("-");
		return capSlug(slug);
	}

	function sanitizeSlug(raw: string): string {
		const slug = raw
			.toLowerCase()
			.replace(/[`"'.]/g, "")
			.replace(/\.md$/, "")
			.replace(/[^a-z0-9-]+/g, "-")
			.replace(/-{2,}/g, "-")
			.replace(/^-|-$/g, "");
		return capSlug(slug.split("-").slice(0, 8).join("-"));
	}

	function setLogStatus(ctx: any, file: string): void {
		const theme = ctx.ui.theme;
		ctx.ui.setStatus(
			"md-log",
			theme.fg("accent", "🗒 ") + theme.fg("dim", path.basename(file)),
		);
	}

	// Create `<base>.md` (or `<base>-2.md`, ...) in AUTO_LOG_DIR with exclusive
	// create (flag "wx"), so concurrent pi sessions can never clobber each
	// other's files. Returns the created path; throws if no free name is found.
	function createExclusive(baseName: string, content: string): string {
		fs.mkdirSync(AUTO_LOG_DIR, { recursive: true });
		for (let n = 1; n <= 100; n++) {
			const name = n === 1 ? `${baseName}.md` : `${baseName}-${n}.md`;
			const candidate = path.join(AUTO_LOG_DIR, name);
			try {
				fs.writeFileSync(candidate, content, { encoding: "utf-8", flag: "wx" });
				return candidate;
			} catch (err: any) {
				if (err?.code !== "EEXIST") throw err;
			}
		}
		throw new Error(`no free filename for ${baseName}.md in ${AUTO_LOG_DIR}`);
	}

	// Synchronously create and link a uniquely named placeholder file, then
	// kick off background topic naming. Called from the first user message_end
	// with no awaits before file creation, so every subsequent event is logged.
	function startAutoLog(firstPrompt: string, ctx: any): void {
		autoLogEligible = false;
		const date = new Date().toISOString().slice(0, 10);
		const uid = Math.random().toString(36).slice(2, 8);
		let created: string;
		try {
			created = createExclusive(`${date}-session-${uid}`, "");
		} catch (err: any) {
			ctx.ui.notify(`md-log: could not create log file: ${err?.message ?? err}`, "error");
			return;
		}
		logFile = created;
		pi.appendEntry("md-log", { file: created });
		setLogStatus(ctx, created);
		ctx.ui.notify(`md-log: ${path.basename(created)}`, "info");
		void renameToTopic(created, firstPrompt, ctx);
	}

	async function renameToTopic(fromFile: string, firstPrompt: string, ctx: any): Promise<void> {
		// Name the topic with the LLM; fall back to first-prompt words on
		// failure or timeout (a stalled request must not block naming forever).
		let timer: ReturnType<typeof setTimeout> | undefined;
		const timeout = new Promise<string>((resolve) => {
			timer = setTimeout(() => resolve(fallbackSlug(firstPrompt)), NAMING_TIMEOUT_MS);
		});
		const slug = await Promise.race([generateSlug(firstPrompt, ctx), timeout]);
		clearTimeout(timer);

		await withLock(() => {
			// Only rename while our placeholder is still the active log target.
			// /md-unlog, manual /md-log, and session shutdown all invalidate this.
			if (shutDown || logFile !== fromFile) return;
			const date = new Date().toISOString().slice(0, 10);
			try {
				const content = fs.readFileSync(fromFile, "utf-8");
				// "Rename" as exclusive-create + delete: never overwrites an
				// existing note, even against concurrent sessions.
				const renamed = createExclusive(`${date}-${slug}`, content);
				fs.rmSync(fromFile);
				logFile = renamed;
				pi.appendEntry("md-log", { file: renamed });
				setLogStatus(ctx, renamed);
				ctx.ui.notify(`md-log: renamed to ${path.basename(renamed)}`, "info");
			} catch {
				// Keep logging under the placeholder name.
				ctx.ui.notify(`md-log: rename failed, keeping ${path.basename(fromFile)}`, "warning");
			}
		});
	}

	async function generateSlug(firstPrompt: string, ctx: any): Promise<string> {
		try {
			const model = ctx.model;
			if (!model || !ctx.modelRegistry.hasConfiguredAuth(model)) {
				return fallbackSlug(firstPrompt);
			}
			const prompt =
				"Summarize the TOPIC of the following request as a filename slug: " +
				"3-6 words, lowercase, kebab-case, only [a-z0-9-]. " +
				"Reply with ONLY the slug, nothing else.\n\nRequest:\n" +
				firstPrompt.slice(0, 2000);
			const response = await ctx.modelRegistry.complete(model, {
				messages: [
					{
						role: "user" as const,
						content: [{ type: "text" as const, text: prompt }],
						timestamp: Date.now(),
					},
				],
			});
			const text = (response.content || [])
				.filter((c: any) => c.type === "text")
				.map((c: any) => c.text)
				.join(" ")
				.trim();
			const slug = sanitizeSlug(text);
			return slug || fallbackSlug(firstPrompt);
		} catch {
			return fallbackSlug(firstPrompt);
		}
	}

	// --- Serialization: events can fire close together; keep appends ordered ---

	let writeLock: Promise<void> = Promise.resolve();
	function withLock<T>(fn: () => T | Promise<T>): Promise<T> {
		const prev = writeLock;
		let release: () => void;
		writeLock = new Promise<void>((r) => {
			release = r;
		});
		return prev.then(fn).finally(() => release!());
	}

	function appendToFile(text: string): void {
		if (!logFile) return;
		try {
			let current = "";
			if (fs.existsSync(logFile)) {
				current = fs.readFileSync(logFile, "utf-8");
			}
			const prefix = current.trim().length > 0 ? "\n\n" : "";
			fs.writeFileSync(logFile, current + prefix + text + "\n", "utf-8");
		} catch {
			// File may have been deleted externally; ignore.
		}
	}

	// --- Formatting ---

	function callout(type: string, title: string, bodyLines: string[]): string {
		const lines = [`> [!${type}] ${title}`];
		for (const line of bodyLines) {
			lines.push(line.length === 0 ? ">" : `> ${line}`);
		}
		return lines.join("\n");
	}

	function userBlock(text: string): string {
		return `> [!quote] YOU\n\n${text}`;
	}

	// Skill declarations (`<skill name="..." ...> ...whole SKILL.md... </skill>`)
	// are system-injected context, not user prose. Replace each with a compact
	// callout noting the skill was loaded, so the log keeps the signal without
	// the noise. Runs on already-trimmed text.
	function stripSkillBlocks(text: string): string {
		return text.replace(
			/<skill\b([^>]*)>[\s\S]*?<\/skill>/g,
			(_match, attrs: string) => {
				const name = /name="([^"]+)"/.exec(attrs)?.[1];
				return `> [!note] SKILL loaded: ${name ?? "(unknown)"}`;
			},
		);
	}

	function assistantBlock(text: string): string {
		return `> [!abstract] PI\n\n${text}`;
	}

	function optionsList(options: Array<{ label: string }>): string[] {
		return options.map((o, i) => `${i + 1}. ${o.label}`);
	}

	function questionCallout(label: string, question: string, context: string | undefined, options: Array<{ label: string }>): string {
		const body: string[] = [];
		for (const line of question.split("\n")) body.push(line);
		if (context) {
			body.push("");
			for (const line of context.split("\n")) body.push(line);
		}
		if (options.length > 0) {
			body.push("");
			body.push(...optionsList(options));
		}
		return callout("question", label, body);
	}

	function answerCalloutQuiz(details: any): string {
		const status = details?.status;
		if (status === "cancelled") {
			return callout("warning", "Quiz — cancelled", ["(user skipped)"]);
		}
		if (status === "unavailable") {
			return callout("warning", "Quiz — unavailable", [details?.message || ""]);
		}
		// "I don't know" is neither correct nor incorrect — it's a distinct signal,
		// so it never renders as a red ✗.
		const dontKnow = details?.dontKnow === true;
		const correct = details?.correct === true;
		const type = dontKnow ? "question" : correct ? "success" : "failure";
		const title = dontKnow
			? "Quiz — I don't know"
			: correct
				? "Quiz — correct ✓"
				: "Quiz — incorrect ✗";
		const body: string[] = [];

		if (dontKnow) {
			body.push("Your answer: I don't know");
		} else {
			const answers: any[] = details?.answers || [];
			const sel = answers.map((a) => `${a.index}. ${a.label}`).join(", ") || "(none)";
			body.push(`Your answer: ${sel}`);
		}

		const correctIndices: number[] = details?.correctIndices || [];
		const correctStr = correctIndices.map((i) => `${i}`).join(", ");
		body.push(`Correct answer: ${correctStr}`);

		// Optional free-text note the user typed in the always-present note field.
		// Only present (in details) when non-empty, so no guard for empty strings.
		if (details?.note) {
			body.push("");
			const noteLines = String(details.note).split("\n");
			body.push(`Note: ${noteLines[0]}`);
			for (let i = 1; i < noteLines.length; i++) body.push(noteLines[i]);
		}

		if (details?.explanation) {
			body.push("");
			for (const line of String(details.explanation).split("\n")) body.push(line);
		}
		return callout(type, title, body);
	}

	function answerCalloutAsk(details: any): string {
		const status = details?.status;
		if (status === "cancelled") {
			return callout("warning", "Question — cancelled", ["(user skipped)"]);
		}
		if (status === "unavailable") {
			return callout("warning", "Question — unavailable", [details?.message || ""]);
		}
		const answers: any[] = details?.answers || [];
		const body: string[] = answers.map((a) => {
			if (a.type === "other") return `Other: ${a.label}`;
			if (a.type === "text") return a.label;
			return `${a.index}. ${a.label}`;
		});
		if (body.length === 0) body.push("(no answer)");
		return callout("example", "Answer", body);
	}

	// --- Event handlers ---

	pi.on("message_end", async (event, _ctx) => {
		if (!logFile && !autoLogEligible) return;
		const msg = event.message;
		if (!msg || !("role" in msg)) return;

		if (msg.role === "user") {
			const text = typeof msg.content === "string"
				? msg.content
				: Array.isArray(msg.content)
					? msg.content.filter((c: any) => c.type === "text").map((c: any) => c.text).join("\n")
					: "";
			const trimmed = stripSkillBlocks(text.trim());
			if (!trimmed) return;
			if (!logFile && autoLogEligible) {
				// Create + link the placeholder synchronously so the log is live
				// before any assistant/tool events for this turn.
				startAutoLog(trimmed, _ctx);
				if (!logFile) return; // creation failed (already notified)
			}
			await withLock(() => appendToFile(userBlock(trimmed)));
			return;
		}

		if (msg.role === "assistant") {
			if (!logFile) return;
			const textParts = (msg.content || [])
				.filter((c: any) => c.type === "text")
				.map((c: any) => (c.text as string).trim())
				.filter((t: string) => t.length > 0);
			if (textParts.length === 0) return;
			await withLock(() => appendToFile(assistantBlock(textParts.join("\n\n"))));
			return;
		}
		// toolResult messages are handled by the tool_result event (for QA tools).
	});

	// ask_user_question never shuffles its options, so the tool_call args are
	// already the true display order — safe to write the question live, before
	// the user answers.
	pi.on("tool_call", async (event, _ctx) => {
		if (!logFile) return;
		const toolName = (event as any).toolName;
		if (toolName !== "ask_user_question") return;
		const input = (event as any).input || {};
		const question: string = input.question || "";
		const context: string | undefined = input.details?.trim() || undefined;
		const options: Array<{ label: string }> = Array.isArray(input.options) ? input.options : [];
		const block = questionCallout("Question", question, context, options);
		await withLock(() => appendToFile(block));
	});

	// quiz DOES shuffle its options inside execute(), so the tool_call args are
	// the pre-shuffle author order — NOT what the user is shown. quiz emits an
	// onUpdate() with the true (post-shuffle) order before it blocks on the
	// user's answer; wait for that instead so the logged order always matches
	// what's on screen. Guard against duplicate writes if multiple updates fire
	// for the same call.
	const loggedQuizQuestion = new Set<string>();
	pi.on("tool_execution_update", async (event, _ctx) => {
		if (!logFile) return;
		const toolName = (event as any).toolName;
		if (toolName !== "quiz") return;
		const toolCallId = (event as any).toolCallId;
		if (loggedQuizQuestion.has(toolCallId)) return;
		const shuffled = (event as any).partialResult?.details?.options as Array<{ index: number; label: string }> | undefined;
		if (!shuffled || shuffled.length === 0) return;
		loggedQuizQuestion.add(toolCallId);
		const input = (event as any).args || {};
		const question: string = input.question || "";
		const context: string | undefined = input.details?.trim() || undefined;
		const options = shuffled.map((o) => ({ label: o.label }));
		const block = questionCallout("Quiz", question, context, options);
		await withLock(() => appendToFile(block));
	});

	pi.on("tool_result", async (event, _ctx) => {
		if (!logFile) return;
		const toolName = (event as any).toolName;
		if (!QA_TOOLS.has(toolName)) return;
		const details = (event as any).details;
		const block = toolName === "quiz"
			? answerCalloutQuiz(details)
			: answerCalloutAsk(details);
		await withLock(() => appendToFile(block));
	});

	// --- Commands ---

	pi.registerCommand("md-log", {
		description: "Mirror the session to a markdown file (backfills history)",
		handler: async (args, ctx: any) => {
			const filepath = args.trim();
			if (!filepath) {
				ctx.ui.notify("Usage: /md-log <filepath>", "warning");
				return;
			}
			if (typeof ctx.isIdle === "function" && !ctx.isIdle()) {
				ctx.ui.notify("Wait for the agent to finish before linking.", "warning");
				return;
			}

			const resolved = path.isAbsolute(filepath) ? filepath : path.resolve(ctx.cwd, filepath);

			// The file must already exist — /md-log links into an existing note,
			// it never creates one. This avoids silently scattering new files
			// (and parent directories) around the vault from a typo'd path.
			if (!fs.existsSync(resolved)) {
				ctx.ui.notify(`File does not exist: ${resolved}`, "error");
				return;
			}
			if (!fs.statSync(resolved).isFile()) {
				ctx.ui.notify(`Not a file: ${resolved}`, "error");
				return;
			}

			logFile = resolved;
			autoLogEligible = false; // manual link overrides auto-log
			pi.appendEntry("md-log", { file: resolved });

			// Backfill the active branch.
			const written = backfill(ctx);

			const theme = ctx.ui.theme;
			ctx.ui.setStatus(
				"md-log",
				theme.fg("accent", "🗒 ") + theme.fg("dim", path.basename(resolved)),
			);
			ctx.ui.notify(`Linked: ${resolved} (${written} entries backfilled)`, "success");
		},
	});

	pi.registerCommand("md-unlog", {
		description: "Stop mirroring the session to a markdown file",
		handler: async (_args, ctx) => {
			if (!logFile) {
				if (autoLogEligible) {
					autoLogEligible = false;
					pi.appendEntry("md-log", { file: null });
					ctx.ui.notify("Auto-log disabled for this session", "info");
				} else {
					ctx.ui.notify("No file linked", "warning");
				}
				return;
			}
			const name = path.basename(logFile);
			logFile = null;
			autoLogEligible = false;
			pi.appendEntry("md-log", { file: null });
			ctx.ui.setStatus("md-log", undefined);
			ctx.ui.notify(`Unlinked: ${name}`, "info");
		},
	});

	// --- Backfill ---

	function backfill(ctx: any): number {
		if (!logFile) return 0;
		const entries: any[] = ctx.sessionManager.getEntries();
		if (entries.length === 0) return 0;

		const byId = new Map<string, any>();
		for (const e of entries) if (e.id) byId.set(e.id, e);

		// Active leaf = last entry that has an id (skip the session header).
		let leaf: any = null;
		for (let i = entries.length - 1; i >= 0; i--) {
			if (entries[i].id) {
				leaf = entries[i];
				break;
			}
		}
		if (!leaf) return 0;

		// Walk parent chain to root.
		const chain: any[] = [];
		let cur: any = leaf;
		const seen = new Set<string>();
		while (cur && cur.id && !seen.has(cur.id)) {
			seen.add(cur.id);
			chain.push(cur);
			cur = cur.parentId ? byId.get(cur.parentId) : null;
		}
		chain.reverse();

		// Track tool-call args from assistant messages so we can pair with results.
		const toolCallArgs = new Map<string, { name: string; args: any }>();

		const blocks: string[] = [];
		let count = 0;
		for (const entry of chain) {
			if (entry.type !== "message") continue;
			const msg = entry.message;
			if (!msg || !("role" in msg)) continue;
			count++;

			if (msg.role === "user") {
				const text = typeof msg.content === "string"
					? msg.content
					: Array.isArray(msg.content)
						? msg.content.filter((c: any) => c.type === "text").map((c: any) => c.text).join("\n")
						: "";
				const trimmed = stripSkillBlocks(text.trim());
				if (trimmed) blocks.push(userBlock(trimmed));
				continue;
			}

			if (msg.role === "assistant") {
				// Index tool calls for later pairing.
				for (const c of msg.content || []) {
					if (c.type === "toolCall" && QA_TOOLS.has(c.name)) {
						toolCallArgs.set(c.id, { name: c.name, args: c.arguments });
					}
				}
				const textParts = (msg.content || [])
					.filter((c: any) => c.type === "text")
					.map((c: any) => (c.text as string).trim())
					.filter((t: string) => t.length > 0);
				if (textParts.length > 0) blocks.push(assistantBlock(textParts.join("\n\n")));
				continue;
			}

			if (msg.role === "toolResult") {
				if (!QA_TOOLS.has(msg.toolName)) continue;
				const tc = toolCallArgs.get(msg.toolCallId);
				// Question block. For quiz, use the persisted result's `details.options`
				// — the TRUE post-shuffle display order the user actually saw — rather
				// than the original tool-call args, which are the pre-shuffle author
				// order and can mismatch what's on screen. ask_user_question never
				// shuffles, so its tool-call args are already the true order.
				if (tc) {
					const a = tc.args || {};
					const label = tc.name === "quiz" ? "Quiz" : "Question";
					const shuffled = msg.toolName === "quiz"
						? (msg.details?.options as Array<{ index: number; label: string }> | undefined)
						: undefined;
					const options = shuffled && shuffled.length > 0
						? shuffled.map((o) => ({ label: o.label }))
						: (Array.isArray(a.options) ? a.options : []);
					blocks.push(questionCallout(label, a.question || "", a.details?.trim() || undefined, options));
				}
				if (msg.toolName === "quiz") {
					blocks.push(answerCalloutQuiz(msg.details));
				} else {
					blocks.push(answerCalloutAsk(msg.details));
				}
				continue;
			}
		}

		if (blocks.length > 0) {
			try {
				fs.writeFileSync(logFile, blocks.join("\n\n") + "\n", "utf-8");
			} catch {
				// ignore
			}
		}
		return count;
	}
}
