const form=document.querySelector('#config');
const msg=document.querySelector('#message');
let cfg={};

const labels={
  enabled:'Enabled',
  inference_runtime:'Detector Runtime',
  quiet_start:'Quiet Start',
  quiet_end:'Quiet End',
  bark_on_threshold:'Sensitivity',
  bark_off_threshold:'Release Sensitivity',
  min_event_duration_s:'Minimum Bark Length',
  release_duration_s:'Release Time',
  min_event_gap_s:'Minimum Gap',
  rolling_window_s:'Bark Window',
  required_barks:'Required Barks',
  post_playback_suppression_s:'After Playback Pause',
  cooldown_s:'Cooldown',
  response_path:'Response File',
  rms_gate_dbfs:'Noise Gate',
  acoustic_detector_enabled:'Acoustic Backup',
  yamnet_peak_normalize:'Normalize Audio',
  yamnet_peak_normalize_min_dbfs:'Normalize Above',
  dog_specific_floor:'Dog Class Floor',
  website_detection_debounce_s:'Detection Debounce'
};

async function json(url,options){
  const r=await fetch(url,options);
  const data=await r.json();
  if(!r.ok)throw Error(data.detail||r.statusText);
  return data;
}

function render(c){
  cfg=c;
  form.innerHTML='';
  for(const [k,v] of Object.entries(c)){
    const label=document.createElement('label');
    const name=document.createElement('span');
    name.textContent=labels[k]||k;
    const input=document.createElement('input');
    input.name=k;
    if(typeof v==='boolean'){
      input.type='checkbox';
      input.checked=v;
    }else{
      input.value=v??'';
      input.dataset.type=typeof v;
    }
    label.append(name,input);
    form.append(label);
  }
}

async function status(){
  try{
    const s=await json('/api/status');
    const state=s.state||'LISTENING';
    const barks=`${s.bark_count||0} / ${(cfg.required_barks||5)}`;
    const dbfs=typeof s.last_dbfs==='number'?`${s.last_dbfs.toFixed(1)} dBFS`:'Waiting';
    document.querySelector('#state-pill').textContent=state.replaceAll('_',' ');
    document.querySelector('#state-pill').dataset.state=state;
    document.querySelector('#bark-count').textContent=barks;
    document.querySelector('#quiet-state').textContent=s.quiet_active?'Active':'Inactive';
    document.querySelector('#audio-level').textContent=dbfs;
  }catch(e){
    msg.textContent=e.message;
  }
}

document.querySelector('#test').onclick=()=>json('/api/test-response',{method:'POST'}).then(status).catch(e=>msg.textContent=e.message);
document.querySelector('#browser-start').onclick=async()=>{
  try{
    await dogwatchBrowserDetector.start(cfg);
    document.querySelector('#browser-start').disabled=true;
    document.querySelector('#browser-stop').disabled=false;
    msg.textContent='';
  }catch(e){
    msg.textContent='Browser detector failed: '+e.message;
  }
};
document.querySelector('#browser-stop').onclick=async()=>{
  await dogwatchBrowserDetector.stop();
  document.querySelector('#browser-start').disabled=false;
  document.querySelector('#browser-stop').disabled=true;
};
document.querySelector('#save').onclick=async()=>{
  const out={};
  for(const el of form.elements){
    out[el.name]=el.type==='checkbox'?el.checked:el.value===''?null:el.dataset.type==='number'?Number(el.value):el.value;
  }
  try{
    render(await json('/api/config',{method:'PUT',headers:{'content-type':'application/json'},body:JSON.stringify(out)}));
    msg.textContent='Saved.';
  }catch(e){
    msg.textContent='Not saved: '+e.message;
  }
};

json('/api/config').then(render).then(status).catch(e=>msg.textContent=e.message);
setInterval(status,1000);
