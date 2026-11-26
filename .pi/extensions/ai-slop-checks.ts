/**
 * Runs scripts/agent_hook.py after each bash, edit, and write call of pi, as
 * .claude/settings.json and .codex/hooks.json do for Claude Code and Codex.
 * The script checks the message of a new commit and an edited Markdown file.
 * Its violations (exit code 2) are appended to the tool result, which is then
 * marked as an error. Its notes that do not block (exit code 0 and
 * additionalContext on stdout) are appended without the mark.
 *
 * Pi loads this file from .pi/extensions/ once the project is trusted.
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { spawn } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HOOK = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "scripts", "agent_hook.py");
const TOOLS = new Set(["bash", "edit", "write"]);

interface HookResult {
	code: number | null;
	stdout: string;
	stderr: string;
}

function runHook(event: object, cwd: string, signal?: AbortSignal): Promise<HookResult> {
	return new Promise((resolve) => {
		const child = spawn("python3", [HOOK], { cwd, signal });
		let stdout = "";
		let stderr = "";
		child.stdout.on("data", (chunk) => {
			stdout += chunk;
		});
		child.stderr.on("data", (chunk) => {
			stderr += chunk;
		});
		child.on("error", (error) => resolve({ code: null, stdout, stderr: String(error) }));
		child.on("close", (code) => resolve({ code, stdout, stderr }));
		child.stdin.on("error", () => {});
		child.stdin.end(JSON.stringify(event));
	});
}

/** Return the text that the result of the hook adds to the tool result. */
function feedback(result: HookResult): { text: string; isError: boolean } | undefined {
	if (result.code === 2 && result.stderr.trim()) {
		return { text: result.stderr.trim(), isError: true };
	}
	if (result.code === 0 && result.stdout.trim()) {
		try {
			const context = JSON.parse(result.stdout)?.hookSpecificOutput?.additionalContext;
			if (typeof context === "string" && context.trim()) {
				return { text: context.trim(), isError: false };
			}
		} catch {
			return undefined;
		}
	}
	return undefined;
}

export default function (pi: ExtensionAPI) {
	pi.on("tool_result", async (event, ctx) => {
		if (!TOOLS.has(event.toolName)) {
			return undefined;
		}
		const hookEvent = { hook_event_name: "PostToolUse", tool_name: event.toolName, tool_input: event.input, cwd: ctx.cwd };
		const result = await runHook(hookEvent, ctx.cwd, ctx.signal);
		const found = feedback(result);
		if (!found) {
			if (result.code !== 0 && result.code !== 2 && result.stderr.trim() && ctx.hasUI) {
				ctx.ui.notify(`scripts/agent_hook.py failed: ${result.stderr.trim()}`, "warning");
			}
			return undefined;
		}
		const text: { type: "text"; text: string } = { type: "text", text: found.text };
		return {
			content: [...event.content, text],
			structuredContent: event.structuredContent,
			isError: event.isError || found.isError,
		};
	});
}
