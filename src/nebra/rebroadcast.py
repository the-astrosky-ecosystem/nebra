"""Rebroadcast module for handling event streams with thread-safe processing.

This module provides:
- A DataSource abstract base class for implementing event sources
- A RebroadcastClient class that processes events from a DataSource and sends them to ATProto
- Thread-safe queue for communication between event producers and consumers
- Automatic retries for failed sends with exponential backoff
- Clean startup and shutdown
"""

import queue
import threading
import time
from abc import ABC, abstractmethod
from typing import Any

from nebra.client import send


class DataSource(ABC):
    """Abstract base class for event sources.

    Users should subclass this and implement the run() method to provide events.
    The run() method should handle its own error recovery.
    """

    def __init__(self, max_queue_size: int = 1000):
        """Initialize the DataSource with an event queue.

        Args:
            max_queue_size: Maximum size of the event queue.
        """
        self.event_queue = queue.Queue(maxsize=max_queue_size)
        self.stop_event = threading.Event()

    def add_event(self, event: dict[str, Any]) -> bool:
        """Add an event to the queue.

        Args:
            event: The event to add to the queue.

        Returns:
            bool: True if the event was added, False if the queue was full.
        """
        try:
            self.event_queue.put_nowait(event)
            return True
        except queue.Full:
            print("Event queue full, dropping oldest event")
            try:
                # Remove oldest event and try again
                self.event_queue.get_nowait()
                self.event_queue.put_nowait(event)
                return True
            except queue.Empty:
                # Queue was empty after all, just put the event
                self.event_queue.put_nowait(event)
                return True
        except Exception:
            return False

    def stop(self) -> None:
        """Signal the data source to stop."""
        self.stop_event.set()

    @abstractmethod
    def run(self) -> None:
        """Run the event source.

        This method should:
        1. Generate events and add them to the queue using add_event()
        2. Handle its own error recovery
        3. Check self.stop_event.is_set() periodically to allow clean shutdown
        """


class RebroadcastClient:
    """A client for rebroadcasting events from a DataSource to ATProto with thread-safe processing."""

    def __init__(
        self,
        data_source: DataSource,
        max_retries: int = 7,
        initial_retry_delay: float = 1.0,
        **send_kwargs,
    ):
        """Initialize the RebroadcastClient.

        Args:
            data_source: A DataSource instance that provides events.
            max_retries: Maximum number of retry attempts for failed sends.
            initial_retry_delay: Initial delay in seconds for retry attempts (exponential backoff).
            **send_kwargs: Additional keyword arguments to pass to the send function.
        """
        self.data_source = data_source
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.send_kwargs = send_kwargs

        # Event to signal threads to stop
        self.stop_event = threading.Event()

        # Threads
        self.data_source_thread: threading.Thread | None = None
        self.consumer_thread: threading.Thread | None = None

    def _send_event_with_retry(self, event: dict[str, Any]):
        """Send an event with retry logic and exponential backoff.

        Args:
            event: The event to send.
        """
        retry_count = 0
        while retry_count <= self.max_retries and not self.stop_event.is_set():
            try:
                send(event, **self.send_kwargs)
                print(f"Successfully sent event: {event.get('eventID', 'unknown')}")
                return

            except Exception as e:
                if retry_count >= self.max_retries:
                    print(
                        f"Max retries exceeded for event {event.get('eventID', 'unknown')}. Error: {e}"
                    )
                    raise e

                # Calculate delay with exponential backoff
                delay = self.initial_retry_delay * (2**retry_count)
                print(
                    f"Failed to send event {event.get('eventID', 'unknown')}. Retry {retry_count + 1}/{self.max_retries} in {delay}s. Error: {e}"
                )

                # Wait for the delay or until stop is requested
                self.stop_event.wait(timeout=delay)
                retry_count += 1

    def _consumer(self) -> None:
        """Consumer thread: processes events from the queue and sends them to ATProto."""
        while not self.stop_event.is_set():
            try:
                # Get an event from the queue (with timeout to allow checking stop_event)
                event = self.data_source.event_queue.get(timeout=0.1)

                # Send the event with retry logic
                self._send_event_with_retry(event)
                self.data_source.event_queue.task_done()

            except queue.Empty:
                # Queue was empty, just continue the loop
                continue

    def start(self, block: bool = True) -> None:
        """Start the data source and consumer threads.

        Args:
            block: If True, this method will block until a keyboard interrupt is received
                  and handle cleanup automatically. If False, the method will return immediately.
        """
        if self.data_source_thread is not None or self.consumer_thread is not None:
            print("Client is already running")
            return

        self.stop_event.clear()

        # Start data source thread
        self.data_source_thread = threading.Thread(
            target=self.data_source.run, daemon=True
        )
        self.data_source_thread.start()

        # Start consumer thread
        self.consumer_thread = threading.Thread(target=self._consumer, daemon=True)
        self.consumer_thread.start()

        print("Rebroadcast client started")

        # If blocking, wait for keyboard interrupt
        if block:
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nReceived keyboard interrupt, shutting down...")
                self.stop()

    def stop(self) -> None:
        """Stop the data source and consumer threads."""
        if self.data_source_thread is None and self.consumer_thread is None:
            print("Client is not running")
            return

        print("Stopping rebroadcast client...")
        self.stop_event.set()
        self.data_source.stop()

        # Wait for threads to finish
        if self.data_source_thread is not None:
            self.data_source_thread.join(timeout=30)
            self.data_source_thread = None

        if self.consumer_thread is not None:
            self.consumer_thread.join(timeout=30)
            self.consumer_thread = None

        print("Rebroadcast client stopped")
