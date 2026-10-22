export function createSelection(initialScope = 'all') {
  let currentScope = initialScope;
  const values = new Set();
  const valid = id => Number.isSafeInteger(Number(id)) && Number(id) > 0;
  const store = {
    ids: () => [...values], size: () => values.size, scope: () => currentScope,
    has: id => values.has(Number(id)),
    toggle(id, checked) { if (valid(id)) checked ? values.add(Number(id)) : values.delete(Number(id)); },
    clear() { values.clear(); },
    setScope(next, force = false) {
      if (next === currentScope) return true;
      if (values.size && !force) return false;
      values.clear(); currentScope = next; return true;
    },
    selectRange(orderedIds, start, end, checked) {
      const a = orderedIds.indexOf(Number(start));
      const b = orderedIds.indexOf(Number(end));
      if (a < 0 || b < 0) return;
      orderedIds.slice(Math.min(a, b), Math.max(a, b) + 1).forEach(id => store.toggle(id, checked));
    },
  };
  return store;
}
