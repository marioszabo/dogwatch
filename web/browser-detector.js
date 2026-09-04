const dogwatchBrowserDetector=(()=>{
  const WINDOW_SIZE=15360,HOP_SIZE=7680;
  const DOG_CLASSES=[67,68,69,70,71,72,73,74,75,117];
  const SPECIFIC=[69,70,71,72,73,74,75,117];
  const GENERAL=[67,68];
  let model,audioContext,stream,source,processor,running=false;
  let windowBuffer=new Float32Array(WINDOW_SIZE),windowPosition=0,predictionBuffer=[],lastDetection=0;
  let sensitivity=.3,specificFloor=.01,debounce=4;
  function setText(text){const el=document.querySelector('#browser-detector');if(el)el.textContent=text}
  function resampleAudio(input,fromRate,toRate){
    const ratio=toRate/fromRate,out=new Float32Array(Math.floor(input.length*ratio));
    for(let i=0;i<out.length;i++){const index=i/ratio,low=Math.floor(index),high=Math.min(low+1,input.length-1),w=index-low;out[i]=input[low]*(1-w)+input[high]*w}
    return out;
  }
  function normalize(input){
    let mean=0;for(const v of input)mean+=v;mean/=input.length;
    const out=new Float32Array(input.length);let peak=0;
    for(let i=0;i<input.length;i++){const v=input[i]-mean;out[i]=v;peak=Math.max(peak,Math.abs(v))}
    if(peak>0){for(let i=0;i<out.length;i++)out[i]/=peak}
    return out;
  }
  async function loadModel(){
    if(model)return;
    if(tf.setWasmPaths)tf.setWasmPaths('/static/libs/');
    await tf.setBackend('wasm');await tf.ready();
    model=await yamnet.load('/static/model/');
  }
  async function postScore(url,score,dogScores,topPredictions){
    await fetch(url,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({score,dog_scores:dogScores,top_predictions:topPredictions})});
  }
  async function processWindow(input){
    const tensor=tf.tensor(normalize(input),[WINDOW_SIZE],'float32');
    const predictions=await model.predict(tensor);
    const scores=await predictions.data();
    tensor.dispose();predictions.dispose();
    predictionBuffer.push(scores);
    if(predictionBuffer.length<2)return;
    const combined=new Float32Array(scores.length);
    for(let i=0;i<combined.length;i++)combined[i]=(predictionBuffer[0][i]+predictionBuffer[1][i])/2;
    predictionBuffer=[];
    const top=Array.from(combined).map((score,index)=>({label:model.classNames[index]||`Class ${index}`,score,index})).sort((a,b)=>b.score-a.score).slice(0,10);
    const dogScores={};
    for(const i of DOG_CLASSES)if(combined[i]>.01)dogScores[model.classNames[i]||`Class ${i}`]=combined[i];
    const anyDog=Math.max(...DOG_CLASSES.map(i=>combined[i]||0));
    const specific=Math.max(...SPECIFIC.map(i=>combined[i]||0));
    const general=Math.max(...GENERAL.map(i=>combined[i]||0));
    const shouldDetect=specific>specificFloor&&(anyDog>=sensitivity||general>=sensitivity);
    if(shouldDetect){
      const now=Date.now()/1000;
      if(now-lastDetection>=debounce){lastDetection=now;await postScore('/api/browser-detection',anyDog,dogScores,top)}
      setText(`Browser YAMNet: detected dog sound ${anyDog.toFixed(3)}`);
    }else{
      await postScore('/api/browser-preview',anyDog,dogScores,top);
      setText(`Browser YAMNet: listening, dog score ${anyDog.toFixed(3)}`);
    }
  }
  function processChunk(chunk,sampleRate){
    const audio=sampleRate===16000?chunk:resampleAudio(chunk,sampleRate,16000);
    for(let i=0;i<audio.length;i++){
      if(windowPosition<WINDOW_SIZE){windowBuffer[windowPosition++]=audio[i];continue}
      windowBuffer.copyWithin(0,HOP_SIZE);windowPosition=WINDOW_SIZE-HOP_SIZE;windowBuffer[windowPosition++]=audio[i];
      processWindow(windowBuffer.slice()).catch(err=>setText(`Browser YAMNet error: ${err.message}`));
    }
  }
  async function start(config){
    if(running)return;
    sensitivity=Number(config.bark_on_threshold??.3);specificFloor=Number(config.dog_specific_floor??.01);debounce=Number(config.website_detection_debounce_s??4);
    setText('Browser YAMNet: loading model...');
    await loadModel();
    stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:false,noiseSuppression:false,autoGainControl:true,channelCount:1,sampleRate:{ideal:16000}}});
    audioContext=new (window.AudioContext||window.webkitAudioContext)();
    source=audioContext.createMediaStreamSource(stream);
    await audioContext.audioWorklet.addModule('/static/audio-processor.js');
    processor=new AudioWorkletNode(audioContext,'audio-processor');
    source.connect(processor);processor.connect(audioContext.destination);
    processor.port.onmessage=(event)=>{if(event.data.type==='audioData'&&running)processChunk(event.data.data,audioContext.sampleRate)};
    running=true;windowBuffer=new Float32Array(WINDOW_SIZE);windowPosition=0;predictionBuffer=[];lastDetection=0;
    setText('Browser YAMNet: listening');
  }
  async function stop(){
    running=false;
    if(processor)processor.disconnect();
    if(source)source.disconnect();
    if(stream)stream.getTracks().forEach(t=>t.stop());
    if(audioContext)await audioContext.close();
    processor=source=stream=audioContext=null;
    setText('Browser YAMNet: stopped');
  }
  return{start,stop};
})();
