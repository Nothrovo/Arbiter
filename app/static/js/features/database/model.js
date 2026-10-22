import {esc, formatTime} from '../../ui/primitives.js';

export function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

export function summarizeTelemetryRange(earliest, latest) {
  if (!earliest && !latest) return 'Belum ada telemetri tercatat';
  if (!earliest) return `Hingga ${formatTime(latest)}`;
  if (!latest) return `Mulai ${formatTime(earliest)}`;
  return `${formatTime(earliest)} — ${formatTime(latest)}`;
}
