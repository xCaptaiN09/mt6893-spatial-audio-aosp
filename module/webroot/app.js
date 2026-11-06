'use strict';
// KernelSU's public exec callback bridge. No external runtime dependencies.
const byId = id => document.getElementById(id);
const actions = new Set(['status','on','off','report','demo','settings']);
let pending = false, state = null, serial = 0;

function nativeExec(action) {
  if (!actions.has(action)) return Promise.reject(new Error('Unknown operation'));
  if (!window.ksu || typeof window.ksu.exec !== 'function') {
    return Promise.reject(new Error('Open this page from the module WebUI in a compatible root manager.'));
  }
  return new Promise((resolve, reject) => {
    const name = `spatial_result_${Date.now()}_${serial++}`;
    const timer = setTimeout(() => {
      delete window[name]; reject(new Error('The audio operation timed out. Save a diagnostic report.'));
    }, action === 'status' ? 20000 : 90000);
    window[name] = (errno, stdout, stderr) => {
      clearTimeout(timer); delete window[name];
      resolve({code:Number(errno),out:String(stdout || ''),err:String(stderr || '')});
    };
    try { window.ksu.exec(`sh /data/adb/modules/mt6893-spatial-aosp/control.sh ${action}`, '{}', name); }
    catch (error) {clearTimeout(timer);delete window[name];reject(error);}
  });
}
function decodeState(text) {
  const line = text.split(/\r?\n/).find(l => l.trim().startsWith('{'));
  if (!line) throw new Error('Android did not return an audio status. Save a diagnostic report.');
  const parsed = JSON.parse(line);
  if (parsed.error) throw new Error(parsed.error);
  if (typeof parsed.enabled !== 'boolean' || typeof parsed.available !== 'boolean' || typeof parsed.level !== 'number' || typeof parsed.mounted !== 'boolean')
    throw new Error('Incomplete audio status. Save a diagnostic report.');
  return parsed;
}
function feedback(message, error = false) {
  byId('feedback').hidden = !message;
  byId('feedback').classList.toggle('error', error);
  byId('feedback').textContent = message;
}
function buttons() {
  const capable = state && state.mounted === true && state.level > 0;
  byId('original').disabled = pending || !capable;
  byId('spatial').disabled = pending || !capable;
  byId('demo').disabled = pending || !capable || !state.enabled || !state.available;
  for (const id of ['report','settings','refresh']) byId(id).disabled = pending;
  document.body.classList.toggle('busy', pending);
}
function paint(next) {
  state = next;
  byId('device').textContent = next.device || 'No headphone information';
  byId('dot').classList.toggle('ready',next.available);
  byId('original').setAttribute('aria-pressed',String(next.mounted && !next.enabled));
  byId('spatial').setAttribute('aria-pressed',String(next.mounted && next.enabled));
  byId('stage').classList.toggle('enabled',next.mounted && next.enabled && next.available && next.level > 0);
  byId('tracking-copy').textContent = next.headTrackerAvailable ? 'Tracking controls are not included in this preview.' : 'Requires compatible tracking hardware.';
  if (!next.mounted) {
    byId('status').textContent = 'Audio files not mounted';
    byId('stage-copy').textContent = 'Headphones can be detected while the spatial engine is unavailable.';
  } else if (next.level === 0) {
    byId('status').textContent = 'Audio engine unavailable';
    byId('stage-copy').textContent = 'Reboot after installation. If this remains, save a diagnostic report.';
  } else if (!next.enabled) {
    byId('status').textContent = 'Original audio';
    byId('stage-copy').textContent = 'Spatial processing is turned off.';
  } else if (!next.available) {
    byId('status').textContent = 'Enabled · waiting for headphones';
    byId('stage-copy').textContent = 'Connect supported wired or USB headphones.';
  } else {
    byId('status').textContent = 'Enabled · available';
    byId('stage-copy').textContent = 'Ready for compatible audio. Multichannel input up to 7.1.4.';
  }
  buttons();
}
function failure(error) {
  state = null;
  byId('stage').classList.remove('enabled');
  byId('dot').classList.remove('ready');
  byId('status').textContent = 'Status unavailable';
  byId('stage-copy').textContent = 'The audio state could not be verified.';
  byId('device').textContent = 'Connection not verified';
  for (const id of ['original','spatial']) byId(id).setAttribute('aria-pressed','false');
  feedback(error.message,true);
}
async function perform(action) {
  if (pending) return;
  pending = true; buttons();
  if (action === 'demo') feedback('Playing the 24-second channel sequence. Keep media volume low.');
  try {
    const result = await nativeExec(action);
    if (['status','on','off'].includes(action)) {
      const next = decodeState(result.out);
      if (result.code !== 0) throw new Error(result.err || 'The requested state was not confirmed.');
      paint(next);
      if (!next.mounted) feedback('Audio files are not mounted. Reinstall this preview with Magic Mount active, then reboot and save a report.',true);
      else feedback(action === 'status' ? '' : next.enabled ? 'Spatial Audio enabled.' : 'Original audio selected.');
    } else {
      if (result.code !== 0) throw new Error(result.out || result.err || 'Operation failed. Save a diagnostic report.');
      feedback(action === 'settings' ? '' : result.out.trim());
    }
  } catch (error) {
    if (['status','on','off'].includes(action)) failure(error);
    else feedback(error.message,true);
  } finally { pending = false; buttons(); }
}
byId('original').addEventListener('click',() => perform('off'));
byId('spatial').addEventListener('click',() => perform('on'));
byId('refresh').addEventListener('click',() => perform('status'));
byId('report').addEventListener('click',() => perform('report'));
byId('settings').addEventListener('click',() => perform('settings'));
byId('demo').addEventListener('click',() => perform('demo'));
document.addEventListener('visibilitychange',() => {
  document.body.classList.toggle('inactive',document.hidden);
  if (!document.hidden && !pending) perform('status');
});
perform('status');
