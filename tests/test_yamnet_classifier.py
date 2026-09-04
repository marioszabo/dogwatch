from ml.yamnet_classifier import DOG_CONTEXT_LABELS,DOG_VOCALIZATION_LABELS,label_indices


def test_dog_labels_include_vocalizations_and_context():
    labels=["Speech","Dog","Bark","Whimper (dog)","Vehicle","Domestic animals, pets","Growling","Animal"]
    vocalizations=label_indices(labels,DOG_VOCALIZATION_LABELS)
    context=label_indices(labels,DOG_CONTEXT_LABELS)
    assert vocalizations==[2,3,6]
    assert context==[1,5,7]
