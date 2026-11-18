from evaluations.metrics.result_accuracy import compare_results

def test_exact_numeric_match():
    result = compare_results(
        {"sales":1000.0},
        {"sales":"1000.0"}
    )
    
    assert result["sales"]["passed"] is True
    
def test_numeric_tolerance():
    result = compare_results(
        {"sales":1000.0},
        {"sales":"1000.05"}
    )
    
    assert result["sales"]["passed"] is True
    
def test_categorical_match():
    result = compare_results(
        {"category":"Electronics"},
        {"category":"electronics"}
    )
    
    assert result["category"]["passed"] is True 
    
def test_missing_result():
    result = compare_results(
        {"category":"Electronics"},
        {}
    )
    
    assert result["category"]["passed"] is False