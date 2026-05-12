"""
Generic parallel execution utility for running tasks concurrently with batching and rate limiting.

This module provides reusable utilities for parallel execution that can be used across the application
for any tasks that need concurrent processing with API rate limiting, batching, and progress tracking.
"""

import asyncio
from typing import List, Callable, Any, Optional, TypeVar, Dict, Tuple
from dataclasses import dataclass
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Input type
R = TypeVar('R')  # Result type


@dataclass
class ParallelExecutionConfig:
    """Configuration for parallel execution"""
    max_concurrent: int = 10
    """Maximum number of concurrent tasks"""
    
    batch_size: Optional[int] = None
    """Batch size (defaults to max_concurrent if not specified)"""
    
    batch_delay: float = 0.5
    """Delay between batches in seconds"""
    
    retry_attempts: int = 3
    """Number of retry attempts for failed tasks"""
    
    retry_delay: float = 1.0
    """Initial delay for retry (exponential backoff)"""
    
    timeout: Optional[float] = None
    """Timeout for individual tasks in seconds"""
    
    show_progress: bool = True
    """Whether to print progress information"""
    
    progress_callback: Optional[Callable[[int, int], None]] = None
    """Optional callback function for progress updates: callback(completed, total)"""


class ParallelExecutor:
    """
    Generic parallel executor for running tasks concurrently with batching and rate limiting.
    
    Features:
    - Concurrent execution with configurable limits
    - Batching with delays to respect API rate limits
    - Automatic retry logic with exponential backoff
    - Progress tracking and callbacks
    - Support for both sync and async functions
    - Timeout handling
    
    Example:
        ```python
        # Simple usage
        executor = ParallelExecutor()
        results = executor.run(
            items=[1, 2, 3, 4, 5],
            func=lambda x: x * 2,
            config=ParallelExecutionConfig(max_concurrent=2)
        )
        
        # With custom processing
        def process_item(item, context):
            return item + context['offset']
        
        results = executor.run(
            items=[1, 2, 3],
            func=process_item,
            func_args={'context': {'offset': 10}}
        )
        ```
    """
    
    def __init__(self, config: Optional[ParallelExecutionConfig] = None):
        """
        Initialize parallel executor with configuration.
        
        Args:
            config: Configuration for parallel execution. Uses defaults if not provided.
        """
        self.config = config or ParallelExecutionConfig()
    
    async def _execute_with_retry(
        self,
        func: Callable,
        item: T,
        func_args: Optional[Dict[str, Any]],
        semaphore: asyncio.Semaphore,
        timeout: Optional[float]
    ) -> R:
        """
        Execute a function with retry logic and rate limiting.
        
        Args:
            func: Function to execute
            item: Input item to process
            func_args: Additional arguments to pass to the function
            semaphore: Semaphore for rate limiting
            timeout: Timeout in seconds
            
        Returns:
            Result of the function execution
            
        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(self.config.retry_attempts):
            try:
                async with semaphore:
                    # Prepare function arguments
                    if func_args:
                        args = (item,) + tuple(func_args.values()) if isinstance(func_args, dict) else (item,) + func_args
                    else:
                        args = (item,)
                    
                    # Execute with timeout if specified
                    if timeout:
                        result = await asyncio.wait_for(
                            self._call_func_async(func, *args),
                            timeout=timeout
                        )
                    else:
                        result = await self._call_func_async(func, *args)
                    
                    return result
                    
            except asyncio.TimeoutError:
                if attempt < self.config.retry_attempts - 1:
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"Timeout on attempt {attempt + 1}, retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Max retries reached for item after timeout")
                    raise
                    
            except Exception as e:
                # Check if it's a rate limit error
                is_rate_limit = any(keyword in str(e).lower() for keyword in ['rate_limit', '429', 'too many requests'])
                
                if is_rate_limit and attempt < self.config.retry_attempts - 1:
                    # Exponential backoff with jitter
                    wait_time = self.config.retry_delay * (2 ** attempt) + (0.1 * attempt)
                    logger.warning(f"Rate limit hit on attempt {attempt + 1}, waiting {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                elif attempt < self.config.retry_attempts - 1:
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"Error on attempt {attempt + 1}: {e}. Retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Max retries reached for item: {e}")
                    raise
    
    async def _call_func_async(self, func: Callable, *args) -> Any:
        """
        Call a function asynchronously, handling both sync and async functions.
        
        Args:
            func: Function to call (can be sync or async)
            *args: Arguments to pass to the function
            
        Returns:
            Result of the function call
        """
        if asyncio.iscoroutinefunction(func):
            # Already async
            return await func(*args)
        else:
            # Sync function, run in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args)
    
    async def _run_parallel_async(
        self,
        items: List[T],
        func: Callable[[T, ...], R],
        func_args: Optional[Dict[str, Any]] = None
    ) -> List[R]:
        """
        Run parallel execution asynchronously with batching.
        
        Args:
            items: List of items to process
            func: Function to apply to each item
            func_args: Additional arguments to pass to the function
            
        Returns:
            List of results in the same order as input items
        """
        batch_size = self.config.batch_size or self.config.max_concurrent
        semaphore = asyncio.Semaphore(self.config.max_concurrent)
        all_results = []
        total_items = len(items)
        
        # Process items in batches
        for batch_idx in range(0, len(items), batch_size):
            batch = items[batch_idx:batch_idx + batch_size]
            batch_num = batch_idx // batch_size + 1
            total_batches = (len(items) + batch_size - 1) // batch_size
            
            if self.config.show_progress:
                print(f"  Processing batch {batch_num}/{total_batches} ({len(batch)} items)...")
            
            # Create tasks for this batch
            tasks = [
                self._execute_with_retry(
                    func,
                    item,
                    func_args,
                    semaphore,
                    self.config.timeout
                )
                for item in batch
            ]
            
            # Run batch in parallel
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check for exceptions
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to process item {batch_idx + i}: {result}")
                    # You can choose to either raise or continue
                    # For now, we'll keep the exception in results
            
            all_results.extend(batch_results)
            
            # Progress callback
            if self.config.progress_callback:
                self.config.progress_callback(len(all_results), total_items)
            
            # Add delay between batches (except for the last batch)
            if batch_idx + batch_size < len(items) and self.config.batch_delay > 0:
                await asyncio.sleep(self.config.batch_delay)
        
        if self.config.show_progress:
            print(f"  ✅ Completed processing {len(all_results)}/{total_items} items")
        
        return all_results
    
    def run(
        self,
        items: List[T],
        func: Callable[[T, ...], R],
        func_args: Optional[Dict[str, Any]] = None,
        config: Optional[ParallelExecutionConfig] = None
    ) -> List[R]:
        """
        Run parallel execution on a list of items.
        
        Args:
            items: List of items to process
            func: Function to apply to each item (can be sync or async)
            func_args: Additional arguments to pass to the function
            config: Optional config to override default configuration
            
        Returns:
            List of results in the same order as input items
            
        Example:
            ```python
            executor = ParallelExecutor()
            
            # Process numbers
            results = executor.run(
                items=[1, 2, 3, 4, 5],
                func=lambda x: x * 2
            )
            
            # Process with additional arguments
            def process(item, multiplier):
                return item * multiplier
            
            results = executor.run(
                items=[1, 2, 3],
                func=process,
                func_args={'multiplier': 10}
            )
            ```
        """
        # Use provided config or fall back to instance config
        if config:
            original_config = self.config
            self.config = config
        
        try:
            results = asyncio.run(self._run_parallel_async(items, func, func_args))
            return results
        finally:
            if config:
                self.config = original_config


def parallel_batch_process(
    items: List[T],
    func: Callable[[T, ...], R],
    max_concurrent: int = 10,
    batch_delay: float = 0.5,
    **kwargs
) -> List[R]:
    """
    Convenience function for parallel batch processing.
    
    Args:
        items: List of items to process
        func: Function to apply to each item
        max_concurrent: Maximum concurrent tasks
        batch_delay: Delay between batches
        **kwargs: Additional arguments passed to func
        
    Returns:
        List of results
        
    Example:
        ```python
        results = parallel_batch_process(
            items=[1, 2, 3, 4, 5],
            func=lambda x: x * 2,
            max_concurrent=3
        )
        ```
    """
    config = ParallelExecutionConfig(
        max_concurrent=max_concurrent,
        batch_delay=batch_delay
    )
    executor = ParallelExecutor(config)
    return executor.run(items, func, func_args=kwargs if kwargs else None)


def create_parallel_executor(
    max_concurrent: int = 10,
    batch_size: Optional[int] = None,
    batch_delay: float = 0.5,
    retry_attempts: int = 3,
    show_progress: bool = True
) -> ParallelExecutor:
    """
    Factory function to create a configured parallel executor.
    
    Args:
        max_concurrent: Maximum concurrent tasks
        batch_size: Batch size (defaults to max_concurrent)
        batch_delay: Delay between batches in seconds
        retry_attempts: Number of retry attempts
        show_progress: Whether to show progress
        
    Returns:
        Configured ParallelExecutor instance
        
    Example:
        ```python
        executor = create_parallel_executor(
            max_concurrent=5,
            batch_delay=1.0,
            show_progress=True
        )
        
        results = executor.run(items, process_func)
        ```
    """
    config = ParallelExecutionConfig(
        max_concurrent=max_concurrent,
        batch_size=batch_size,
        batch_delay=batch_delay,
        retry_attempts=retry_attempts,
        show_progress=show_progress
    )
    return ParallelExecutor(config)

