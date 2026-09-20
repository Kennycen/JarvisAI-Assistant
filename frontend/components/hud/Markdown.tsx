import type { ReactNode } from "react";

/**
 * Minimal markdown renderer for agent replies.
 *
 * This returns React elements rather than an HTML string, deliberately. The
 * agent can relay arbitrary web content through read_page and search_the_web, so
 * anything it echoes back is untrusted: a string-building renderer fed to
 * dangerouslySetInnerHTML would let `<img onerror=...>` execute in the HUD.
 * Building nodes makes markup injection structurally impossible -- React escapes
 * every text child -- and leaves only link protocols to sanitise.
 *
 * Supports: fenced code, inline code, bold, italic, links, ordered and unordered
 * lists, headings, tables, paragraphs.
 */

const ALLOWED_PROTOCOL = /^(?:https?:|mailto:)/i;

function safeHref(raw: string): string | null {
  const trimmed = raw.trim();
  // Rejects javascript:, data:, vbscript: and any other scheme outright.
  return ALLOWED_PROTOCOL.test(trimmed) ? trimmed : null;
}

const INLINE_PATTERN = new RegExp(
  [
    "(`[^`\\n]+`)", // inline code
    "(\\*\\*\\*[^*\\n]+\\*\\*\\*)", // bold italic
    "(\\*\\*[^*\\n]+\\*\\*)", // bold
    "(\\*[^*\\n]+\\*)", // italic
    "(\\[[^\\]\\n]+\\]\\([^)\\n]+\\))", // link
  ].join("|"),
  "g",
);

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  let lastIndex = 0;
  let i = 0;

  for (const match of text.matchAll(INLINE_PATTERN)) {
    const token = match[0];
    const start = match.index ?? 0;

    if (start > lastIndex) nodes.push(text.slice(lastIndex, start));
    lastIndex = start + token.length;
    const key = `${keyPrefix}-i${i++}`;

    if (token.startsWith("`")) {
      nodes.push(
        <code key={key} className="md-code">
          {token.slice(1, -1)}
        </code>,
      );
    } else if (token.startsWith("***")) {
      nodes.push(
        <strong key={key}>
          <em>{token.slice(3, -3)}</em>
        </strong>,
      );
    } else if (token.startsWith("**")) {
      nodes.push(<strong key={key}>{token.slice(2, -2)}</strong>);
    } else if (token.startsWith("*")) {
      nodes.push(<em key={key}>{token.slice(1, -1)}</em>);
    } else {
      const split = token.indexOf("](");
      const label = token.slice(1, split);
      const href = safeHref(token.slice(split + 2, -1));
      // A rejected protocol degrades to the label text, never a live link.
      nodes.push(
        href ? (
          <a
            key={key}
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="md-link"
          >
            {label}
          </a>
        ) : (
          label
        ),
      );
    }
  }

  if (lastIndex < text.length) nodes.push(text.slice(lastIndex));
  return nodes;
}

const TABLE_SEPARATOR = /^\|?[\s\-:|]+\|[\s\-:|]+\|?$/;

function isTableRow(line: string) {
  return /^\|.*\|$/.test(line.trim());
}

function parseCells(line: string) {
  return line
    .trim()
    .replace(/^\||\|$/g, "")
    .split("|")
    .map((c) => c.trim());
}

export default function Markdown({ text }: { text: string }) {
  if (!text.trim()) return null;

  const blocks: ReactNode[] = [];
  const lines = text.split("\n");
  let key = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Fenced code block.
    const fence = line.match(/^```(\w*)\s*$/);
    if (fence) {
      const code: string[] = [];
      i++;
      while (i < lines.length && !/^```/.test(lines[i])) code.push(lines[i++]);
      blocks.push(
        <pre key={key++} className="md-pre">
          <code>{code.join("\n")}</code>
        </pre>,
      );
      continue;
    }

    // Table: a row followed by a separator row.
    if (isTableRow(line) && i + 1 < lines.length && TABLE_SEPARATOR.test(lines[i + 1])) {
      const headers = parseCells(line);
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && isTableRow(lines[i])) rows.push(parseCells(lines[i++]));
      i--;

      blocks.push(
        <table key={key++} className="md-table">
          <thead>
            <tr>
              {headers.map((h, hi) => (
                <th key={hi}>{renderInline(h, `h${key}-${hi}`)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((cells, ri) => (
              <tr key={ri}>
                {cells.map((c, ci) => (
                  <td key={ci}>{renderInline(c, `c${key}-${ri}-${ci}`)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>,
      );
      continue;
    }

    // Consecutive list items collapse into one list.
    const isUl = /^\s*[-*+]\s+/.test(line);
    const isOl = /^\s*\d+[.)]\s+/.test(line);
    if (isUl || isOl) {
      const items: string[] = [];
      const pattern = isUl ? /^\s*[-*+]\s+/ : /^\s*\d+[.)]\s+/;
      while (
        i < lines.length &&
        (isUl ? /^\s*[-*+]\s+/ : /^\s*\d+[.)]\s+/).test(lines[i])
      ) {
        items.push(lines[i].replace(pattern, ""));
        i++;
      }
      i--;

      const rendered = items.map((item, ii) => (
        <li key={ii}>{renderInline(item, `l${key}-${ii}`)}</li>
      ));
      blocks.push(
        isUl ? (
          <ul key={key++} className="md-list">
            {rendered}
          </ul>
        ) : (
          <ol key={key++} className="md-list md-list-ordered">
            {rendered}
          </ol>
        ),
      );
      continue;
    }

    const heading = line.match(/^(#{1,3})\s+(.+)/);
    if (heading) {
      blocks.push(
        <div key={key++} className="md-heading">
          {renderInline(heading[2], `hd${key}`)}
        </div>,
      );
      continue;
    }

    if (!line.trim()) continue;

    blocks.push(
      <p key={key++} className="md-p">
        {renderInline(line, `p${key}`)}
      </p>,
    );
  }

  return <div className="md">{blocks}</div>;
}
