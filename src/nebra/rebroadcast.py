"""Rebroadcast module for handling event streams with thread-safe processing.

This module provides a RebroadcastClient class that:
- Runs a generator in a producer thread to fetch events
- Processes events in a consumer thread to send them to ATProto
- Uses thread-safe queues for communication between threads
- Handles errors and retries appropriately
- Provides clean startup and shutdown
"""

import queue
import threading
import time
from typing import Callable, Generator, Dict, Any, Optional

from nebra.client import send as atproto_send


class RebroadcastClient:
    """A client for rebroadcasting events from a generator to ATProto with thread-safe processing."""
    
    def __init__(
        self,
        generator_factory: Callable[[], Generator[Dict[str, Any], None, None]],
        max_retries: int = 5,
        initial_retry_delay: float = 1.0,
        max_queue_size: int = 1000,
        **send_kwargs,
    ):
        """Initialize the RebroadcastClient.
        
        Args:
            generator_factory: A callable that returns a new generator when called.
            max_retries: Maximum number of retry attempts for failed sends.
            initial_retry_delay: Initial delay in seconds for retry attempts (exponential backoff).
            max_queue_size: Maximum size of the event queue.
            **send_kwargs: Additional keyword arguments to pass to the send function.
        """
        self.generator_factory = generator_factory
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.send_kwargs = send_kwargs
        
        # Thread-safe queue for events
        self.event_queue = queue.Queue(maxsize=max_queue_size)
        
        # Event to signal threads to stop
        self.stop_event = threading.Event()
        
        # Threads
        self.producer_thread: Optional[threading.Thread] = None
        self.consumer_thread: Optional[threading.Thread] = None
    
    def _producer(self) -> None:
        """Producer thread: runs the generator and adds events to the queue."""
        current_generator = self.generator_factory()
        
        while not self.stop_event.is_set():
            try:
                # Get next event from generator
                event = next(current_generator)
                
                # Try to put the event in the queue (non-blocking)
                try:
                    self.event_queue.put_nowait(event)
                except queue.Full:
                    print("Event queue full, dropping oldest event")
                    # Remove oldest event and try again
                    try:
                        self.event_queue.get_nowait()
                        self.event_queue.put_nowait(event)
                    except queue.Empty:
                        # Queue was empty after all, just put the event
                        self.event_queue.put_nowait(event)
                        
            except StopIteration:
                # Generator completed normally
                print("Generator completed normally")
                break
            except Exception as e:  # noqa
                print(f"Generator failed with error: {e}. Reinitializing...")
                current_generator = self.generator_factory()  # Get a fresh generator
                time.sleep(1)  # Wait before retrying
                continue
    
    def _consumer(self) -> None:
        """Consumer thread: processes events from the queue and sends them to ATProto."""
        while not self.stop_event.is_set():
            try:
                # Get an event from the queue (with timeout to allow checking stop_event)
                event = self.event_queue.get(timeout=0.1)
                
                retry_count = 0
                while retry_count <= self.max_retries and not self.stop_event.is_set():
                    try:
                        atproto_send(event, **self.send_kwargs)
                        print(f"Successfully sent event: {event.get('eventID', 'unknown')}")
                        break
                    except Exception as e:
                        if retry_count >= self.max_retries:
                            print(f"Max retries exceeded for event {event.get('eventID', 'unknown')}. Error: {e}")
                            break
                        
                        # Calculate delay with exponential backoff
                        delay = self.initial_retry_delay * (2 ** retry_count)
                        print(f"Failed to send event {event.get('eventID', 'unknown')}. Retry {retry_count + 1}/{self.max_retries} in {delay}s. Error: {e}")
                        
                        # Wait for the delay or until stop is requested
                        self.stop_event.wait(timeout=delay)
                        retry_count += 1
                        
                self.event_queue.task_done()
                
            except queue.Empty:
                # Queue was empty, just continue the loop
                continue
            except Exception as e:
                print(f"Unexpected error in consumer: {e}")
                time.sleep(1)
    
    def start(self) -> None:
        """Start the producer and consumer threads."""
        if self.producer_thread is not None or self.consumer_thread is not None:
            print("Client is already running")
            return
            
        self.stop_event.clear()
        
        # Start producer thread
        self.producer_thread = threading.Thread(target=self._producer, daemon=True)
        self.producer_thread.start()
        
        # Start consumer thread
        self.consumer_thread = threading.Thread(target=self._consumer, daemon=True)
        self.consumer_thread.start()
        
        print("Rebroadcast client started")
    
    def stop(self) -> None:
        """Stop the producer and consumer threads."""
        if self.producer_thread is None and self.consumer_thread is None:
            print("Client is not running")
            return
            
        print("Stopping rebroadcast client...")
        self.stop_event.set()
        
        # Wait for threads to finish
        if self.producer_thread is not None:
            self.producer_thread.join(timeout=5)
            self.producer_thread = None
            
        if self.consumer_thread is not None:
            self.consumer_thread.join(timeout=5)
            self.consumer_thread = None
            
        print("Rebroadcast client stopped")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def rebroadcast(
    generator_factory: Callable[[], Generator[Dict[str, Any], None, None]],
    max_retries: int = 5,
    initial_retry_delay: float = 1.0,
    max_queue_size: int = 1000,
    **send_kwargs,
) -> None:
    """Convenience function for simple rebroadcast usage.
    
    Args:
        generator_factory: A callable that returns a new generator when called.
        max_retries: Maximum number of retry attempts for failed sends.
        initial_retry_delay: Initial delay in seconds for retry attempts (exponential backoff).
        max_queue_size: Maximum size of the event queue.
        **send_kwargs: Additional keyword arguments to pass to the send function.
    """
    with RebroadcastClient(
        generator_factory=generator_factory,
        max_retries=max_retries,
        initial_retry_delay=initial_retry_delay,
        max_queue_size=max_queue_size,
        **send_kwargs,
    ) as client:
        # Keep running until KeyboardInterrupt
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Received keyboard interrupt, shutting down...")