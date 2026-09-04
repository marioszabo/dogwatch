"""YAMNet via TensorFlow Hub; model/class map are cached by TF Hub."""
from __future__ import annotations
import csv, io, logging, time, urllib.request
from collections import deque
import numpy as np
from .classifier import AudioClassifier,ClassificationResult,TopPrediction
MODEL_URL="https://tfhub.dev/google/yamnet/1"
CLASS_MAP_URL="https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv"
DOG_VOCALIZATION_LABELS=("Bark","Yip","Howl","Bow-wow","Growling","Whimper (dog)")
DOG_CONTEXT_LABELS=("Dog","Canidae, dogs, wolves","Domestic animals, pets","Animal")
DOG_CONTEXT_WEIGHT=.75
WEBSITE_DOG_LABELS=("Animal","Domestic animals, pets","Dog","Bark","Yip","Howl","Bow-wow","Growling","Whimper (dog)","Canidae, dogs, wolves")
WEBSITE_SPECIFIC_DOG_LABELS=("Dog","Bark","Yip","Howl","Bow-wow","Growling","Whimper (dog)","Canidae, dogs, wolves")
WEBSITE_GENERAL_DOG_LABELS=("Animal","Domestic animals, pets")
def label_indices(labels,targets):
    wanted=set(targets)
    return [i for i,x in enumerate(labels) if x in wanted]
class YAMNetClassifier(AudioClassifier):
    def __init__(self,model_url:str=MODEL_URL,class_map_path:str|None=None):
        logging.info("tensorflow_hub_import_started")
        import setuptools  # Enables the distutils compatibility shim required by this TensorFlow build on Python 3.12.
        import tensorflow_hub as hub
        logging.info("tensorflow_hub_import_finished")
        start=time.perf_counter()
        self.model=hub.load(model_url); self.labels=self._labels(class_map_path); self.dog_vocalization_indices=label_indices(self.labels,DOG_VOCALIZATION_LABELS); self.dog_context_indices=label_indices(self.labels,DOG_CONTEXT_LABELS); self.dog_indices=self.dog_vocalization_indices+self.dog_context_indices
        logging.info("yamnet_loaded",extra={"detail":f"{time.perf_counter()-start:.2f}s"})
        self.website_dog_indices=label_indices(self.labels,WEBSITE_DOG_LABELS); self.website_specific_indices=label_indices(self.labels,WEBSITE_SPECIFIC_DOG_LABELS); self.website_general_indices=label_indices(self.labels,WEBSITE_GENERAL_DOG_LABELS)
        if not self.dog_vocalization_indices: raise RuntimeError("official AudioSet map contains no recognized dog-bark labels")
        self.latencies=deque(maxlen=1000)
    def _labels(self,path):
        if path: raw=open(path,encoding="utf-8").read()
        else:
            model_map=self.model.class_map_path().numpy().decode() if hasattr(self.model,"class_map_path") else None
            raw=open(model_map,encoding="utf-8").read() if model_map else urllib.request.urlopen(CLASS_MAP_URL,timeout=30).read().decode()
        rows=list(csv.DictReader(io.StringIO(raw)))
        if len(rows)!=521 or "display_name" not in rows[0]: raise RuntimeError(f"invalid AudioSet class map: expected 521 rows, got {len(rows)}")
        return [r["display_name"] for r in rows]
    def classify(self,waveform,top_k=5):
        x=np.asarray(waveform,dtype=np.float32).reshape(-1); start=time.perf_counter(); scores,embeddings,_=self.model(x); frames=np.asarray(scores); latency=(time.perf_counter()-start)*1000; self.latencies.append(latency)
        aggregate=frames.mean(axis=0) if len(frames) else np.zeros(len(self.labels))
        if len(frames):
            bark=float(frames[:,self.dog_vocalization_indices].max())
            context=float(frames[:,self.dog_context_indices].max()) if self.dog_context_indices else 0.0
            bark=max(bark,context*DOG_CONTEXT_WEIGHT)
        else: bark=0.0
        dog_scores={self.labels[i]:float(aggregate[i]) for i in self.website_dog_indices}
        ids=np.argsort(aggregate)[::-1][:top_k]; top=tuple(TopPrediction(self.labels[i],float(aggregate[i]),int(i)) for i in ids)
        return ClassificationResult(bark,top,frames,np.asarray(embeddings),latency,dog_scores)
    def latency_stats(self):
        a=np.asarray(self.latencies); return {"count":len(a),"average_ms":float(a.mean()) if len(a) else 0,"p95_ms":float(np.percentile(a,95)) if len(a) else 0}
