"""Deterministic, read-only Python source observations at a pinned Git commit.

No execution of repository code. Results are candidates, not change recommendations.
"""
from __future__ import annotations
import ast
import hashlib
from collections import defaultdict


def module_for(path):
    if not path.endswith('.py'):
        return None
    parts = path.removesuffix('.py').split('/')
    if parts[0] == 'src':
        parts = parts[1:]
    if parts[-1] == '__init__':
        parts.pop()
    return '.'.join(parts) if parts else None


def _strong_components(graph):
    """Tarjan SCC, with stable ordering and no recursion over source text."""
    index = 0
    indices, low, stack, present, components = {}, {}, [], set(), []
    def visit(node):
        nonlocal index
        indices[node] = low[node] = index
        index += 1
        stack.append(node)
        present.add(node)
        for next_node in sorted(graph.get(node, ())):
            if next_node not in indices:
                visit(next_node)
                low[node] = min(low[node], low[next_node])
            elif next_node in present:
                low[node] = min(low[node], indices[next_node])
        if low[node] == indices[node]:
            group = []
            while True:
                v = stack.pop()
                present.remove(v)
                group.append(v)
                if v == node:
                    break
            if len(group) > 1 or node in graph.get(node, ()):
                components.append(sorted(group))
    for node in sorted(graph):
        if node not in indices:
            visit(node)
    return sorted(components)


def _imports(tree, module, is_package, known):
    links = set()
    bases = module.split('.') if is_package else module.split('.')[:-1]
    for item in ast.walk(tree):
        if isinstance(item, ast.Import):
            for alias in item.names:
                target = alias.name
                if target in known:
                    links.add(target)
                # `import package.submodule`: package may be the actual module.
        elif isinstance(item, ast.ImportFrom):
            prefix = bases[:max(0, len(bases) - (item.level - 1))] if item.level else []
            target = '.'.join(prefix + ([item.module] if item.module else []))
            candidates = [target] + [target + '.' + a.name for a in item.names]
            for candidate in candidates:
                if candidate in known:
                    links.add(candidate)
    return links


def _complexity(node):
    branches = (ast.If, ast.IfExp, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler,
                ast.With, ast.AsyncWith, ast.Assert, ast.Match, ast.comprehension)
    decisions = 0
    def walk(n):
        nonlocal decisions
        for child in ast.iter_child_nodes(n):
            # Nested definitions are separate units, not decisions of the parent.
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            if isinstance(child, branches):
                decisions += 1
                if isinstance(child, ast.Match):
                    decisions += max(0, len(child.cases) - 1)
            if isinstance(child, ast.BoolOp):
                decisions += max(0, len(child.values) - 1)
            walk(child)
    walk(node)
    return 1 + decisions


def analyze_python(paths, read_file, commit, max_files=2500):
    """Analyze code as committed in HEAD; `read_file(path)` returns str.

    Relative-import mapping is best-effort. Missing edges must never be treated
    as proof of no dependencies.
    """
    py_paths = sorted(p for p in paths if p.endswith('.py'))[:max_files]
    modules = {module_for(p): p for p in py_paths if module_for(p)}
    parsed, errors = {}, []
    for path in py_paths:
        try:
            source = read_file(path)
            if len(source) > 300_000:
                errors.append({'path':path,'reason':'too large'})
                continue
            parsed[path] = ast.parse(source, filename=path)
        except (SyntaxError, UnicodeError, ValueError, OSError) as exc:
            errors.append({'path':path,'reason':type(exc).__name__})
    graph = defaultdict(set)
    complexity = []
    # Conservative name inventory across parsed sources: avoid advertising
    # private functions as unused when another module imports or mentions them.
    referenced = set()
    dynamic_introspection = False
    for tree in parsed.values():
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                referenced.add(node.id)
            elif isinstance(node, ast.Attribute):
                referenced.add(node.attr)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                referenced.update(alias.name.split('.')[-1] for alias in node.names)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('getattr', 'globals', 'locals', 'eval', 'exec'):
                dynamic_introspection = True
    # If scan is incomplete or introspection is present, do not claim unused
    # names based on absence of references: the false-positive risk is high.
    unused = []
    safe_unused_scan = not errors and len(py_paths) == sum(x.endswith('.py') for x in paths) and not dynamic_introspection

    for module,path in sorted(modules.items()):
        if path not in parsed:
            continue
        tree = parsed[path]
        graph[module].update(_imports(tree,module,path.endswith('/__init__.py'),modules))
        if safe_unused_scan and not path.endswith('/__init__.py') and not path.startswith(('tests/', 'test/')) and '/tests/' not in path:
            for obj in tree.body:
                if not isinstance(obj, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if not obj.name.startswith('_') or obj.name.startswith('__') or obj.name in referenced or obj.decorator_list:
                    continue
                identity = hashlib.sha256((commit+'\0unused\0'+path+'\0'+str(obj.lineno)).encode()).hexdigest()[:16]
                unused.append({'id':identity, 'type':'unused', 'title':obj.name, 'file':path,
                               'line':obj.lineno, 'endLine':obj.end_lineno or obj.lineno,
                               'method':'Conservative AST search for unreferenced private module-level Python functions',
                               'limitations':['Unreferenced in scanned static syntax is not proof of unused code',
                                              'Dynamic imports, plugins, reflection, configuration and external callers may reference this function',
                                              'Manual review required; do not delete automatically']})
        for obj in ast.walk(tree):
            if not isinstance(obj, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            # Functions inside nested structures still have useful locations;
            # qualified names are not inferred from AST parentage.
            score = _complexity(obj)
            length = max(1, (obj.end_lineno or obj.lineno) - obj.lineno + 1)
            if score < 12 and length < 100:
                continue
            identity = hashlib.sha256((commit+'\0complexity\0'+path+'\0'+str(obj.lineno)).encode()).hexdigest()[:16]
            complexity.append({'id':identity,'type':'complexity','title':obj.name,
                               'file':path,'line':obj.lineno,'endLine':obj.end_lineno or obj.lineno,
                               'cyclomaticApprox':score,'lines':length,
                               'method':'AST structural heuristic (not Radon-compatible cyclomatic complexity)',
                               'limitations':['High metrics alone do not justify refactoring',
                                              'AST heuristics do not measure runtime behavior or test adequacy']})
    complexity.sort(key=lambda x:(-x['cyclomaticApprox'],-x['lines'],x['file'],x['line']))
    unused.sort(key=lambda x:(x['file'], x['line']))
    cycles = []
    for group in _strong_components(graph):
        cycle_edges = [{'from':a,'to':b} for a in group for b in sorted(graph.get(a, ())) if b in group]
        paths_in_group = sorted({modules[m] for m in group})
        identity = hashlib.sha256((commit+'\0cycle\0'+'\0'.join(group)).encode()).hexdigest()[:16]
        cycles.append({'id':identity,'type':'cycle','title':' ↔ '.join(group[:3]),
                       'modules':group,'files':paths_in_group,'edges':cycle_edges,
                       'method':'Python AST import graph; strongly connected component',
                       'limitations':['Static imports may not represent runtime dependency direction',
                                      'Dynamic imports and external consumers are not included']})
    return {'commit':commit,'pythonFilesScanned':len(parsed),'pythonFilesAvailable':len(py_paths),
            'truncated':sum(p.endswith('.py') for p in paths)>max_files,
            'parseErrors':errors[:40],'cycles':cycles,'complexity':complexity[:600],
            'unused':unused[:300], 'unusedScanEligible':safe_unused_scan,
            'counts':{'cycles':len(cycles),'complexity':len(complexity),'unused':len(unused)},
            'limitations':['Python-only static analysis; other languages not scanned',
                           'Imported names may be resolved incompletely',
                           'Complexity is an approximate ranking metric, not a defect claim',
                           'Unused candidates only include undecorated private module-level functions; absence of a finding is not proof of usage']}


def _cycle_import_locations(finding, read_file):
    """Find AST import statements supporting each *reported* static edge.

    A strongly connected component is not necessarily a single simple loop. We
    therefore report every indexed edge and its actual source location.
    """
    mapped = {module_for(path): path for path in finding.get('files', [])}
    result = []
    trees = {}
    for edge in finding.get('edges', []):
        src, target = edge.get('from'), edge.get('to')
        path = mapped.get(src)
        item = {'from': src, 'to': target, 'path': path, 'locations': []}
        if path:
            try:
                if path not in trees:
                    trees[path] = ast.parse(read_file(path), filename=path)
                tree = trees[path]
                for node in ast.walk(tree):
                    if not isinstance(node, (ast.Import, ast.ImportFrom)):
                        continue
                    # Apply the same resolution rules as the analyzer, but to
                    # the individual import statement rather than the whole file.
                    single = ast.Module(body=[node], type_ignores=[])
                    if target in _imports(single, src, path.endswith('/__init__.py'), mapped):
                        item['locations'].append({'line': node.lineno,
                                                  'endLine': getattr(node, 'end_lineno', node.lineno)})
            except (SyntaxError, OSError, ValueError, UnicodeError) as exc:
                item['error'] = type(exc).__name__
        result.append(item)
    return result


def _excerpt(lines, first, last, margin, limit, budget):
    """Create a line-aligned excerpt without splitting a source line midway."""
    start = max(1, first - margin)
    end = min(len(lines), last + margin, start + limit - 1)
    collected = []
    size = 0
    for lineno in range(start, end + 1):
        chunk = f'{lineno:5d} {lines[lineno-1]}'
        if size + len(chunk) + 1 > budget:
            break
        collected.append(chunk)
        size += len(chunk) + 1
    return start, start + len(collected) - 1, '\n'.join(collected), len(collected) < (end - start + 1)


def export_evidence(finding, kind, commit, read_file, level='balanced', repository='repository'):
    """Build focused source evidence. The result is NEVER a safety verdict.

    In a cycle, edge-bearing imports take priority over arbitrary file starts.
    All reported edges are included in the location inventory even when source
    content cannot be retrieved under the selected budget.
    """
    if level not in ('compact', 'balanced', 'extended'):
        raise ValueError('Invalid evidence size')
    import json
    context = {'compact': 1, 'balanced': 4, 'extended': 12}[level]
    max_chars = {'compact': 6500, 'balanced': 18000, 'extended': 36000}[level]
    per_excerpt = {'compact': 18, 'balanced': 45, 'extended': 110}[level]
    positions = []
    edge_locations = []
    if kind == 'duplication':
        matches = finding['matches'][:{'compact': 1, 'balanced': 2, 'extended': 4}[level]]
        for match in matches:
            positions += [(finding['first'], match['firstLine'], match['lines'], 'duplication match A'),
                          (finding['second'], match['secondLine'], match['lines'], 'duplication match B')]
    elif kind == 'cycle':
        edge_locations = _cycle_import_locations(finding, read_file)
        for edge in edge_locations:
            for loc in edge['locations']:
                positions.append((edge['path'], loc['line'], loc['endLine'] - loc['line'] + 1,
                                  f"import edge: {edge['from']} → {edge['to']}"))
    elif kind in ('complexity', 'unused'):
        positions.append((finding['file'], finding['line'], finding['endLine'] - finding['line'] + 1,
                          'complexity candidate function' if kind == 'complexity' else 'potentially unreferenced private function'))
    else:
        raise ValueError('Unsupported finding type')

    observations = []
    remaining = max_chars
    missing = []
    # Allocate at least a minimal excerpt for each position; don't let the
    # first long function or import consume all other evidence.
    for idx, (path, line, count, reason) in enumerate(positions):
        if not isinstance(line, int) or not isinstance(count, int) or line < 1 or count < 1:
            missing.append({'path': path, 'reason': reason, 'problem': 'Invalid source range'})
            continue
        quota = min(remaining, max(0, remaining // (len(positions) - idx)))
        try:
            source = read_file(path)
            lines = source.splitlines()
            if line > len(lines):
                raise ValueError('Line not found')
            first, last, snippet, clipped = _excerpt(lines, line, line + count - 1,
                                                      context, max(per_excerpt, count), quota)
            if not snippet:
                missing.append({'path': path, 'reason': reason, 'problem': 'Insufficient context budget'})
                continue
            # The import statement itself or the start of the matched range
            # must be visible; otherwise mark the excerpt incomplete.
            includes_target = first <= line <= last and last >= min(len(lines), line + count - 1)
            observations.append({'path': path, 'firstLine': first, 'lastLine': last,
                                 'reason': reason, 'targetLine': line,
                                 'targetEndLine': line + count - 1,
                                 'targetFullyIncluded': includes_target,
                                 'truncated': clipped or not includes_target,
                                 'uncoveredTargetRanges': ([[last + 1, min(len(lines), line + count - 1)]] if last < line + count - 1 else []),
                                 'sourceSha256': hashlib.sha256(source.encode('utf-8')).hexdigest(),
                                 'snippet': snippet})
            remaining -= len(snippet) + 1
        except (ValueError, OSError, UnicodeError) as exc:
            missing.append({'path': path, 'reason': reason, 'problem': type(exc).__name__})
    if kind == 'cycle':
        for edge in edge_locations:
            if not edge['locations']:
                missing.append({'path': edge['path'],
                                'reason': f"import edge: {edge['from']} → {edge['to']}",
                                'problem': edge.get('error', 'Exact import statement not located')})
    # These fields describe evidence coverage only, never semantic certainty.
    targets_included = sum(bool(o['targetFullyIncluded']) for o in observations)
    edge_count = len(edge_locations) if kind == 'cycle' else None
    edges_with_imports = sum(bool(edge['locations']) for edge in edge_locations) if kind == 'cycle' else None
    edges_with_complete_snippets = (sum(any(o['reason'] == f"import edge: {edge['from']} → {edge['to']}" and o['targetFullyIncluded'] for o in observations) for edge in edge_locations) if kind == 'cycle' else None)
    evidence_coverage = {'requestedAnchors': len(positions),
                         'completeAnchors': targets_included,
                         'missingOrPartialAnchors': len(positions) - targets_included,
                         'missingEvidenceItems': len(missing),
                         'partialTargetRanges': [{'path': o['path'], 'ranges': o['uncoveredTargetRanges']} for o in observations if o['uncoveredTargetRanges']]}
    if kind == 'cycle':
        evidence_coverage.update({'reportedEdges': edge_count,
                                  'edgesWithLocatedImports': edges_with_imports,
                                  'edgesWithCompleteSource': edges_with_complete_snippets})
    evidence_coverage['anchorsComplete'] = bool(positions) and targets_included == len(positions) and not missing and (kind != 'cycle' or edges_with_complete_snippets == edge_count)
    caution = [
        'Source may contain private information or credentials; review before external sharing.',
        'Static results cannot establish that a refactor is safe or that references are complete.',
        'No source execution, edits, or tests were performed by this exporter.',
        'Additional callers, tests, dynamic imports and behavioral effects may be missing.',
    ]
    payload = {'schemaVersion': 2, 'repoName': repository, 'repoCommit': commit,
               'findingType': kind, 'finding': finding, 'evidenceLevel': level,
               'edgeLocations': edge_locations, 'snippets': observations,
               'missingEvidence': missing, 'evidenceCoverage': evidence_coverage, 'cautions': caution,
               'contextIsComplete': False}
    title = {'duplication': 'Duplicate implementation', 'cycle': 'Import dependency cycle',
             'complexity': 'Complex function candidate',
             'unused': 'Potentially unreferenced private function'}[kind]
    content = ['# Repo Studio — AI investigation package', '',
               f'**Repository:** `{repository}`', f'**Category:** {title}',
               f'**Finding ID:** `{finding["id"]}`', f'**Commit:** `{commit}`',
               f'**Context:** {level}', '', '## Observations (tool-derived, not conclusions)',
               '```json', json.dumps(finding, indent=2, ensure_ascii=False), '```']
    if kind == 'cycle':
        content += ['', '## Reported cycle edges and located imports']
        for edge in edge_locations:
            where = ', '.join(str(x['line']) + (('-' + str(x['endLine'])) if x['endLine'] != x['line'] else '')
                              for x in edge['locations']) or 'NOT LOCATED'
            content.append(f"- `{edge['from']}` → `{edge['to']}`: `{edge['path']}` lines {where}")
        content += ['', 'These are static AST imports; conditional and deferred imports may not create runtime cycles.']
    content += ['', '## Evidence coverage (not a correctness verdict)',
                f"- Anchors with complete source: {evidence_coverage['completeAnchors']}/{evidence_coverage['requestedAnchors']}",
                f"- Missing evidence entries: {evidence_coverage['missingEvidenceItems']}"]
    if kind == 'cycle':
        content.append(f"- Reported import edges with complete source: {edges_with_complete_snippets}/{edge_count}")
    if not evidence_coverage['anchorsComplete']:
        content.append('**Partial evidence:** an anchor can be located but still have omitted source lines. Zero missingEvidence entries does not imply complete source.')
        for gap in evidence_coverage['partialTargetRanges']:
            for first_missing, last_missing in gap['ranges']:
                content.append(f"- Missing target source: `{gap['path']}` lines {first_missing}-{last_missing}. Request those exact lines before concluding.")
    content += ['', '## Source evidence (committed source at the commit above)']
    for o in observations:
        content += ['', f"### `{o['path']}` — {o['reason']} (target {o['targetLine']}-{o['targetEndLine']})",
                    '```text', o['snippet'], '```']
        if o['truncated']:
            content.append('**Partial excerpt:** the target range or requested context was not fully included.')
    if missing:
        content += ['', '## Evidence not supplied']
        for entry in missing:
            content.append(f"- `{entry['path']}` ({entry['reason']}): {entry['problem']}")
    content += ['', '## Uncertainties and handling', ''] + ['- ' + x for x in caution]
    content += ['', '## Investigation request',
                'Decide whether this finding warrants no change, more investigation, or a minimal proposed change.',
                'Verify the cited source evidence, inspect callers and tests as necessary, and distinguish facts from hypotheses.',
                'For import cycles, assess whether imports occur at module load time or inside deferred/conditional paths.',
                'Explain missing evidence and request precise additional files/line ranges if needed.',
                'Do not modify repository files. Do not claim a change is safe.']
    markdown = '\n'.join(content) + '\n'
    return {'markdown': markdown, 'json': payload,
            'estimatedTokens': (len(markdown)+3)//4,
            'estimateMethod': 'characters / 4 (rough approximation, not tokenizer)',
            'truncated': not evidence_coverage['anchorsComplete'] or any(x['truncated'] for x in observations),
            'fileStem': _export_stem(repository, kind, finding['id'], level)}


def _export_stem(repository, kind, finding_id, level):
    """Safe, informative, stable filename stem across Markdown and JSON."""
    import re
    def slug(text, fallback):
        value = re.sub(r'[^a-z0-9]+', '-', str(text).lower()).strip('-')[:48].strip('-')
        return value or fallback
    type_name = {'cycle': 'import-cycle', 'complexity': 'complexity',
                 'duplication': 'duplication', 'unused': 'unused-candidate'}[kind]
    return f'repo-studio-{slug(repository, "repository")}-{type_name}-{slug(finding_id, "unknown")[:16]}-{level}'
