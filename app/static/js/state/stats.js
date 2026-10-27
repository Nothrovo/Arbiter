export function createStatsSession() {
  let version = 0;
  let disposed = false;
  return {
    nextRequest() {
      return ++version;
    },
    isCurrent(v) {
      return !disposed && v === version;
    },
    dispose() {
      disposed = true;
      version++;
    },
  };
}
