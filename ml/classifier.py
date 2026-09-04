from __future__ import annotations
from abc import ABC,abstractmethod
from dataclasses import dataclass
import numpy as np
@dataclass(frozen=True)
class TopPrediction: label: str; score: float; index: int
@dataclass(frozen=True)
class ClassificationResult:
    bark_score: float
    top_predictions: tuple[TopPrediction,...]
    frame_scores: np.ndarray
    embeddings: np.ndarray
    latency_ms: float
    dog_scores: dict[str,float] | None = None
class AudioClassifier(ABC):
    sample_rate=16000
    @abstractmethod
    def classify(self,waveform: np.ndarray,top_k:int=5)->ClassificationResult: ...
