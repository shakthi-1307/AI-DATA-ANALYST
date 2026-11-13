import json 
from pathlib import Path 

DATASET_PATH = (
    Path(__file__).parent
    / "datasets"
    / "golden_questions.json"
)

def load_golden_dataset():
    with open(DATASET_PATH,"r",encoding="utf-8") as file:
        dataset = json.load(file)
        
    return dataset

def validate_dataset(dataset):
    required_fields = {
        "id",
        "question",
        "expected_metric",
        "expected_tables",
        "metric_definition"
    }
    
    seen_ids = set()
    
    for case in dataset:
        missing = required_fields - case.keys()
        
        if missing:
            raise ValueError(
                f"Missing fields in {case.get('id','unknown')} : {missing}"
            )
            
        if case["id"] in seen_ids:
            raise ValueError(f"Duplicate evaluation ID: {case['id']}")
        
        seen_ids.add(case["id"])
        
    return True