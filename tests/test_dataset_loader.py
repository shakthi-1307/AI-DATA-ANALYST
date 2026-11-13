from evaluations.dataset_loader import (
    load_golden_dataset,
    validate_dataset
)

def test_dataset_loads():
    dataset = load_golden_dataset()
    assert len(dataset) == 4 
    
def test_dataset_is_valid():
    dataset = load_golden_dataset()
    assert validate_dataset(dataset) is True 
    
def test_dataset_ids_are_unique():
    dataset = load_golden_dataset()
    ids = [case["id"] for case in dataset]
    assert len(ids) == len(set(ids))