# Plugin loading internals

Status: VERIFIED-STATIC for the discovered command/skill/MCP registration bodies; PARTIAL for the global plugin caller graph.

## Plugin discovery and command loading

`chunk-phacttch.js@964054` defines `nle`, the cached plugin-command loader. It returns an empty list when plugins are disabled. Otherwise it consumes enabled plugin records from `Ys(e)` (including plugin errors), accepts an explicitly handed-in command set, and loads each plugin's default `commandsPath`, custom `commandsPaths`, and inline `commandsMetadata`. Directory paths are scanned recursively by the `TDt`/`Tj` path around `chunk-phacttch.js@955000`; the scan is bounded by depth 32 and 4096 directories. Files are read with a 1 MiB limit and parsed as command markdown/frontmatter.

`z6` constructs the normalized prompt-command object. It validates metadata, allowed/disallowed tools, hooks, model/effort/context/background fields, plugin identity, and a lazy `getPromptForCommand`. Malformed PreToolUse or PermissionRequest hook metadata disables the plugin command's hooks and clears its allowed-tools field rather than accepting an invalid hook contract. Command loading emits plugin-load telemetry and logs per-plugin failures; one bad plugin does not erase the other successfully loaded commands.

```text
plugin config/state
  -> Ys(enabled plugins + errors)
  -> nle cache
       -> default/custom command paths -> TDt/Tj file scan
       -> inline commandsMetadata
  -> z6 normalized prompt command
  -> active command registry / model-facing command set
```

## Skills and watcher behavior

`Jao`/`D0e` performs the corresponding skill scan, including default/custom skill directories, manifest enable/disable filtering, realpath deduplication, and the `skillsV5` storage route when Storage V5 is active. The plugin watcher `Ben`/`Xen` (`chunk-phacttch.js@2433000` and `@2441000`) debounces file changes, uses a burst breaker, and defers rescans while a turn is running. Reload is therefore quiescence-sensitive; a filesystem change is not necessarily visible in the middle of the current model turn.

## Plugin MCP servers

`kGt` (`chunk-phacttch.js@1826026`) is the plugin wrapper around MCP connection. It resolves a plugin server, handles unlisted/twin cases, deduplicates connection through `K3.join`, calls `connectMcpServer`, verifies that the plugin remains loaded, and removes the server if it was unloaded during connection. It returns a connected client or a failure result. This is the registration boundary between plugin state and the general MCP lifecycle described in report 06.

## Registration contract and permissions

Plugin commands are tagged with `source: "plugin"` and `pluginInfo`. The normalized command carries permissions and tool restrictions into the ordinary tool/permission machinery; no separate execution engine was found. The source therefore supports a shared permission path, with plugin metadata influencing the allowed-tools set and hooks. A complete proof that every plugin-defined agent/skill/command restriction propagates identically into every subagent mode remains open.

## Failure and lazy paths

- Disabled plugins return no plugin commands.
- A plugin manifest/configuration error is reported while other plugins can continue.
- Malformed command metadata is sanitized; malformed permission hooks are disabled conservatively.
- Directory traversal and file-size limits bound discovery.
- Dynamic command loading is cached and invalidated by the plugin watcher; watcher reload waits for a quiet point.
- Plugin MCP connection is deduplicated and checks for unload races.

## Confidence table

| Claim | Confidence | Anchor |
|---|---|---|
| Commands come from enabled plugins, paths, and inline metadata | VERIFIED-STATIC | `chunk-phacttch.js@964054` |
| Command files are bounded recursive scans and frontmatter-normalized | VERIFIED-STATIC | `chunk-phacttch.js@955000–960000` |
| Skill discovery uses manifest filters, deduplication, and optional Storage V5 | VERIFIED-STATIC | `chunk-phacttch.js@Jao/D0e` |
| Watcher defers reload during active turns | VERIFIED-STATIC | `chunk-phacttch.js@2433000`, `@2441000` |
| Plugin MCP connection checks unload races and deduplicates joins | VERIFIED-STATIC | `chunk-phacttch.js@1826026` |
| Static graph enumerates every plugin capability caller | UNKNOWN | partial REA semantic graph; dynamic imports and configuration dispatch remain |

Open: exact manifest discovery precedence across all scopes, plugin-defined agent execution bodies, hook merge ordering when multiple plugins target one event, and the complete plugin unload cleanup path.
