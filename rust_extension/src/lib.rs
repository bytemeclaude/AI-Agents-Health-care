use pyo3::prelude::*;
use std::collections::HashSet;

/// Rust-accelerated Jaccard Similarity Search for RAG
#[pyfunction]
fn fast_jaccard_search(query: String, documents: Vec<String>) -> Vec<(f64, String)> {
    let query_words: HashSet<String> = query.to_lowercase()
        .split_whitespace()
        .map(|s| s.to_string())
        .collect();

    let mut scores = Vec::new();

    for doc in documents {
        let doc_words: HashSet<String> = doc.to_lowercase()
            .split_whitespace()
            .map(|s| s.to_string())
            .collect();
        
        let intersection_count = query_words.intersection(&doc_words).count();
        let union_count = query_words.union(&doc_words).count();
        
        let score = if union_count == 0 {
            0.0
        } else {
            intersection_count as f64 / union_count as f64
        };
        
        scores.push((score, doc));
    }
    
    // Sort descending by score
    scores.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap());
    scores
}

/// A Python module implemented in Rust.
#[pymodule]
fn medical_agent_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fast_jaccard_search, m)?)?;
    return Ok(());
}
