"""Pure TeX transforms for splitting dense Beamer frames safely."""

from __future__ import annotations

import re

# Pandoc frame titles can wrap across source lines and contain nested formatting
# such as ``\texttt{...}`` or ``\texorpdfstring{...}{...}``. A lazy ``.*?``
# stops at the first inner closing brace and turns the remainder of the title
# into frame content when dense frames are split. Match the bounded nesting
# Pandoc emits so every continuation frame receives the complete title.
_FRAME_TITLE_RE = r"\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}"
_FRAME_RE = re.compile(
    rf"(?P<open>\\begin\{{frame\}}(?:\[[^\]]*\])?(?:{_FRAME_TITLE_RE})?\n)"
    r"(?P<body>.*?)"
    r"(?P<close>\\end\{frame\})",
    re.DOTALL,
)
_ENV_BEGIN_RE = re.compile(r"\\begin\{(?P<name>[A-Za-z*]+)\}")
_ENV_END_RE = re.compile(r"\\end\{(?P<name>[A-Za-z*]+)\}")
_TEX_GROUP_RE = re.compile(r"\\(?P<kind>begin|end)group\b")
_ISOLATE_SLIDE_ENVS = frozenset(
    {"codelisting", "lstlisting", "verbatim", "description", "enumerate", "figure", "itemize", "longtable", "table"}
)
_FRAMEBREAK_MARKER = "\n\\par\n\\framebreak\n"


def _append_framebreak(lines: list[str]) -> None:
    """Append one frame break unless the generated TeX already has one."""
    if lines and lines[-1].rstrip().endswith(r"\framebreak"):
        return
    lines.append(_FRAMEBREAK_MARKER)


def _brace_delta(line: str) -> int:
    """Return the unescaped TeX-brace balance contributed by one source line."""
    delta = 0
    escaped = False
    for character in line:
        if character == "{" and not escaped:
            delta += 1
        elif character == "}" and not escaped:
            delta -= 1
        if character == "\\" and not escaped:
            escaped = True
        else:
            escaped = False
    return delta


def _split_frame_body(body: str, *, paragraph_threshold: int = 900) -> str:
    """Split safe top-level blocks inside one Beamer ``allowframebreaks`` frame.

    Pandoc emits figures and longtables as unbreakable environments. A frame can
    therefore overflow even when it has ``allowframebreaks``. This pass isolates
    those environments and adds breaks only between top-level paragraphs once a
    frame segment is dense enough; it never inserts a break inside a list,
    theorem, equation, figure, or table environment.
    """
    source_lines = body.splitlines(keepends=True)
    output: list[str] = []
    environment_stack: list[str] = []
    segment_length = 0
    segment_has_content = False
    isolate_ended = False
    table_wrapper_open = False
    brace_depth = 0
    tex_group_depth = 0

    for index, line in enumerate(source_lines):
        stripped = line.strip()
        tex_group_delta = sum(1 if match.group("kind") == "begin" else -1 for match in _TEX_GROUP_RE.finditer(stripped))
        events = sorted(
            [
                *(("begin", match) for match in _ENV_BEGIN_RE.finditer(stripped)),
                *(("end", match) for match in _ENV_END_RE.finditer(stripped)),
            ],
            key=lambda event: event[1].start(),
        )

        if not environment_stack and stripped.startswith(r"{\def\LTcaptype"):
            if segment_has_content:
                _append_framebreak(output)
            output.append(line)
            segment_length = 0
            segment_has_content = False
            table_wrapper_open = True
            isolate_ended = False
            continue

        if events:
            for kind, event in events:
                if kind == "begin":
                    name = event.group("name")
                    if (
                        not environment_stack
                        and name in _ISOLATE_SLIDE_ENVS
                        and segment_has_content
                        and not table_wrapper_open
                        and tex_group_depth == 0
                        and tex_group_delta <= 0
                    ):
                        _append_framebreak(output)
                        segment_length = 0
                        segment_has_content = False
                    environment_stack.append(name)
                    isolate_ended = False
                    continue
                if environment_stack and event.group("name") == environment_stack[-1]:
                    ended = environment_stack.pop()
                    if not environment_stack and ended in _ISOLATE_SLIDE_ENVS:
                        isolate_ended = True
                        segment_length = 0
                        segment_has_content = False
            output.append(line)
            tex_group_depth = max(0, tex_group_depth + tex_group_delta)
            continue

        if (
            not environment_stack
            and tex_group_depth == 0
            and stripped
            and isolate_ended
            and not stripped.startswith(r"\end{frame}")
            and not stripped.startswith("}")
        ):
            _append_framebreak(output)
            segment_length = 0
            segment_has_content = False
            isolate_ended = False

        output.append(line)
        if environment_stack:
            segment_length += len(line)
            segment_has_content = True
            continue

        if stripped == r"\framebreak":
            segment_length = 0
            segment_has_content = False
            isolate_ended = False
            continue
        if not environment_stack and table_wrapper_open and stripped == "}":
            table_wrapper_open = False
            isolate_ended = True
            segment_length = 0
            segment_has_content = False
            continue
        if stripped:
            segment_length += len(line)
            segment_has_content = True
            brace_depth += _brace_delta(line)
            tex_group_depth = max(0, tex_group_depth + tex_group_delta)
            next_nonempty = next(
                (candidate.strip() for candidate in source_lines[index + 1 :] if candidate.strip()),
                "",
            )
            safe_line_boundary = (
                brace_depth == 0
                and tex_group_depth == 0
                and bool(next_nonempty)
                and not stripped.endswith((r"\\", "&"))
                and not stripped.startswith((r"\label", r"\caption"))
                and not next_nonempty.startswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ")", "]", ","))
                and not next_nonempty.startswith((r"\end{frame}", "}"))
            )
            if segment_length >= paragraph_threshold and safe_line_boundary:
                _append_framebreak(output)
                segment_length = 0
                segment_has_content = False
                brace_depth = 0
            continue

        next_nonempty = next(
            (candidate.strip() for candidate in source_lines[index + 1 :] if candidate.strip()),
            "",
        )
        if (
            segment_length >= (paragraph_threshold // 2)
            and tex_group_depth == 0
            and next_nonempty
            and not next_nonempty.startswith(r"\end{frame}")
        ):
            _append_framebreak(output)
            segment_length = 0
            segment_has_content = False

    return "".join(output)


def split_long_slide_frames(tex_content: str) -> tuple[str, int]:
    """Split dense generated Beamer frames into independently sized frames."""
    changed = 0

    def replace_frame(match: re.Match[str]) -> str:
        nonlocal changed
        if "allowframebreaks" not in match.group("open"):
            return match.group(0)
        body = match.group("body")
        # Beamer re-typesets allowframebreaks frames multiple times; the
        # listings package's verbatim scanner cannot survive that (\par is
        # injected between passes -> "Paragraph ended before \lst@next").
        # Frames containing verbatim-like environments keep their content in
        # one piece below; additionally strip allowframebreaks so Beamer does
        # not re-typeset the frame.
        has_verbatim = bool(re.search(r"\\begin\{(?:lstlisting|verbatim|lstinputlisting)\}", body))
        updated = _split_frame_body(body)
        if updated != body:
            changed += 1
        segments = updated.split(_FRAMEBREAK_MARKER)
        if len(segments) == 1:
            if has_verbatim and "allowframebreaks" in match.group("open"):
                stripped_open = match.group("open").replace("allowframebreaks", "").replace("[]", "", 1)
                return f"{stripped_open}{updated}{match.group('close')}"
            return f"{match.group('open')}{updated}{match.group('close')}"
        # A split frame's verbatim-bearing segment must not keep
        # allowframebreaks either: Beamer would re-typeset that segment and
        # the listings/verbatim scanner fails across the injected \par again.
        if has_verbatim:

            def _strip_af(segment: str) -> str:
                if re.search(r"\\begin\{(?:lstlisting|verbatim|lstinputlisting)\}", segment):
                    stripped_open = match.group("open").replace("allowframebreaks", "").replace("[]", "", 1)
                    return f"{stripped_open}{segment}{match.group('close')}"
                return f"{match.group('open')}{segment}{match.group('close')}"

            return "\n\n".join(_strip_af(segment) for segment in segments)
        return "\n\n".join(f"{match.group('open')}{segment}{match.group('close')}" for segment in segments)

    return _FRAME_RE.sub(replace_frame, tex_content), changed


__all__ = ["split_long_slide_frames"]
