export function createTriageSession() {
  let queueScroll = 0, id = null, detailVersion = 0, disposed = false;
  return {
    rememberQueue(value) { queueScroll = Math.max(0, Number(value) || 0); },
    open(value) { id = Number(value); },
    activeId: () => id,
    close() { id = null; detailVersion++; return queueScroll; },
    nextDetail() { return ++detailVersion; },
    isCurrentDetail: version => !disposed && version === detailVersion,
    dispose() { disposed = true; detailVersion++; },
  };
}
