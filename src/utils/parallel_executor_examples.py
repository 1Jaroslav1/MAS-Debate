"""
Examples demonstrating usage of the ParallelExecutor utility.

This file shows various use cases for parallel execution across different scenarios.
"""

from src.utils import (
    ParallelExecutor,
    ParallelExecutionConfig,
    parallel_batch_process,
    create_parallel_executor
)
from typing import List, Dict, Any
import time


# Example 1: Simple parallel processing
def example_simple_processing():
    """Example: Process a list of numbers in parallel"""
    print("\n" + "="*60)
    print("Example 1: Simple Parallel Processing")
    print("="*60)
    
    def square(x):
        time.sleep(0.1)  # Simulate work
        return x ** 2
    
    numbers = list(range(1, 21))
    
    # Using the executor
    executor = ParallelExecutor()
    results = executor.run(
        items=numbers,
        func=square,
        config=ParallelExecutionConfig(max_concurrent=5)
    )
    
    print(f"Results: {results}")


# Example 2: Parallel API calls with retry
def example_api_calls():
    """Example: Make parallel API calls with automatic retry"""
    print("\n" + "="*60)
    print("Example 2: Parallel API Calls with Retry")
    print("="*60)
    
    def fetch_data(user_id):
        """Simulate API call that might fail"""
        import random
        if random.random() < 0.1:  # 10% chance of failure
            raise Exception("API rate limit")
        time.sleep(0.2)
        return {"user_id": user_id, "data": f"data_for_{user_id}"}
    
    user_ids = list(range(1, 11))
    
    config = ParallelExecutionConfig(
        max_concurrent=3,
        retry_attempts=3,
        batch_delay=0.5,
        show_progress=True
    )
    
    executor = ParallelExecutor(config)
    results = executor.run(items=user_ids, func=fetch_data)
    
    print(f"Fetched {len(results)} results")


# Example 3: Processing with context/additional arguments
def example_with_context():
    """Example: Process items with additional context"""
    print("\n" + "="*60)
    print("Example 3: Processing with Context")
    print("="*60)
    
    def process_with_context(item, multiplier, offset):
        """Process item with additional arguments"""
        time.sleep(0.05)
        return (item * multiplier) + offset
    
    items = [1, 2, 3, 4, 5]
    
    # Pass additional arguments
    results = parallel_batch_process(
        items=items,
        func=process_with_context,
        max_concurrent=3,
        multiplier=10,  # Additional kwargs
        offset=100
    )
    
    print(f"Results: {results}")


# Example 4: LLM-based processing (simulate)
def example_llm_processing():
    """Example: Process items using LLM calls"""
    print("\n" + "="*60)
    print("Example 4: LLM-based Processing")
    print("="*60)
    
    def analyze_text(text):
        """Simulate LLM analysis"""
        time.sleep(0.3)  # Simulate LLM call
        return {
            "text": text,
            "sentiment": "positive" if len(text) > 20 else "neutral",
            "length": len(text)
        }
    
    texts = [
        "This is a short text",
        "This is a longer text that will take more time to analyze",
        "Another text for processing",
        "Yet another piece of text",
        "Final text in our batch"
    ]
    
    config = ParallelExecutionConfig(
        max_concurrent=2,
        batch_delay=1.0,  # Longer delay for API rate limits
        show_progress=True
    )
    
    executor = ParallelExecutor(config)
    results = executor.run(items=texts, func=analyze_text)
    
    for result in results:
        print(f"  - {result['text'][:30]}...: {result['sentiment']}")


# Example 5: Custom progress tracking
def example_custom_progress():
    """Example: Use custom progress callback"""
    print("\n" + "="*60)
    print("Example 5: Custom Progress Tracking")
    print("="*60)
    
    def process_item(item):
        time.sleep(0.1)
        return item * 2
    
    def progress_callback(completed, total):
        """Custom progress callback"""
        percentage = (completed / total) * 100
        print(f"  Progress: {completed}/{total} ({percentage:.1f}%)")
    
    items = list(range(1, 21))
    
    config = ParallelExecutionConfig(
        max_concurrent=5,
        show_progress=False,  # Disable default progress
        progress_callback=progress_callback
    )
    
    executor = ParallelExecutor(config)
    results = executor.run(items=items, func=process_item)
    
    print(f"Processed {len(results)} items")


# Example 6: Error handling
def example_error_handling():
    """Example: Handle errors gracefully"""
    print("\n" + "="*60)
    print("Example 6: Error Handling")
    print("="*60)
    
    def risky_operation(item):
        """Operation that might fail"""
        if item % 3 == 0:
            raise ValueError(f"Cannot process {item}")
        time.sleep(0.05)
        return item * 2
    
    items = list(range(1, 11))
    
    config = ParallelExecutionConfig(
        max_concurrent=3,
        retry_attempts=2,
        show_progress=True
    )
    
    executor = ParallelExecutor(config)
    results = executor.run(items=items, func=risky_operation)
    
    # Filter out exceptions
    successful = [r for r in results if not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]
    
    print(f"Successful: {len(successful)}, Failed: {len(failed)}")
    if failed:
        print(f"Errors: {[str(e) for e in failed]}")


# Example 7: Using factory function
def example_factory_function():
    """Example: Create executor using factory"""
    print("\n" + "="*60)
    print("Example 7: Using Factory Function")
    print("="*60)
    
    def process(item):
        time.sleep(0.05)
        return item ** 3
    
    # Create pre-configured executor
    executor = create_parallel_executor(
        max_concurrent=4,
        batch_delay=0.3,
        show_progress=True
    )
    
    items = list(range(1, 16))
    results = executor.run(items=items, func=process)
    
    print(f"Results: {results}")


# Example 8: Real-world use case - Document processing
def example_document_processing():
    """Example: Process documents in parallel"""
    print("\n" + "="*60)
    print("Example 8: Document Processing")
    print("="*60)
    
    class Document:
        def __init__(self, id: int, content: str):
            self.id = id
            self.content = content
    
    def process_document(doc: Document) -> Dict[str, Any]:
        """Process a document"""
        time.sleep(0.1)  # Simulate processing
        return {
            "doc_id": doc.id,
            "word_count": len(doc.content.split()),
            "char_count": len(doc.content),
            "processed": True
        }
    
    # Create sample documents
    documents = [
        Document(1, "This is document one with some content"),
        Document(2, "Second document has different content"),
        Document(3, "Third document contains more text"),
        Document(4, "Fourth document is here"),
        Document(5, "Fifth and final document")
    ]
    
    executor = create_parallel_executor(max_concurrent=3)
    results = executor.run(items=documents, func=process_document)
    
    for result in results:
        if not isinstance(result, Exception):
            print(f"  Doc {result['doc_id']}: {result['word_count']} words, {result['char_count']} chars")


def run_all_examples():
    """Run all examples"""
    print("\n" + "="*80)
    print("PARALLEL EXECUTOR UTILITY - USAGE EXAMPLES")
    print("="*80)
    
    example_simple_processing()
    example_with_context()
    example_custom_progress()
    example_error_handling()
    example_factory_function()
    example_document_processing()
    
    # Skip these as they involve random failures/longer waits
    # example_api_calls()
    # example_llm_processing()
    
    print("\n" + "="*80)
    print("All examples completed!")
    print("="*80)


if __name__ == "__main__":
    run_all_examples()

