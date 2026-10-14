"""Rebroadcast module for handling event streams with thread-safe processing.

This module provides:
- A DataSource abstract base class for implementing event sources
- A RebroadcastClient class that processes events from a DataSource and sends them to ATProto
- A simple rebroadcast() function for quick setup
- Thread-safe queue for communication between event producers and consumers
- Automatic retries for failed sends with exponential backoff
- Clean startup and shutdown
"""

import queue
import threading
import time
import typing as t
from typing import Any

from nebra.client import send


class DataSource:
    """Class for managing event sources with thread-safe queue operations.
    
    This class provides a thread-safe queue for communication between event producers
    and consumers, along with methods for monitoring the producer's activity.
    
    Attributes
    ----------
    stop_event : threading.Event
        An event to signal when the data source should stop.
        
    Methods
    -------
    add_event(event: dict[str, Any]) -> bool
        Add an event to the queue.
        
    get_event(timeout: float | None = None) -> dict[str, Any]
        Get an event from the queue, with optional timeout.
        
    is_active() -> bool
        Check if the data source is active (not stopped).
        
    mark_producer_running() -> None
        Mark the producer as running by recording the current time.
        This method is thread-safe.
        
    producer_last_signal() -> float
        Get the number of seconds since mark_producer_running() was last called.

    Examples
    --------
    The following example shows how to use a DataSource with a callable:

    ```python
    import time
    import nebra

    def post_producer(data_source: nebra.DataSource):
        counter = 1
        while data_source.is_active():
            # Mark that the producer is running
            data_source.mark_producer_running()
            
            new_post = {
                "$type": "app.bsky.feed.post",
                "text": f"This is test post {counter}.",
                "createdAt": nebra.get_atproto_utc_time()
            }
            data_source.add_event(new_post)
            counter += 1
            time.sleep(1)
            
        # Producer has been stopped
        print(f"Producer last signal was {data_source.producer_last_signal():.2f} seconds ago")
            
    class PostConsumer:
        def __init__(self, data_source: nebra.DataSource):
            self.data_source = data_source
            
        def process_events(self):
            while self.data_source.is_active():
                try:
                    # Get an event with a 1-second timeout
                    event = self.data_source.get_event(timeout=1.0)
                    print(f"Processing event: {event}")
                except queue.Empty:
                    # No event available, continue checking if active
                    continue
    ```
    """

    def __init__(self, max_queue_size: int = 1000):
        """Initialize the DataSource with an event queue.

        Parameters
        ----------
        max_queue_size : int, optional
            Maximum size of the event queue. Defaults to 1000.
        """
        self._event_queue = queue.Queue(maxsize=max_queue_size)
        self.stop_event = threading.Event()
        self._producer_last_active = time.time()
        self._producer_active_lock = threading.Lock()

    def add_event(self, event: dict[str, Any]) -> bool:
        """Add an event to the queue.

        Parameters
        ----------
        event : dict[str, Any]
            The event to add to the queue.
            
        Returns
        -------
        bool
            True if the event was added, False if the queue was full.
        """
        try:
            self._event_queue.put_nowait(event)
            return True
        except queue.Full:
            print("Event queue full, dropping oldest event")
            try:
                # Remove oldest event and try again
                self._event_queue.get_nowait()
                self._event_queue.put_nowait(event)
                return True
            except queue.Empty:
                # Queue was empty after all, just put the event
                self._event_queue.put_nowait(event)
                return True
                
    def get_event(self, timeout: float | None = None) -> dict[str, Any]:
        """Get an event from the queue.
        
        Parameters
        ----------
        timeout : float | None, optional
            Maximum time to wait for an event, in seconds. If None, waits indefinitely.
            
        Returns
        -------
        dict[str, Any]
            The event from the queue.
            
        Raises
        ------
        queue.Empty
            If no event is available within the specified timeout.
        """
        return self._event_queue.get(timeout=timeout)

    def stop(self) -> None:
        """Signal the data source to stop.

        This method sets the stop_event, which should be checked periodically
        in the producer function to allow for clean shutdown.
        """
        self.stop_event.set()
        
    def is_active(self) -> bool:
        """Check if the data source is active (not stopped).
        
        Returns
        -------
        bool
            True if the data source is active (stop_event is not set), False otherwise.
        """
        return not self.stop_event.is_set()
        
    def mark_producer_running(self) -> None:
        """Mark the producer as running by recording the current time.
        
        This method is thread-safe and can be called from any thread.
        The time since this was last called can be accessed with producer_last_signal().
        """
        with self._producer_active_lock:
            self._producer_last_active = time.time()
            
    def producer_last_signal(self) -> float:
        """Get the number of seconds since mark_producer_running() was last called.
        
        Returns
        -------
        float
            The number of seconds since mark_producer_running() was last called.
            If mark_producer_running() has never been called, returns the time since
            the DataSource was initialized.
        """
        with self._producer_active_lock:
            return time.time() - self._producer_last_active


class RebroadcastClient:
    """A client for rebroadcasting events from a producer function to ATProto with thread-safe processing.
    
    This class manages a producer thread and a consumer thread to process events
    from a producer function and send them to ATProto with retry logic.
    
    Attributes
    ----------
    send_function : Callable
        The function used to send events to ATProto.
    data_source : DataSource
        The data source providing the event queue and stop event.
    producer_function : Callable
        The function that produces events and adds them to the data source.
    producer_args : tuple
        Positional arguments to pass to the producer function.
    producer_kwargs : dict
        Keyword arguments to pass to the producer function.
    max_retries : int
        Maximum number of retry attempts for failed sends.
    initial_retry_delay : float
        Initial delay in seconds for retry attempts (exponential backoff).
    send_kwargs : dict
        Additional keyword arguments to pass to the send function.
    stop_event : threading.Event
        An event to signal when the client should stop.
    producer_thread : threading.Thread or None
        The thread running the producer function.
    consumer_thread : threading.Thread or None
        The thread consuming and sending events.
    """

    def __init__(
        self,
        producer_function: t.Callable,
        producer_args: tuple = (),
        producer_kwargs: dict | None = None,
        max_retries: int = 7,
        initial_retry_delay: float = 1.0,
        send_function=send,
        **send_kwargs,
    ):
        """Initialize the RebroadcastClient.
        
        Parameters
        ----------
        producer_function : Callable
            A function that produces events and adds them to the data source.
            This function should take a DataSource as its first argument, followed by
            any additional arguments specified in producer_args and producer_kwargs.
        producer_args : tuple, optional
            Positional arguments to pass to the producer function. Defaults to ().
        producer_kwargs : dict, optional
            Keyword arguments to pass to the producer function. Defaults to None.
        max_retries : int, optional
            Maximum number of retry attempts for failed sends. Defaults to 7.
        initial_retry_delay : float, optional
            Initial delay in seconds for retry attempts (exponential backoff). Defaults to 1.0.
        send_function : Callable, optional
            Function to use for sending events. Defaults to nebra.client.send.
        **send_kwargs : dict
            Additional keyword arguments to pass to the send function.
        """
        self.send_function = send_function
        self.data_source = DataSource()
        self.producer_function = producer_function
        self.producer_args = producer_args
        self.producer_kwargs = producer_kwargs or {}
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.send_kwargs = send_kwargs

        # Event to signal threads to stop
        self.stop_event = threading.Event()

        # Threads
        self.producer_thread: threading.Thread | None = None
        self.consumer_thread: threading.Thread | None = None

    def _send_event_with_retry(self, event: dict[str, Any]):
        """Send an event with retry logic and exponential backoff.
        
        This method attempts to send an event, retrying with exponential backoff
        if the send fails. It will stop retrying if the stop_event is set.
        
        Parameters
        ----------
        event : dict[str, Any]
            The event to send.
            
        Raises
        ------
        Exception
            If the maximum number of retries is exceeded.
        """
        retry_count = 0
        while retry_count <= self.max_retries and not self.stop_event.is_set():
            try:
                self.send_function(event, **self.send_kwargs)
                print("Successfully sent event")
                return

            except Exception as e:
                if retry_count >= self.max_retries:
                    print(
                        f"Max retries exceeded for event. Event:\n{event}\nError: {e}"
                    )
                    raise

                # Calculate delay with exponential backoff
                delay = self.initial_retry_delay * (2**retry_count)
                print(
                    f"Failed to send event. Retry {retry_count + 1}/{self.max_retries} in {delay}s. Error: {e}"
                )

                # Wait for the delay or until stop is requested
                self.stop_event.wait(timeout=delay)
                retry_count += 1

    def _consumer(self) -> None:
        """Consumer thread: processes events from the queue and sends them to ATProto.

        This method runs in a separate thread and continuously processes events
        from the data source's event queue, sending them to ATProto with retry logic.
        """
        while not self.stop_event.is_set():
            try:
                # Get an event from the queue (with timeout to allow checking stop_event)
                event = self.data_source.get_event(timeout=0.1)

                # Send the event with retry logic
                self._send_event_with_retry(event)
                
            except queue.Empty:
                # Queue was empty, just continue the loop
                continue

    def start(self, block: bool = True) -> None:
        """Start the producer and consumer threads.
        
        Parameters
        ----------
        block : bool, optional
            If True, this method will block until a keyboard interrupt is received
            and handle cleanup automatically. If False, the method will return immediately.
            Defaults to True.
        """
        if self.producer_thread is not None or self.consumer_thread is not None:
            print("Client is already running")
            return

        self.stop_event.clear()
        self.data_source.stop_event.clear()

        # Start producer thread with all arguments
        self.producer_thread = threading.Thread(
            target=self.producer_function,
            args=(self.data_source, *self.producer_args),
            kwargs=self.producer_kwargs,
            daemon=True
        )
        self.producer_thread.start()

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
        """Stop the producer and consumer threads.
        
        This method signals the threads to stop, waits for them to finish,
        and cleans up the thread references.
        """
        if self.producer_thread is None and self.consumer_thread is None:
            print("Client is not running")
            return

        print("Stopping rebroadcast client...")
        self.stop_event.set()
        self.data_source.stop()

        # Wait for threads to finish
        if self.producer_thread is not None:
            self.producer_thread.join(timeout=30)
            self.producer_thread = None

        if self.consumer_thread is not None:
            self.consumer_thread.join(timeout=30)
            self.consumer_thread = None

        print("Rebroadcast client stopped")


def rebroadcast(
    producer_function: t.Callable,
    args: tuple = (),
    kwargs: dict | None = None,
    max_retries: int = 7,
    initial_retry_delay: float = 1.0,
    send_function=send,
    **send_kwargs,
):
    """Rebroadcast events from a producer function onto the AT Protocol.
    Includes threading for speed, robust error handling that automatically reboots
    clients that crash, a Queue system to deal with busy networks or rate limited PDSs,
    and more!

    This function is the recommended way to rebroadcast events onto the AT Protocol from
    an existing source in a robust way.

    Parameters
    ----------
    producer_function : Callable
        A function that produces events and adds them to the data source.
        This function should take a DataSource as its first argument, followed by
        any additional arguments specified in args and kwargs.
    args : tuple, optional
        Positional arguments to pass to the producer function. Defaults to ().
    kwargs : dict, optional
        Keyword arguments to pass to the producer function. Defaults to None.
    max_retries : int, optional
        Maximum number of retry attempts for failed sends. Defaults to 7.
    initial_retry_delay : float, optional
        Initial delay in seconds for retry attempts (exponential backoff). Defaults to 1.0.
    send_function : Callable, optional
        Function to use for sending events. Defaults to nebra.client.send.
    **send_kwargs : dict
        Additional keyword arguments to pass to the send function.
    """
    client = RebroadcastClient(
        producer_function=producer_function,
        producer_args=args,
        producer_kwargs=kwargs,
        max_retries=max_retries,
        initial_retry_delay=initial_retry_delay,
        send_function=send_function,
        **send_kwargs,
    )
    client.start()
